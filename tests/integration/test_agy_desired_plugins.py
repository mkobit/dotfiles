"""Check that the agy plugin bridge desires exactly the plugins that chezmoi renders for it."""

import json
from pathlib import Path

from chezmoi_cli import ChezmoiCli
from skill_filter import plugin_bridge

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src/chezmoi"
AGENT_PLUGINS = ".local/share/agent-plugins"
AGY_MANIFESTS = ("plugin.json", ".antigravity-plugin/plugin.json")


def _chezmoi(tmp_path: Path, *args: str) -> str:
    destination = tmp_path / "destination"
    destination.mkdir(exist_ok=True)
    result = (
        ChezmoiCli(
            config=tmp_path / "chezmoi.json",
            source=SOURCE_ROOT,
            destination=destination,
            cache=tmp_path / "cache",
            persistent_state=tmp_path / "state.boltdb",
            no_tty=True,
        )
        .raw(*args)
        .run()
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


def test_agy_desired_set_matches_the_rendered_plugins(tmp_path):
    config = {"data": {"local": {"bin": {"agy": {"installation_method": "preinstalled"}}}}}
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

    bridge = json.loads(_chezmoi(tmp_path, "execute-template", '{{ includeTemplate "ai/plugin-bridge" . }}'))
    assert bridge["cli_hosts"] == ["antigravity"]
    desired = plugin_bridge._desired_agy_plugins(bridge["marketplaces"], destination)
    assert set(desired) == expected
    for name, (_, plugin_dir, version) in desired.items():
        assert version == _agy_manifest(plugin_dir)["version"], name
