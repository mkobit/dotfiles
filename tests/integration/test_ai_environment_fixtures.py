"""Verify environment-scoped capabilities in composed chezmoi fixtures."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src/chezmoi"
AUTHORED_CAPABILITIES_EXTERNAL = SOURCE_ROOT / ".chezmoiexternals/ai-authored-capabilities.toml.tmpl"
PLUGIN_BRIDGE_DATA = SOURCE_ROOT / ".chezmoidata/ai/plugin-bridge.toml"
MARKETPLACE_TEMPLATES = (
    Path("dot_local/share/agent-plugins/marketplace/dot_claude-plugin/marketplace.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplace/dot_agents/plugins/marketplace.json.tmpl"),
)


def _write_fixture_source(source: Path, repo_root: Path, config: Path, environment: str) -> None:
    (source / ".chezmoiexternals").mkdir(parents=True)
    shutil.copy2(
        AUTHORED_CAPABILITIES_EXTERNAL,
        source / ".chezmoiexternals/ai-authored-capabilities.toml.tmpl",
    )
    data_file = source / ".chezmoidata/ai/plugin-bridge.toml"
    data_file.parent.mkdir(parents=True)
    shutil.copy2(PLUGIN_BRIDGE_DATA, data_file)

    for relative_path in MARKETPLACE_TEMPLATES:
        target_file = source / relative_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_ROOT / relative_path, target_file)

    capabilities = {
        "mydev-capability": "mydev",
        "mydata-capability": "mydata",
    }
    config_lines = [
        "[data.ai.plugin_bridge]",
        f"environment = {json.dumps(environment)}",
        "",
    ]
    for capability, enabled_environment in capabilities.items():
        skill = repo_root / "src/overlay-plugins" / capability / "skills/example/SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text(f"# {capability}\n", encoding="utf-8")
        config_lines.extend(
            [
                f"[data.ai.plugin_bridge.capabilities.{capability}]",
                f'description = "Fixture capability for {enabled_environment}."',
                f'source_dir = "src/overlay-plugins/{capability}"',
                'marketplace = "dotfiles"',
                'hosts = ["claude", "codex", "cursor"]',
                f"environments = [{json.dumps(enabled_environment)}]",
                "",
                f"[data.ai.plugin_bridge.capabilities.{capability}.skills]",
                'example = "present"',
                "",
            ]
        )
    config.write_text("\n".join(config_lines), encoding="utf-8")


def _apply(source: Path, destination: Path, config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--config",
            str(config),
            "--refresh-externals=always",
            "apply",
        ],
        capture_output=True,
        check=False,
        cwd=destination.parent,
        text=True,
    )


def _snapshot(destination: Path) -> dict[str, bytes]:
    roots = [
        destination / ".local/share/agent-plugins/marketplace",
        destination / ".cursor/plugins/local/mydev-capability",
        destination / ".cursor/plugins/local/mydata-capability",
    ]
    return {
        path.relative_to(destination).as_posix(): path.read_bytes()
        for root in roots
        if root.exists()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize(
    ("environment", "selected", "absent"),
    [
        ("mydev", "mydev-capability", "mydata-capability"),
        ("mydata", "mydata-capability", "mydev-capability"),
    ],
)
def test_environment_fixture_selects_capability_and_cursor_projection(tmp_path, environment, selected, absent):
    """The selected environment gets its marketplace entry and fresh Cursor skill projection."""
    repo_root = tmp_path / "repo"
    source = repo_root / "src/chezmoi"
    destination = tmp_path / "destination"
    destination.mkdir()
    config = tmp_path / "chezmoi.toml"
    _write_fixture_source(source, repo_root, config, environment)

    first_apply = _apply(source, destination, config)
    assert first_apply.returncode == 0, first_apply.stderr

    claude_marketplace = destination / ".local/share/agent-plugins/marketplace/.claude-plugin/marketplace.json"
    codex_marketplace = destination / ".local/share/agent-plugins/marketplace/.agents/plugins/marketplace.json"
    claude_names = {plugin["name"] for plugin in json.loads(claude_marketplace.read_text())["plugins"]}
    codex_names = {plugin["name"] for plugin in json.loads(codex_marketplace.read_text())["plugins"]}
    expected_names = {"mkobit-dotfiles", selected}
    assert claude_names == expected_names
    assert codex_names == expected_names

    selected_skill = destination / ".cursor/plugins/local" / selected / "skills/example/SKILL.md"
    absent_skill = destination / ".cursor/plugins/local" / absent / "skills/example/SKILL.md"
    assert selected_skill.read_text(encoding="utf-8") == f"# {selected}\n"
    assert not absent_skill.exists()

    first_snapshot = _snapshot(destination)
    second_apply = _apply(source, destination, config)
    assert second_apply.returncode == 0, second_apply.stderr
    assert _snapshot(destination) == first_snapshot
