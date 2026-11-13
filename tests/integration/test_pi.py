"""Check Pi deployment with isolated chezmoi source and destination trees."""

import functools
import hashlib
import http.server
import io
import json
import shutil
import subprocess
import tarfile
import threading
import tomllib
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src/chezmoi"


def pi_fixture(tmp_path, method="existing", settings=None):
    source = tmp_path / "source"
    for relative in (
        "dot_pi",
        ".chezmoiscripts/run_after_pi-cleanup.sh.tmpl",
    ):
        original = SOURCE_ROOT / relative
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if original.is_dir():
            shutil.copytree(original, target)
        elif original.exists():
            shutil.copy2(original, target)
    destination = tmp_path / "destination"
    destination.mkdir()
    config = tmp_path / "config.json"
    data = {"local": {"bin": {"pi": {}}}, "pi": {"settings": {} if settings is None else settings}}
    if method is not None:
        data["local"]["bin"]["pi"]["installation_method"] = method
    config.write_text(json.dumps({"data": data}))
    return source, destination, config


def apply_pi(fixture):
    source, destination, config = fixture
    return subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--config",
            str(config),
            "--cache",
            str(source.parent / "cache"),
            "--persistent-state",
            str(source.parent / "state"),
            "apply",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("method", ["existing", "github_releases"])
def test_pi_settings_replace_top_level_values(tmp_path, method):
    fixture = pi_fixture(tmp_path, method, {"cacheWarming": "off", "nested": {"new": True}, "list": []})
    target = fixture[1] / ".pi/agent/settings.json"
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps({"foreign": 7, "nested": {"old": True}, "list": [1]}))
    result = apply_pi(fixture)
    assert result.returncode == 0, result.stderr
    assert json.loads(target.read_text()) == {"foreign": 7, "cacheWarming": "off", "nested": {"new": True}, "list": []}


@pytest.mark.parametrize("method", [None, "none", "unknown", ""])
def test_pi_modes_preserve_unmanaged_files(tmp_path, method):
    fixture = pi_fixture(tmp_path, method)
    destination = fixture[1]
    for relative in (
        ".pi/agent/settings.json",
        ".pi/agent/auth.json",
        ".pi/agent/sessions/session.json",
        ".local/share/pi/pi",
        ".local/bin/pi",
    ):
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("preserve")
    result = apply_pi(fixture)
    assert (result.returncode != 0) == (method in {"unknown", ""}), result.stderr
    for relative in (".pi/agent/auth.json", ".pi/agent/sessions/session.json", ".local/share/pi/pi", ".local/bin/pi"):
        assert (destination / relative).read_text() == "preserve"
    target = destination / ".pi/agent/settings.json"
    if method == "none":
        assert not target.exists()
        assert apply_pi(fixture).returncode == 0
    else:
        assert target.read_text() == "preserve"


@pytest.mark.parametrize("content", ["", "   \n", "broken", "[]", "null", "1", '"text"'])
def test_pi_rejects_invalid_settings_input(tmp_path, content):
    fixture = pi_fixture(tmp_path)
    target = fixture[1] / ".pi/agent/settings.json"
    target.parent.mkdir(parents=True)
    target.write_text(content)
    result = apply_pi(fixture)
    assert result.returncode != 0
    assert target.read_text() == content


def test_pi_creates_missing_settings(tmp_path):
    fixture = pi_fixture(tmp_path)
    result = apply_pi(fixture)
    assert result.returncode == 0, result.stderr
    assert json.loads((fixture[1] / ".pi/agent/settings.json").read_text()) == {}


@pytest.mark.parametrize(
    "settings", [{"flag": False, "count": 2, "text": "", "value": None}, {"list": [1, "two"], "nested": {}}]
)
def test_pi_settings_preserve_native_json_types(tmp_path, settings):
    fixture = pi_fixture(tmp_path, settings=settings)
    result = apply_pi(fixture)
    assert result.returncode == 0, result.stderr
    assert json.loads((fixture[1] / ".pi/agent/settings.json").read_text()) == settings


