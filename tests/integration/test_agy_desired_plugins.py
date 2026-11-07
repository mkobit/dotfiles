"""Check that the agy plugin bridge desires exactly the plugins that chezmoi renders for it."""

import json
import subprocess
from pathlib import Path

import pytest

from skill_filter import plugin_bridge

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src/chezmoi"
AGENT_PLUGINS = ".local/share/agent-plugins"
AGY_MANIFESTS = ("plugin.json", ".antigravity-plugin/plugin.json")


def _chezmoi(tmp_path: Path, *args: str) -> str:
    destination = tmp_path / "destination"
    destination.mkdir(exist_ok=True)
    result = subprocess.run(
        [
            "chezmoi",
            "--config",
            str(tmp_path / "chezmoi.json"),
            "--source",
            str(SOURCE_ROOT),
            "--destination",
            str(destination),
            "--cache",
            str(tmp_path / "cache"),
            "--persistent-state",
            str(tmp_path / "state.boltdb"),
            "--no-tty",
            *args,
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _agy_manifest(plugin_dir: Path) -> dict:
    manifests = [plugin_dir / name for name in AGY_MANIFESTS if (plugin_dir / name).is_file()]
    assert len(manifests) == 1, f"{plugin_dir.name}: expected one agy manifest, found {manifests}"
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert isinstance(manifest.get("name"), str) and manifest["name"], plugin_dir.name
    assert isinstance(manifest.get("version"), str) and manifest["version"], plugin_dir.name
    return manifest


@pytest.mark.parametrize("superpowers_method", ["chezmoi_external", "none"])
def test_agy_desired_set_matches_the_rendered_plugins(tmp_path, superpowers_method):
    config = {
        "data": {
            "ai": {"plugins": {"superpowers": {"installation_method": superpowers_method}}},
            "local": {"bin": {"agy": {"installation_method": "preinstalled"}}},
        }
    }
    (tmp_path / "chezmoi.json").write_text(json.dumps(config), encoding="utf-8")
    destination = tmp_path / "destination"
    (destination / AGENT_PLUGINS).mkdir(parents=True)

    # Scripts are excluded: the test needs only the files that the bridge reads.
    _chezmoi(tmp_path, "apply", "--exclude=scripts", str(destination / AGENT_PLUGINS))

    authored = json.loads(_chezmoi(tmp_path, "execute-template", '{{ includeTemplate "ai/authored-plugins" . }}'))
    expected = {name for name, plugin in authored.items() if plugin["enabled"]}
    marketplace_plugins = destination / AGENT_PLUGINS / "marketplace/plugins"
    for name in expected:
        assert _agy_manifest(marketplace_plugins / name)["name"] == name
    assert expected, "no authored plugin is enabled"

    if superpowers_method == "chezmoi_external":
        superpowers = destination / AGENT_PLUGINS / "marketplaces/superpowers-marketplace/plugins/superpowers"
        pinned = json.loads(_chezmoi(tmp_path, "data", "--format=json"))["ai"]["plugins"]["superpowers"]["version"]
        manifest = _agy_manifest(superpowers)
        assert (manifest["name"], manifest["version"]) == ("superpowers", pinned)
        expected.add("superpowers")

    bridge = json.loads(_chezmoi(tmp_path, "execute-template", '{{ includeTemplate "ai/plugin-bridge" . }}'))
    assert bridge["cli_hosts"] == ["antigravity"]
    desired = plugin_bridge._desired_agy_plugins(bridge["marketplaces"], destination)
    assert set(desired) == expected
    for name, (_, plugin_dir, version) in desired.items():
        assert version == _agy_manifest(plugin_dir)["version"], name
