import functools
import hashlib
import json
import shlex
import shutil
import subprocess
import threading
import tomllib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from chezmoi_test_data import installation_method

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src/chezmoi"
EXTERNAL_TEMPLATE = SOURCE_ROOT / "dot_local/.chezmoiexternals/claude.toml.tmpl"
LAUNCHER_TEMPLATE = SOURCE_ROOT / "dot_local/bin/symlink_claude.tmpl"
PLATFORMS = [
    ("darwin", "arm64", "darwin-arm64", "d8cb1e5c79684cc12a8bfc813e3a2073406921b6245744b3009be3ab5651d21e"),
    ("darwin", "amd64", "darwin-x64", "c896d2aee12ff4d95861033d9730d3d22dc19e4f32779134d3399ef3dfb0e77a"),
    ("linux", "arm64", "linux-arm64", "346d294f0103d6fc0de11ac953579b5c62dfa90698a4cfc486b6f927c615e697"),
    ("linux", "amd64", "linux-x64", "1859583ce32920595c61ef868bee52e1b1594f7486db209935e01f1e5e804ae2"),
]


def _render(template, *, method="direct_release", os_name="linux", arch="amd64", destination=None):
    data = {
        "chezmoi": {"os": os_name, "arch": arch},
        "claude_code": {"installation_method": method} if method is not None else {},
    }
    return subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPOSITORY_ROOT),
            *(["--destination", str(destination)] if destination is not None else []),
            "execute-template",
            "--file",
            "--override-data",
            json.dumps(data),
            str(template),
        ],
        capture_output=True,
        check=False,
        text=True,
    )


@pytest.mark.parametrize(("os_name", "arch", "vendor_platform", "checksum"), PLATFORMS)
def test_claude_external_selects_platform_binary(os_name, arch, vendor_platform, checksum):
    result = _render(EXTERNAL_TEMPLATE, os_name=os_name, arch=arch)

    assert result.returncode == 0, result.stderr
    external = tomllib.loads(result.stdout)
    assert external == {
        "lib/claude/2.1.283/claude": {
            "type": "file",
            "url": f"https://downloads.claude.ai/claude-code-releases/2.1.283/{vendor_platform}/claude",
            "executable": True,
            "checksum": {"sha256": checksum},
        }
    }


@pytest.mark.parametrize("method", ["preinstalled", "none", None, "dotfiles.script", "other"])
@pytest.mark.parametrize("template", [EXTERNAL_TEMPLATE, LAUNCHER_TEMPLATE], ids=["external", "launcher"])
def test_claude_unmanaged_methods_emit_no_target(method, template):
    result = _render(template, method=method)

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_claude_external_rejects_unsupported_platform():
    result = _render(EXTERNAL_TEMPLATE, arch="riscv64")

    assert result.returncode != 0
    assert "bin.claude: no direct_release platform entry for linux_riscv64" in result.stderr


def test_claude_launcher_uses_destination(tmp_path):
    destination = tmp_path / "destination"
    result = _render(LAUNCHER_TEMPLATE, destination=destination)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(destination / ".local/lib/claude/2.1.283/claude")


def test_claude_apply_replaces_installer_launcher_and_preserves_old_binary(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    local_source = source / "dot_local"
    (local_source / ".chezmoiexternals").mkdir(parents=True)
    (local_source / "bin").mkdir()
    shutil.copy(EXTERNAL_TEMPLATE, local_source / ".chezmoiexternals/claude.toml.tmpl")
    shutil.copy(LAUNCHER_TEMPLATE, local_source / "bin/symlink_claude.tmpl")
    catalog = tomllib.loads((SOURCE_ROOT / ".chezmoidata/bin/claude.toml").read_text())
    payload = b"#!/bin/sh\nprintf '2.1.283 (Claude Code)\\n'\n"
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    (downloads / "claude").write_bytes(payload)
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(SimpleHTTPRequestHandler, directory=str(downloads))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    release = catalog["bin"]["claude"]["direct_release"]
    release["url_format"] = f"http://127.0.0.1:{server.server_port}/claude"
    release["checksums"]["linux_amd64"] = hashlib.sha256(payload).hexdigest()
    config = tmp_path / "chezmoi.json"
    config.write_text(
        json.dumps(
            {
                "data": {
                    **catalog,
                    "claude_code": {"installation_method": "direct_release"},
                    "chezmoi": {"os": "linux", "arch": "amd64"},
                }
            }
        )
    )
    launcher = destination / ".local/bin/claude"
    launcher.parent.mkdir(parents=True)
    old_binary = destination / ".local/share/claude/versions/old"
    old_binary.parent.mkdir(parents=True)
    old_binary.write_text("previous installation\n")
    launcher.symlink_to(old_binary)
    try:
        result = subprocess.run(
            [
                "chezmoi",
                "--config",
                str(config),
                "--source",
                str(source),
                "--destination",
                str(destination),
                "--cache",
                str(tmp_path / "cache"),
                "--persistent-state",
                str(tmp_path / "state.boltdb"),
                "apply",
                "--force",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    assert result.returncode == 0, result.stderr
    binary = destination / ".local/lib/claude/2.1.283/claude"
    assert launcher.is_symlink()
    assert launcher.readlink() == binary
    assert binary.read_bytes() == payload
    assert binary.stat().st_mode & 0o111 == 0o111
    assert old_binary.read_text() == "previous installation\n"
    version = subprocess.run([str(launcher), "--version"], capture_output=True, text=True, check=False)
    assert version.returncode == 0, version.stderr
    assert version.stdout.strip() == "2.1.283 (Claude Code)"


@pytest.mark.integration
def test_claude_version(host, chezmoi_data, chezmoi_dest):
    """Verify that the claude CLI is accessible and operational."""
    method = installation_method(chezmoi_data, "claude_code")
    if method == "none":
        pytest.skip("Claude Code installation method is set to 'none'")
    launcher = str(chezmoi_dest / ".local/bin/claude") if method == "direct_release" else "claude"
    result = host.run(f"{shlex.quote(launcher)} --version")
    assert result.rc == 0, f"claude --version failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"
    if method == "direct_release":
        assert result.stdout.strip() == f"{chezmoi_data['bin']['claude']['version']} (Claude Code)"


@pytest.mark.integration
def test_claude_settings_json_deployed(host, chezmoi_dest):
    """Verify ~/.claude/settings.json exists after chezmoi apply."""
    settings_file = host.file(str(chezmoi_dest / ".claude" / "settings.json"))
    assert settings_file.exists, "~/.claude/settings.json does not exist"
