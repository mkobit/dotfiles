import functools
import hashlib
import json
import os
import shutil
import subprocess
import threading
import tomllib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "src/chezmoi"
EXTERNAL = Path("dot_local/share/gh-managed/.chezmoiexternals/extensions.toml.tmpl")
SCRIPT = Path(".chezmoiscripts/run_after_09_register-gh-extensions.sh.tmpl")
DISPATCHER = Path("dot_local/bin/.chezmoiexternals/bins.toml.tmpl")
NAMES = ("gh-stack", "gh-actions-lock")
VERSIONS = {"gh-stack": "0.2.1", "gh-actions-lock": "0.4.0"}
CHECKSUMS = {
    "gh-stack": {
        "darwin_amd64": "3309195dc0566c5ecfe7b6e777aec30306df87069dedb4a5eb39ba5641b7e2fa",
        "darwin_arm64": "c4d62dc667343d6dd8ff1cb60dcff9d0e097c2460dea326892f36d5d2e835d76",
        "linux_amd64": "ffe9d48b6342faffc3b0cb420202ff1df32e24faf32693debd7423274bbdf859",
        "linux_arm64": "25ec261a391261a1462d38f85c230b0e0b14ae3547926130996541f62f25f78b",
    },
    "gh-actions-lock": {
        "darwin_amd64": "6b81e2050e0fcd1953649886231b2d19f8861428272d86067a59c22bd4b75c76",
        "darwin_arm64": "5934d40f8cc78ed3e9be15ba43fc82c2432cbf3aa088107f923878df07099bec",
        "linux_amd64": "f9da98f2a6e9e0ae77deadf9a2319a8a86bb002b541cc3203b247cc59fb04842",
        "linux_arm64": "7de0e440274688b8ddcbb6f44ce686aaebbe17a54a3052ebc11d4bae9f641fa2",
    },
}


@pytest.fixture(scope="module")
def real_gh():
    executable = shutil.which("gh")
    assert executable, "Unmet prerequisite: real GitHub CLI must be installed"
    return Path(executable).resolve()


