"""Verify selected personal SBX guest tools render from existing bin catalogs."""

import json
import subprocess
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHEZMOI_SOURCE = REPO_ROOT / "src" / "chezmoi"
TEMPLATE = CHEZMOI_SOURCE / ".chezmoiexternals" / "sbx-tools.toml.tmpl"


def _catalog(name: str) -> dict:
    path = CHEZMOI_SOURCE / ".chezmoidata" / "bin" / f"{name}.toml"
    with path.open("rb") as catalog_file:
        return tomllib.load(catalog_file)["bin"][name]


def _render(
    *,
    enabled: bool = True,
    tools: dict | None = None,
    arch: str = "amd64",
    catalogs: dict | None = None,
):
    data = {
        "chezmoi": {"arch": arch, "os": "linux"},
        "github_releases": {"base_url": "https://github.com"},
        "bin": catalogs or {name: _catalog(name) for name in ("fd", "ripgrep")},
        "sbx": {"personal": {"enabled": enabled, "tools": tools or {}}},
    }
    return subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPO_ROOT),
            "--override-data",
            json.dumps(data),
            "execute-template",
            "--file",
            str(TEMPLATE),
        ],
        capture_output=True,
        check=False,
        text=True,
    )


def test_selected_guest_tools_render_to_arch_specific_cache_with_checksums():
    rendered = _render(tools={"ripgrep": True, "fd": True})

    assert rendered.returncode == 0, rendered.stderr
    external = tomllib.loads(rendered.stdout)

    for name in ("fd", "ripgrep"):
        release = _catalog(name)["github_releases"]
        target = release["platforms"]["linux_amd64"]
        filename = release["filename_format"].replace("{version}", _catalog(name)["version"])
        filename = filename.replace("{target}", target).replace("{ext}", "")
        tag = release["tag_format"].replace("{version}", _catalog(name)["version"])
        expected_url = release["url_format"].replace("{base}", "https://github.com")
        expected_url = expected_url.replace("{repo}", release["repo"])
        expected_url = expected_url.replace("{tag}", tag).replace("{filename}", filename)
        expected_path = release["path_format"].replace("{version}", _catalog(name)["version"])
        expected_path = expected_path.replace("{target}", target)
        target_path = f".local/share/sbx/tool-cache/linux_amd64/{name}"

        assert external[target_path]["url"] == expected_url
        assert external[target_path]["path"] == expected_path
        assert external[target_path]["checksum"][release["checksum_type"]] == release["checksums"]["linux_amd64"]


def test_selected_guest_tools_render_for_arm64_catalog_entries():
    rendered = _render(tools={"ripgrep": True}, arch="arm64")

    assert rendered.returncode == 0, rendered.stderr
    external = tomllib.loads(rendered.stdout)
    release = _catalog("ripgrep")["github_releases"]
    assert (
        external[".local/share/sbx/tool-cache/linux_arm64/ripgrep"]["checksum"]["sha256"]
        == release["checksums"]["linux_arm64"]
    )


@pytest.mark.parametrize("tools", [{}, {"ripgrep": False}])
def test_missing_or_false_guest_tool_selection_emits_no_tools(tools):
    rendered = _render(tools=tools)

    assert rendered.returncode == 0, rendered.stderr
    assert rendered.stdout == ""


def test_disabled_personal_layer_emits_no_guest_tools():
    rendered = _render(enabled=False, tools={"ripgrep": True})

    assert rendered.returncode == 0, rendered.stderr
    assert rendered.stdout == ""


def test_selected_guest_tool_requires_a_checksum():
    catalogs = {name: _catalog(name) for name in ("fd", "ripgrep")}
    catalogs["ripgrep"]["github_releases"]["checksums"]["linux_amd64"] = ""

    rendered = _render(tools={"ripgrep": True}, catalogs=catalogs)

    assert rendered.returncode != 0
    assert "no checksum for Linux guest platform linux_amd64" in rendered.stderr


def test_selected_guest_tool_fails_for_unsupported_linux_architecture():
    rendered = _render(tools={"ripgrep": True}, arch="s390x")

    assert rendered.returncode != 0
    assert "sbx.personal.tools.ripgrep" in rendered.stderr
    assert "linux_s390x" in rendered.stderr
