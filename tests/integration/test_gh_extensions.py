import hashlib
import json
import os
import shutil
import subprocess
import tomllib
from http.server import SimpleHTTPRequestHandler
from pathlib import Path

import pytest
from integration_support.chezmoi import chezmoi_argv
from integration_support.http import serve_directory

SOURCE = Path(__file__).resolve().parents[2] / "src/chezmoi"
EXTERNAL = Path("dot_local/share/gh-managed/.chezmoiexternals/extensions.toml.tmpl")
SCRIPT = Path(".chezmoiscripts/run_after_09_register-gh-extensions.sh.tmpl")
DISPATCHER = Path("dot_local/bin/.chezmoiexternals/bins.toml.tmpl")
NAMES = ("gh-stack", "gh-actions-lock")


@pytest.fixture(scope="module")
def real_gh(record_testsuite_property):
    executable = shutil.which("gh")
    assert executable, "Unmet prerequisite: real GitHub CLI must be installed"
    executable = Path(executable).resolve()
    version = subprocess.run([str(executable), "--version"], capture_output=True, text=True, check=True, timeout=30)
    record_testsuite_property("gh_version", version.stdout.splitlines()[0])
    return executable


class ExtensionCase:
    def __init__(self, root, executable):
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
        self.gh_binary.symlink_to(executable)
        for relative in (EXTERNAL, SCRIPT, DISPATCHER, Path(".chezmoitemplates/bin/github-releases-entry.tmpl")):
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE / relative, target)
        self.catalog = {}
        for name in NAMES:
            path = SOURCE / f".chezmoidata/bin/{name}.toml"
            self.catalog.update(tomllib.loads(path.read_text())["bin"])
        self.choices = {name: {"installation_method": "github_releases"} for name in NAMES}
        self.write_config()

    def run(self, command, **kwargs):
        for key in ("HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "GH_CONFIG_DIR"):
            assert Path(self.env[key]).resolve().is_relative_to(self.root.resolve())
        return subprocess.run(command, env=self.env, capture_output=True, text=True, check=False, timeout=30, **kwargs)

    def cm(self, *args):
        return self.run(
            chezmoi_argv(
                *args,
                source=self.source,
                destination=self.destination,
                config=self.config,
                cache=self.cache,
                state=self.state,
            )
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
def case(tmp_path, real_gh):
    return ExtensionCase(tmp_path, real_gh)


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

    with serve_directory(downloads, Handler) as base_url:

        def release(name, version):
            payload = f"#!/bin/sh\nprintf '%s\\n' '{name} {version}'\n".encode()
            path = downloads / name / version
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(payload)
            tool = case.catalog[name]
            tool["version"] = version
            source = tool["github_releases"]
            source["url_format"] = f"{base_url}/{name}/{{tag}}"
            source["tag_format"] = "{version}"
            source["checksums"] = dict.fromkeys(source["platforms"], hashlib.sha256(payload).hexdigest())
            case.write_config()
            return payload

        for name in NAMES:
            release(name, "1.0.0")
        yield release, requests


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
def test_platform_catalogs_select_verified_release_assets(case, platform):
    os_name, arch = platform.split("_")
    rendered = tomllib.loads(case.render(EXTERNAL, {"chezmoi": {"os": os_name, "arch": arch}}))
    assert set(rendered) == {f"{name}/{name}" for name in NAMES}
    for name in NAMES:
        tool = case.catalog[name]
        assert rendered[f"{name}/{name}"] == {
            "type": "file",
            "executable": True,
            "url": f"https://github.com/github/{name}/releases/download/v{tool['version']}/{os_name}-{arch}",
            "checksum": {"sha256": tool["github_releases"]["checksums"][platform]},
        }


def test_init_choices_are_separate_from_generic_binaries(case):
    shutil.copy2(SOURCE / ".chezmoi.toml.tmpl", case.source / ".chezmoi.toml.tmpl")
    generated = case.root / "init.toml"
    result = case.cm("init", "--config-path", str(generated), "--promptDefaults")
    assert result.returncode == 0, result.stderr
    data = tomllib.loads(generated.read_text())["data"]
    for name in NAMES:
        assert data["gh"]["extensions"][name]["installation_method"] == "github_releases"
        assert name not in data["local"]["bin"]
    assert tomllib.loads(case.render(DISPATCHER)) == {}


def test_unsupported_platform_disables_extension_choices(case):
    relative = Path(".chezmoi.toml.tmpl")
    shutil.copy2(SOURCE / relative, case.source / relative)
    result = case.cm(
        "execute-template",
        "--init",
        "--override-data",
        json.dumps({"chezmoi": {"os": "freebsd", "arch": "amd64"}}),
        "--file",
        str(case.source / relative),
    )
    assert result.returncode == 0, result.stderr
    data = tomllib.loads(result.stdout)["data"]
    for name in NAMES:
        assert data["gh"]["extensions"][name]["installation_method"] == "none"


def test_initial_apply_exposes_both_public_commands(case, local_releases):
    _apply(case)
    for name in NAMES:
        assert case.registration(name).readlink() == case.directory(name)
        result = case.gh(name.removeprefix("gh-"), "--version")
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == f"{name} {case.catalog[name]['version']}"


def test_apply_reconciles_upgrades_downgrades_and_missing_registration(case, local_releases):
    release, requests = local_releases
    name = "gh-stack"
    state = Path(case.env["XDG_STATE_HOME"]) / "gh/extensions" / name / "state.yml"
    _apply(case)
    for version in ("9.0.0", "0.0.1"):
        payload = release(name, version)
        _apply(case)
        assert (case.directory(name) / name).read_bytes() == payload
        result = case.gh("stack", "--version")
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == f"{name} {version}"
        downloads = len(requests)
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text("preserve update state\n")
        _apply(case)
        assert state.read_text() == "preserve update state\n"
        assert len(requests) == downloads
        assert case.registration(name).readlink() == case.directory(name)
        assert (case.directory(name) / name).read_bytes() == payload
    case.registration(name).unlink()
    _apply(case)
    assert case.registration(name).readlink() == case.directory(name)
    assert len(requests) == downloads
    result = case.gh("stack", "--version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"{name} {version}"
    diff = case.cm("diff", "--exclude=scripts")
    assert diff.returncode == 0, diff.stderr
    assert not diff.stdout.strip()


@pytest.mark.parametrize("kind", ["link", "directory"])
def test_replacement_preserves_external_target_and_clears_stale_state(case, local_releases, kind):
    name = "gh-stack"
    old = _previous_registration(case, name, kind)
    state = case.destination / ".local/state/gh/extensions" / name
    state.mkdir(parents=True)
    (state / "state.yml").write_text("old update state\n")
    _apply(case)
    assert case.registration(name).readlink() == case.directory(name)
    assert (old / name).read_text() == "#!/bin/sh\necho previous\n"
    assert not state.exists(), "Local registration must clear stale update state"
    result = case.gh("stack", "--version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"{name} {case.catalog[name]['version']}"


@pytest.mark.parametrize(
    ("choice", "kind"), [(None, "link"), ("none", "directory")], ids=["missing-key-with-link", "none-with-directory"]
)
def test_disabled_extension_preserves_registration_while_other_works(case, local_releases, choice, kind):
    _, requests = local_releases
    name = "gh-stack"
    old = _previous_registration(case, name, kind)
    state = case.destination / ".local/state/gh/extensions" / name / "state.yml"
    state.parent.mkdir(parents=True)
    state.write_text("unmanaged update state\n")
    if choice is None:
        del case.choices[name]
    else:
        case.choices[name] = {"installation_method": choice}
    case.write_config()
    _apply(case)
    assert all(not request.startswith(f"/{name}/") for request in requests)
    assert not case.directory(name).exists()
    assert (old / name).read_text() == "#!/bin/sh\necho previous\n"
    assert state.read_text() == "unmanaged update state\n"
    if kind == "link":
        assert case.registration(name).readlink() == old
    else:
        assert not case.registration(name).is_symlink()
        assert (case.registration(name) / name).read_text() == "#!/bin/sh\necho previous\n"
        assert (case.registration(name) / "nested/old-target").readlink() == old
    other = "gh-actions-lock"
    result = case.gh("actions-lock", "--version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"{other} {case.catalog[other]['version']}"


def test_absent_gh_choices_are_noop_without_gh_or_supported_data_home(case, local_releases):
    _, requests = local_releases
    case.choices = None
    case.write_config()
    case.gh_binary.unlink()
    case.env["XDG_DATA_HOME"] = str(case.root / "inherited-data")
    _apply(case)
    assert requests == []
    assert not (case.destination / ".local/share/gh").exists()
    assert all(not case.directory(name).exists() for name in NAMES)


def test_disabling_management_preserves_installations_without_gh(case, local_releases):
    _, requests = local_releases
    _apply(case)
    contents = {name: (case.directory(name) / name).read_bytes() for name in NAMES}
    downloads = len(requests)
    case.choices = {name: {"installation_method": "none"} for name in NAMES}
    case.write_config()
    case.gh_binary.unlink()
    case.env["XDG_DATA_HOME"] = str(case.root / "inherited-data")
    _apply(case)
    assert len(requests) == downloads
    for name in NAMES:
        assert case.registration(name).readlink() == case.directory(name)
        assert (case.directory(name) / name).read_bytes() == contents[name]


@pytest.mark.parametrize(
    ("availability", "registration"),
    [("absent", "old"), ("nonexecutable", "matching"), ("directory", "matching")],
    ids=["missing-gh-preserves-old-link", "nonexecutable-gh-skips-before-xdg-check", "directory-is-not-gh"],
)
def test_unavailable_gh_preserves_registration_and_retries(case, local_releases, real_gh, availability, registration):
    _, requests = local_releases
    name = "gh-actions-lock"
    if registration == "old":
        target = _previous_registration(case, name, "link")
    else:
        _apply(case)
        target = case.directory(name)
    content = (target / name).read_bytes()
    state = case.destination / ".local/state/gh/extensions" / name / "state.yml"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text("keep update state\n")
    case.gh_binary.unlink()
    if availability == "nonexecutable":
        shutil.copyfile(real_gh, case.gh_binary)
        case.gh_binary.chmod(0o644)
        case.env["XDG_DATA_HOME"] = str(case.root / "inherited-data")
    elif availability == "directory":
        case.gh_binary.mkdir()

    result = case.cm("apply", "--force")
    assert case.registration(name).is_symlink(), result.stderr
    assert case.registration(name).readlink() == target
    assert (target / name).read_bytes() == content
    assert state.read_text() == "keep update state\n"
    assert result.returncode == 0, result.stderr
    assert "gh extensions" in result.stderr.lower()
    assert "skip" in result.stderr.lower()
    assert str(case.gh_binary) in result.stderr

    downloads = len(requests)
    if availability == "directory":
        case.gh_binary.rmdir()
    elif availability == "nonexecutable":
        case.gh_binary.unlink()
    case.gh_binary.symlink_to(real_gh)
    case.env["XDG_DATA_HOME"] = str(case.destination / ".local/share")
    _apply(case)
    assert len(requests) == downloads
    assert case.registration(name).readlink() == case.directory(name)
    result = case.gh(name.removeprefix("gh-"), "--version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"{name} {case.catalog[name]['version']}"


def test_checksum_rejection_preserves_existing_registration(case, local_releases):
    name = "gh-actions-lock"
    old = _previous_registration(case, name, "link")
    source = case.catalog[name]["github_releases"]
    source["checksums"] = dict.fromkeys(source["platforms"], "0" * 64)
    case.write_config()
    result = case.cm("apply", "--force")
    assert result.returncode != 0
    assert name in result.stderr
    assert case.registration(name).readlink() == old
    assert (old / name).read_text() == "#!/bin/sh\necho previous\n"
    assert not (case.directory(name) / name).exists()


@pytest.mark.parametrize("replacement", ["missing", "nonexecutable", "directory"])
def test_invalid_replacement_preserves_registration(case, local_releases, replacement):
    name = "gh-stack"
    _apply(case)
    case.registration(name).unlink()
    old = _previous_registration(case, name, "link")
    binary = case.directory(name) / name
    if replacement == "nonexecutable":
        binary.chmod(0o644)
    else:
        binary.unlink()
        if replacement == "directory":
            binary.mkdir()
    # Exercise registration directly so externals cannot repair the invalid file first.
    script = case.root / "register.sh"
    script.write_text(case.render(SCRIPT))
    result = case.run(["sh", str(script)])
    assert result.returncode != 0
    assert name in result.stderr
    assert "executable" in result.stderr.lower()
    assert case.registration(name).readlink() == old
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
    result = case.gh("actions-lock", "--version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"{name} {case.catalog[name]['version']}"


def test_conflicting_data_home_preserves_inherited_registration_and_state(case, local_releases):
    _apply(case)
    sentinel = case.root / "inherited-data/gh/extensions/sentinel"
    sentinel.mkdir(parents=True)
    (sentinel / "keep").write_text("inherited registration\n")
    state = case.root / "inherited-state/gh/extensions/gh-stack"
    state.parent.mkdir(parents=True)
    state.write_text("inherited update state\n")
    case.env["XDG_DATA_HOME"] = str(sentinel.parents[2])
    case.env["XDG_STATE_HOME"] = str(state.parents[2])
    result = case.cm("apply", "--force")
    assert result.returncode != 0
    assert "XDG_DATA_HOME" in result.stderr
    assert (sentinel / "keep").read_text() == "inherited registration\n"
    assert state.read_text() == "inherited update state\n"
    for name in NAMES:
        assert case.registration(name).readlink() == case.directory(name)


def test_inherited_state_is_untouched_during_registration(case, local_releases):
    state = case.root / "inherited-state/gh/extensions/gh-stack"
    state.parent.mkdir(parents=True)
    state.write_text("inherited update state\n")
    case.env["XDG_STATE_HOME"] = str(state.parents[2])
    _apply(case)
    assert state.read_text() == "inherited update state\n"
    assert case.registration("gh-stack").readlink() == case.directory("gh-stack")