class ExtensionCase:
    def __init__(self, root, executable, record_property):
        self.root = root
        self.source = root / "source"
        self.destination = root / "destination"
        self.config = root / "chezmoi.json"
        self.cache = root / "chezmoi-cache"
        self.state = root / "chezmoi-state.boltdb"
        self.env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("GH_", "GITHUB_", "CHEZMOI_", "XDG_"))
        }
        self.env.update(
            HOME=str(root / "home"),
            XDG_DATA_HOME=str(self.destination / ".local/share"),
            XDG_STATE_HOME=str(self.destination / ".local/state"),
            XDG_CACHE_HOME=str(root / "gh-cache"),
            XDG_CONFIG_HOME=str(root / "config"),
            GH_CONFIG_DIR=str(root / "gh-config"),
            GH_PROMPT_DISABLED="1",
            GH_NO_UPDATE_NOTIFIER="1",
            GH_NO_EXTENSION_UPDATE_NOTIFIER="1",
            CI="true",
        )
        for key in ("HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "GH_CONFIG_DIR"):
            assert Path(self.env[key]).resolve().is_relative_to(root.resolve())
            Path(self.env[key]).mkdir(parents=True, exist_ok=True)
        self.gh_binary = self.destination / ".local/bin/gh"
        self.gh_binary.parent.mkdir(parents=True)
        shutil.copy2(executable, self.gh_binary)
        version = self.gh("--version")
        assert version.returncode == 0, version.stderr
        assert tuple(map(int, version.stdout.split()[2].split(".")[:2])) >= (2, 97), version.stdout
        record_property("gh_version", version.stdout.splitlines()[0])
        for relative in (EXTERNAL, SCRIPT, DISPATCHER, Path(".chezmoitemplates/bin/github-releases-entry.tmpl")):
            if (SOURCE / relative).is_file():
                target = self.source / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(SOURCE / relative, target)
        self.catalog = {}
        for name in NAMES:
            path = SOURCE / f".chezmoidata/bin/{name}.toml"
            if path.is_file():
                self.catalog.update(tomllib.loads(path.read_text())["bin"])
        self.choices = {name: {"installation_method": "github_releases"} for name in NAMES}
        self.write_config()

    def run(self, command, **kwargs):
        for key in ("HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "GH_CONFIG_DIR"):
            assert Path(self.env[key]).resolve().is_relative_to(self.root.resolve())
        return subprocess.run(command, env=self.env, capture_output=True, text=True, check=False, timeout=30, **kwargs)

    def cm(self, *args):
        return self.run(
            [
                "chezmoi",
                "--config",
                str(self.config),
                "--source",
                str(self.source),
                "--destination",
                str(self.destination),
                "--cache",
                str(self.cache),
                "--persistent-state",
                str(self.state),
                *args,
            ]
        )

    def gh(self, *args, **kwargs):
        return self.run([str(self.gh_binary), *args], **kwargs)

    def write_config(self):
        data = {"bin": self.catalog, "local": {"bin": {}}}
        if self.choices is not None:
            data["gh"] = {"extensions": self.choices}
        self.config.write_text(json.dumps({"data": data}))

    def render(self, relative, override=None):
        result = self.cm(
            "execute-template",
            "--override-data",
            json.dumps(override or {}),
            "--file",
            str(self.source / relative),
        )
        assert result.returncode == 0, result.stderr
        return result.stdout

    def directory(self, name):
        return self.destination / ".local/share/gh-managed" / name

    def registration(self, name):
        return self.destination / ".local/share/gh/extensions" / name

    def register(self, name, directory=None):
        directory = directory or self.directory(name)
        result = self.gh("extension", "install", ".", cwd=directory)
        assert result.returncode == 0, result.stderr


@pytest.fixture
def case(tmp_path, real_gh, record_property):
    return ExtensionCase(tmp_path, real_gh, record_property)


@pytest.fixture
def local_releases(case):
    downloads = case.root / "downloads"
    downloads.mkdir()
    requests = []

    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            super().do_GET()

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(downloads)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def release(name, version):
        payload = f"#!/bin/sh\nprintf '%s\\n' '{name} {version}'\n".encode()
        path = downloads / name / version
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(payload)
        if name in case.catalog:
            tool = case.catalog[name]
            tool["version"] = version
            tool["github_releases"]["url_format"] = f"http://127.0.0.1:{server.server_port}/{name}/{{tag}}"
            tool["github_releases"]["tag_format"] = "{version}"
            tool["github_releases"]["checksums"] = {key: hashlib.sha256(payload).hexdigest() for key in CHECKSUMS[name]}
        case.write_config()
        return payload

    for name in NAMES:
        release(name, VERSIONS[name])
    try:
        yield release, requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def _stat(path):
    stat = path.lstat()
    return stat.st_ino, stat.st_mode, stat.st_mtime_ns, stat.st_ctime_ns


def _apply(case):
    result = case.cm("apply", "--force")
    assert result.returncode == 0, result.stderr


def _previous_registration(case, name, kind):
    old = case.root / "previous" / name
    old.mkdir(parents=True)
    (old / name).write_text("#!/bin/sh\necho previous\n")
    (old / name).chmod(0o755)
    if kind == "link":
        case.register(name, old)
    else:
        registration = case.registration(name)
        shutil.copytree(old, registration)
        (registration / "nested").mkdir()
        (registration / "nested/old-target").symlink_to(old, target_is_directory=True)
    return old


@pytest.mark.parametrize("platform", ["linux_amd64", "linux_arm64", "darwin_amd64", "darwin_arm64"])
def test_platform_catalogs_render_verified_binaries_without_generic_duplicates(case, platform):
    os_name, arch = platform.split("_")
    override = {"chezmoi": {"os": os_name, "arch": arch}}
    data = case.cm("data", "--format=json")
    assert data.returncode == 0, data.stderr
    assert set(json.loads(data.stdout)["bin"]) == set(NAMES)
    rendered = tomllib.loads(case.render(EXTERNAL, override))
    assert set(rendered) == {f"{name}/{name}" for name in NAMES}
    for name in NAMES:
        assert rendered[f"{name}/{name}"] == {
            "type": "file",
            "executable": True,
            "url": f"https://github.com/github/{name}/releases/download/v{VERSIONS[name]}/{os_name}-{arch}",
            "checksum": {"sha256": CHECKSUMS[name][platform]},
        }
        assert case.catalog[name]["minimum_release_age"] == "21d"
    assert tomllib.loads(case.render(DISPATCHER, override)) == {}


def test_init_choices_are_separate_from_generic_binaries(case):
    shutil.copy2(SOURCE / ".chezmoi.toml.tmpl", case.source / ".chezmoi.toml.tmpl")
    generated = case.root / "init.toml"
    result = case.cm("init", "--config-path", str(generated), "--promptDefaults")
    assert result.returncode == 0, result.stderr
    data = tomllib.loads(generated.read_text())["data"]
    for name in NAMES:
        assert data["gh"]["extensions"][name]["installation_method"] == "github_releases"
        assert name not in data["local"]["bin"]


@pytest.mark.parametrize("name", NAMES)
def test_apply_registers_local_binary_and_reconciles_both_version_directions(case, local_releases, name):
    release, requests = local_releases
    diff = case.cm("diff")
    assert diff.returncode == 0, diff.stderr
    _apply(case)
    binary = case.directory(name) / name
    link = case.registration(name)
    assert binary.is_file(), "Enabled extension binary was not deployed"
    assert link.is_symlink(), "Enabled extension was not registered with gh"
    assert link.readlink() == case.directory(name)
    for version in (VERSIONS[name], "9.0.0", "0.0.1"):
        payload = release(name, version)
        _apply(case)
        assert binary.read_bytes() == payload
        result = case.gh(name.removeprefix("gh-"), "--version")
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == f"{name} {version}"
        before = _stat(binary), _stat(link), len(requests)
        _apply(case)
        assert (_stat(binary), _stat(link), len(requests)) == before
    diff = case.cm("diff", "--exclude=scripts")
    assert diff.returncode == 0, diff.stderr
    assert diff.stdout == ""


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("kind", ["link", "directory"])
def test_apply_replaces_other_registration_and_repairs_removed_link(case, local_releases, name, kind):
    old = _previous_registration(case, name, kind)
    old_stat = _stat(old / name)
    state = case.destination / ".local/state/gh/extensions" / name
    state.mkdir(parents=True)
    (state / "state.yml").write_text("old update state\n")
    _apply(case)
    assert case.registration(name).readlink() == case.directory(name)
    assert (old / name).read_text() == "#!/bin/sh\necho previous\n"
    assert _stat(old / name) == old_stat
    assert not state.exists(), "Local registration must clear stale update state"
    case.registration(name).unlink()
    _apply(case)
    assert case.registration(name).readlink() == case.directory(name)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("choice", [None, "none"])
@pytest.mark.parametrize("existing", [None, "link", "directory"])
def test_disabled_extension_is_untouched_while_other_is_managed(case, local_releases, name, choice, existing):
    _, requests = local_releases
    if existing:
        directory = _previous_registration(case, name, existing)
        state = case.destination / ".local/state/gh/extensions" / name
        state.mkdir(parents=True)
        (state / "state.yml").write_text("unmanaged update state\n")
        before = _stat(directory / name), _stat(case.registration(name)), _stat(state / "state.yml")
    case.choices[name] = {} if choice is None else {"installation_method": choice}
    case.write_config()
    _apply(case)
    other = next(item for item in NAMES if item != name)
    assert case.registration(other).is_symlink()
    assert all(not request.startswith(f"/{name}/") for request in requests)
    if existing:
        assert (directory / name).read_text() == "#!/bin/sh\necho previous\n"
        assert (_stat(directory / name), _stat(case.registration(name)), _stat(state / "state.yml")) == before
        if existing == "directory":
            assert (case.registration(name) / name).read_text() == "#!/bin/sh\necho previous\n"
    else:
        assert not case.registration(name).exists()
        assert not (case.directory(name) / name).exists()


@pytest.mark.parametrize(
    "choices", [None, {}, {name: {} for name in NAMES}, {name: {"installation_method": "none"} for name in NAMES}]
)
def test_all_disabled_bypasses_gh_and_conflicting_data_home(case, local_releases, choices):
    _, requests = local_releases
    case.choices = choices
    case.write_config()
    case.gh_binary.unlink()
    case.env["XDG_DATA_HOME"] = str(case.root / "inherited-data")
    _apply(case)
    assert requests == []
    assert not (case.destination / ".local/share/gh").exists()
    assert case.render(SCRIPT).strip() == ""


@pytest.mark.parametrize("choice", [None, "none"])
def test_disabling_management_preserves_managed_installations_without_gh(case, local_releases, choice):
    _, requests = local_releases
    _apply(case)
    before = {name: (_stat(case.directory(name) / name), _stat(case.registration(name))) for name in NAMES}
    downloads = len(requests)
    case.choices = {name: {} if choice is None else {"installation_method": choice} for name in NAMES}
    case.write_config()
    case.gh_binary.unlink()
    case.env["XDG_DATA_HOME"] = str(case.root / "inherited-data")
    _apply(case)
    assert len(requests) == downloads
    for name in NAMES:
        assert (_stat(case.directory(name) / name), _stat(case.registration(name))) == before[name]


def test_matching_registration_does_not_invoke_gh(case, local_releases):
    _apply(case)
    before = {name: _stat(case.registration(name)) for name in NAMES}
    case.gh_binary.unlink()
    _apply(case)
    assert {name: _stat(case.registration(name)) for name in NAMES} == before


@pytest.mark.parametrize("name", NAMES)
def test_wrong_checksum_never_replaces_registration(case, local_releases, name):
    directory = case.root / "previous" / name
    directory.mkdir(parents=True)
    (directory / name).write_text("#!/bin/sh\necho previous\n")
    (directory / name).chmod(0o755)
    case.register(name, directory)
    before = _stat(case.registration(name))
    case.catalog[name]["github_releases"]["checksums"] = dict.fromkeys(CHECKSUMS[name], "0" * 64)
    case.write_config()
    result = case.cm("apply", "--force")
    assert result.returncode != 0
    assert "sha256 mismatch" in result.stderr.lower()
    assert _stat(case.registration(name)) == before
    assert case.registration(name).readlink() == directory
    assert (directory / name).read_text() == "#!/bin/sh\necho previous\n"
    assert not (case.directory(name) / name).exists()


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("kind", ["link", "directory"])
@pytest.mark.parametrize("replacement", ["missing", "nonexecutable", "directory"])
def test_invalid_replacement_preserves_registration(case, local_releases, name, kind, replacement):
    _apply(case)
    case.registration(name).unlink()
    old = _previous_registration(case, name, kind)
    binary = case.directory(name) / name
    if replacement == "nonexecutable":
        binary.chmod(0o644)
    else:
        binary.unlink()
        if replacement == "directory":
            binary.mkdir()
    before = _stat(case.registration(name))
    # Run the actual rendered registration script without externals repairing the executable first.
    script = case.root / "register.sh"
    script.write_text(case.render(SCRIPT))
    result = case.run(["sh", str(script)])
    assert result.returncode != 0
    assert name in result.stderr
    assert "executable" in result.stderr.lower()
    assert _stat(case.registration(name)) == before
    assert (old / name).read_text() == "#!/bin/sh\necho previous\n"


def test_registration_failure_is_reported_and_next_apply_retries(case, local_releases):
    name = "gh-actions-lock"
    # A real filesystem obstruction makes real gh fail; no fake CLI behavior.
    registry = case.registration(name).parent
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text("blocked registry\n")
    result = case.cm("apply", "--force")
    assert result.returncode != 0
    assert name in result.stderr
    assert "install" in result.stderr
    registry.unlink()
    _apply(case)
    assert case.registration(name).readlink() == case.directory(name)


def test_conflicting_data_home_preserves_inherited_registration_and_state(case, local_releases):
    _apply(case)
    sentinel = case.root / "inherited-data/gh/extensions/sentinel"
    sentinel.mkdir(parents=True)
    (sentinel / "keep").write_text("inherited registration\n")
    state = case.root / "inherited-state/gh/extensions/gh-stack"
    state.parent.mkdir(parents=True)
    state.write_text("inherited update state\n")
    before = _stat(sentinel / "keep"), _stat(state)
    case.env["XDG_DATA_HOME"] = str(sentinel.parents[2])
    case.env["XDG_STATE_HOME"] = str(state.parents[2])
    result = case.cm("apply", "--force")
    assert result.returncode != 0
    assert "XDG_DATA_HOME" in result.stderr
    assert (_stat(sentinel / "keep"), _stat(state)) == before


def test_inherited_state_is_untouched_during_registration_repair(case, local_releases):
    state = case.root / "inherited-state/gh/extensions/gh-stack"
    state.parent.mkdir(parents=True)
    state.write_text("inherited update state\n")
    before = _stat(state)
    case.env["XDG_STATE_HOME"] = str(state.parents[2])
    _apply(case)
    assert _stat(state) == before
    assert state.read_text() == "inherited update state\n"
