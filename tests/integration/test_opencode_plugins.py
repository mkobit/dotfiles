"""Verify OpenCode configuration follows the host and plugin control plane."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src/chezmoi"


@pytest.mark.parametrize("ignore_layer", ["base", "overlay"])
@pytest.mark.parametrize("tool_method", [None, "none"])
def test_opencode_apply_respects_host_and_plugin_control_plane(tmp_path, ignore_layer, tool_method):
    ignore_source = SOURCE_ROOT
    if ignore_layer == "overlay":
        ignore_source = SOURCE_ROOT.parents[3] / "src/chezmoi"
        if not (ignore_source / ".chezmoiignore.tmpl").is_file():
            pytest.skip("the overlay ignore policy is not available in this checkout")
    source = tmp_path / "source"
    for relative in (
        ".chezmoiignore.tmpl",
        "dot_config/opencode/modify_opencode.json",
        ".chezmoitemplates/ai/authored-plugin-manifest-ignore",
    ):
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2((ignore_source if relative == ".chezmoiignore.tmpl" else SOURCE_ROOT) / relative, target)
    destination = tmp_path / "destination"
    destination.mkdir()
    config = tmp_path / "chezmoi.json"
    target = destination / ".config/opencode/opencode.json"
    package = str(destination / ".local/share/agent-plugins/marketplace/plugins/superpowers")
    foreign = {"plugin": ["custom-plugin"], "model": "custom/model"}
    initial = json.dumps({**foreign, "plugin": ["custom-plugin", package]}, indent=2) + "\n"
    data = {"ai": {"plugins": {"superpowers": {}}}, "local": {"bin": {"opencode": {}}}, "mise": {}}
    for host_method, plugin_method, seed, expected in (
        (tool_method, "chezmoi_external", None, None),
        (tool_method, "chezmoi_external", initial, initial),
        ("preinstalled", "chezmoi_external", json.dumps(foreign), {**foreign, "plugin": ["custom-plugin", package]}),
        ("preinstalled", "none", None, foreign),
    ):
        if seed is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(seed)
        data["local"]["bin"]["opencode"] = {} if host_method is None else {"installation_method": host_method}
        data["ai"]["plugins"]["superpowers"]["installation_method"] = plugin_method
        config.write_text(json.dumps({"data": data}))
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
            ],
            capture_output=True,
            check=False,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        if expected is None:
            assert not target.exists()
        elif isinstance(expected, str):
            assert target.read_text() == expected
        else:
            assert json.loads(target.read_text()) == expected