def test_pi_none_after_enabled_removes_only_settings(tmp_path):
    fixture = pi_fixture(tmp_path, settings={"cacheWarming": "off"})
    result = apply_pi(fixture)
    assert result.returncode == 0, result.stderr
    target = fixture[1] / ".pi/agent/settings.json"
    assert target.exists()
    auth = target.with_name("auth.json")
    auth.write_text("preserve")
    data = json.loads(fixture[2].read_text())
    data["data"]["local"]["bin"]["pi"]["installation_method"] = "none"
    fixture[2].write_text(json.dumps(data))
    for _ in range(2):
        result = apply_pi(fixture)
        assert result.returncode == 0, result.stderr
        assert not target.exists()
        assert auth.read_text() == "preserve"


@pytest.fixture
def release_server(tmp_path):

    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_pi_archive_replacement_preserves_state(tmp_path, release_server):
    """A binary-only install or non-exact update leaves runtime assets wrong."""

    fixture = pi_fixture(tmp_path, "github_releases", {"cacheWarming": "off"})
    source, destination, config = fixture
    for relative in (
        ".chezmoidata/bin/pi.toml",
        ".chezmoitemplates/bin/github-releases-entry.tmpl",
        "dot_local/share/.chezmoiexternals/pi.toml.tmpl",
        "dot_local/bin/symlink_pi.tmpl",
        "dot_local/bin/.chezmoiignore.tmpl",
    ):
        original = SOURCE_ROOT / relative
        if original.exists():
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, target)
    data = json.loads(config.read_text())
    data["data"]["bin"] = tomllib.loads((SOURCE_ROOT / ".chezmoidata/bin/pi.toml").read_text())["bin"]
    tool = data["data"]["bin"]["pi"]
    tool["github_releases"]["base_url"] = release_server
    tool["github_releases"]["url_format"] = "{base}/release-{tag}.tar.gz"
    for version, assets in (
        ("1.5.2", {"pi": "fixture binary", "theme.json": "theme", "stale.txt": "old"}),
        ("1.5.3", {"pi": "new fixture binary", "theme.json": "new theme", "sdk.js": "sdk"}),
    ):
        archive = tmp_path / f"release-v{version}.tar.gz"
        with tarfile.open(archive, "w:gz") as handle:
            for name, content in assets.items():
                entry = tarfile.TarInfo(f"pi/{name}")
                payload = content.encode()
                entry.size = len(payload)
                entry.mode = 0o755 if name == "pi" else 0o644
                handle.addfile(entry, io.BytesIO(payload))
        tool["version"] = version
        checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
        tool["github_releases"]["checksums"] = dict.fromkeys(
            ("darwin_arm64", "darwin_amd64", "linux_arm64", "linux_amd64"), checksum
        )
        config.write_text(json.dumps(data))
        result = apply_pi(fixture)
        assert result.returncode == 0, result.stderr
        installed = destination / ".local/share/pi"
        assert {path.name for path in installed.iterdir()} == set(assets)
        assert (installed / "pi").read_text() == assets["pi"]
        assert (installed / "pi").stat().st_mode & 0o111
        link = destination / ".local/bin/pi"
        assert link.is_symlink()
        assert link.resolve() == installed / "pi"
        auth = destination / ".pi/agent/auth.json"
        auth.write_text("preserve")
    data["data"]["local"]["bin"]["pi"]["installation_method"] = "none"
    config.write_text(json.dumps(data))
    for _ in range(2):
        result = apply_pi(fixture)
        assert result.returncode == 0, result.stderr
        assert not (destination / ".pi/agent/settings.json").exists()
        assert auth.read_text() == "preserve"
        assert link.is_symlink()
        assert (installed / "sdk.js").read_text() == "sdk"


@pytest.mark.parametrize("settings", [[], "bad", 1, False])
def test_pi_rejects_nonobject_configured_settings(tmp_path, settings):
    fixture = pi_fixture(tmp_path, settings=settings)
    result = apply_pi(fixture)
    assert result.returncode != 0
    assert not (fixture[1] / ".pi/agent/settings.json").exists()


