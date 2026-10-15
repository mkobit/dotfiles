"""Verify the local upstream plugin route for the pinned OpenCode V1 host."""

import json
import subprocess
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src/chezmoi"


def _render(tmp_path: Path, stdin: str, plugin_method: str | None, tool_method: str | None):
    source = tmp_path / "source"
    source.mkdir(exist_ok=True)
    data = {"ai": {"plugins": {"superpowers": {}}}, "local": {"bin": {"opencode": {}}}}
    if plugin_method is not None:
        data["ai"]["plugins"]["superpowers"]["installation_method"] = plugin_method
    if tool_method is not None:
        data["local"]["bin"]["opencode"]["installation_method"] = tool_method
    return subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(source),
            "--destination",
            str(tmp_path / "destination"),
            "execute-template",
            "--with-stdin",
            "--override-data",
            json.dumps(data),
            "-f",
            str(SOURCE_ROOT / "dot_config/opencode/modify_opencode.json"),
        ],
        input=stdin,
        capture_output=True,
        check=False,
        text=True,
    )


def test_opencode_registers_local_package_and_preserves_other_settings(tmp_path):
    initial = '{"plugin":["custom-plugin"],"model":"custom/model"}'
    result = _render(tmp_path, initial, "chezmoi_external", "github_releases")
    assert result.returncode == 0, result.stderr
    target = str(tmp_path / "destination/.local/share/agent-plugins/marketplace/plugins/superpowers")
    assert json.loads(result.stdout) == {"plugin": ["custom-plugin", target], "model": "custom/model"}
    repeated = _render(tmp_path, result.stdout, "chezmoi_external", "github_releases")
    assert repeated.returncode == 0, repeated.stderr
    assert repeated.stdout == result.stdout


@pytest.mark.parametrize(
    ("plugin_method", "tool_method"),
    [(None, "preinstalled"), ("none", "preinstalled"), ("chezmoi_external", None), ("chezmoi_external", "none")],
)
def test_opencode_disabled_plugin_or_host_removes_only_managed_package(tmp_path, plugin_method, tool_method):
    target = str(tmp_path / "destination/.local/share/agent-plugins/marketplace/plugins/superpowers")
    initial = json.dumps({"plugin": ["custom-plugin", target], "model": "custom/model"})
    result = _render(tmp_path, initial, plugin_method, tool_method)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"plugin": ["custom-plugin"], "model": "custom/model"}
    repeated = _render(tmp_path, result.stdout, plugin_method, tool_method)
    assert repeated.returncode == 0, repeated.stderr
    assert repeated.stdout == result.stdout


@pytest.mark.parametrize(
    ("plugin_method", "tool_method"), [(None, None), ("none", "preinstalled"), ("chezmoi_external", "none")]
)
def test_opencode_disabled_configuration_preserves_custom_input(tmp_path, plugin_method, tool_method):
    initial = '{\n  "plugin": ["custom-plugin"],\n  "model": "custom/model"\n}\n'
    result = _render(tmp_path, initial, plugin_method, tool_method)
    assert result.returncode == 0, result.stderr
    assert result.stdout == initial