def render_pi(tmp_path, template, data, *, init=False):
    source = tmp_path / "render-source"
    source.mkdir()
    for relative in (
        ".chezmoidata/bin/pi.toml",
        ".chezmoidata/bin/codex.toml",
        ".chezmoitemplates/bin/github-releases-entry.tmpl",
    ):
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_ROOT / relative, target)
    config = tmp_path / "render.json"
    config.write_text(json.dumps({"data": data}))
    return subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--destination",
            str(tmp_path / "render-dest"),
            "--config",
            str(config),
            "--cache",
            str(tmp_path / "render-cache"),
            "execute-template",
            *(["--init"] if init else []),
            template,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    "platform,target,checksum",
    [
        ("darwin_arm64", "darwin-arm64", "56b5e194d485ced555667b8ba3276157a8272e9ecde9e001e428af80985bdd9b"),
        ("darwin_amd64", "darwin-x64", "f997a088613514ac97d913aeea7642094d84fe6d46854ff7e64e2c12e536dc50"),
        ("linux_arm64", "linux-arm64", "42805cd5615952fcbbfc9c56b04f8feb84395134952e169a6cdc8d7676975666"),
        ("linux_amd64", "linux-x64", "811c6f2c9e7aaee252b5404252e556fb713aa209c1f7f924226aa77d4ef70cb5"),
    ],
)
@pytest.mark.parametrize(
    "global_base,tool_base,expected_base",
    [
        (None, None, "https://github.com"),
        ("https://global.example", None, "https://global.example"),
        ("https://global.example", "https://tool.example", "https://tool.example"),
    ],
)
def test_pi_release_urls_and_checksums(tmp_path, platform, target, checksum, global_base, tool_base, expected_base):

    data = {"local": {"bin": {"pi": {"installation_method": "github_releases"}}}}
    if global_base:
        data["github_releases"] = {"base_url": global_base}
    if tool_base:
        data["bin"] = {"pi": {"github_releases": {"base_url": tool_base}}}
    os_name, arch = platform.split("_")
    template = (
        '{{- $_ := set .chezmoi "os" "'
        + os_name
        + '" -}}{{- $_ := set .chezmoi "arch" "'
        + arch
        + '" -}}'
        + (SOURCE_ROOT / "dot_local/share/.chezmoiexternals/pi.toml.tmpl").read_text()
    )
    result = render_pi(tmp_path, template, data)
    assert result.returncode == 0, result.stderr
    assert tomllib.loads(result.stdout) == {
        "pi": {
            "type": "archive",
            "url": f"{expected_base}/earendil-works/pi/releases/download/v1.5.2/pi-{target}.tar.gz",
            "stripComponents": 1,
            "exact": True,
            "checksum": {"sha256": checksum},
        }
    }


def test_shared_release_renderer_keeps_optional_exact_out_of_checksum(tmp_path):

    template = '{{ includeTemplate "bin/github-releases-entry.tmpl" (dict "name" "codex" "tool" .bin.codex "platform" "linux_amd64" "base" "https://github.com") }}'
    result = render_pi(tmp_path, template, {})
    assert result.returncode == 0, result.stderr
    external = tomllib.loads(result.stdout)["lib/codex"]
    assert "exact" not in external
    assert set(external["checksum"]) == {"sha256"}


@pytest.mark.parametrize("method", [None, "none", "existing"])
def test_pi_dispatcher_skips_archive_for_inactive_methods(tmp_path, method):
    data = {"local": {"bin": {"pi": {}}}}
    if method is not None:
        data["local"]["bin"]["pi"]["installation_method"] = method
    template = (SOURCE_ROOT / "dot_local/share/.chezmoiexternals/pi.toml.tmpl").read_text()
    result = render_pi(tmp_path, template, data)
    assert result.returncode == 0, result.stderr
    assert not result.stdout.strip()


def test_pi_shared_binary_dispatcher_skips_archive(tmp_path):
    template = (SOURCE_ROOT / "dot_local/bin/.chezmoiexternals/bins.toml.tmpl").read_text()
    result = render_pi(tmp_path, template, {"local": {"bin": {"pi": {"installation_method": "github_releases"}}}})
    assert result.returncode == 0, result.stderr
    assert not result.stdout.strip()


def test_pi_init_sets_static_method_and_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("CI", "true")
    template = (SOURCE_ROOT / ".chezmoi.toml.tmpl").read_text()
    result = render_pi(tmp_path, template, {}, init=True)
    assert result.returncode == 0, result.stderr
    data = tomllib.loads(result.stdout)["data"]
    assert data["local"]["bin"]["pi"]["installation_method"] == "github_releases"
    assert data["pi"]["settings"] == {"cacheWarming": "off"}
