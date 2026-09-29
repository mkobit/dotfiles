"""Integration coverage for authored plugin manifest convergence."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src/chezmoi"
IGNORE_TEMPLATE_FRAGMENT = SOURCE_ROOT / ".chezmoitemplates/ai/authored-plugin-manifest-ignore"
EXTERNALS = SOURCE_ROOT / ".chezmoiexternals/ai-authored-capabilities.toml.tmpl"
CLEANUP = SOURCE_ROOT / ".chezmoiscripts/run_onchange_after_00-agent-plugin-authored-capabilities-cleanup.sh.tmpl"
FILTER_INTERPRETER = SOURCE_ROOT / ".chezmoitemplates/python/filter-interpreter"
FILTER_RESOLVER = REPOSITORY_ROOT / "src/python/skill_filter/resolve-interpreter.sh"


def _write_wrappers(source: Path) -> None:
    wrappers = {
        "dot_local/share/agent-plugins/marketplace/plugins/domain-brain/exact_claude/"
        "exact_dot_claude-plugin/plugin.json.tmpl": '{"name":"domain-brain","host":"claude"}\n',
        "dot_local/share/agent-plugins/marketplace/plugins/domain-brain/exact_codex/"
        "exact_dot_codex-plugin/plugin.json.tmpl": '{"name":"domain-brain","host":"codex"}\n',
        "dot_local/share/agent-plugins/marketplace/plugins/domain-brain/exact_cursor/"
        "exact_dot_cursor-plugin/plugin.json.tmpl": '{"name":"domain-brain","host":"cursor"}\n',
        "dot_cursor/plugins/local/domain-brain/exact_dot_cursor-plugin/plugin.json.tmpl": (
            '{"name":"domain-brain","host":"cursor-local"}\n'
        ),
    }
    for relative_path, contents in wrappers.items():
        wrapper = source / relative_path
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        wrapper.write_text(contents, encoding="utf-8")


def _write_config(path: Path, *, hosts: tuple[str, ...], environment: str, declared: bool = True) -> None:
    lines = [
        "[data.ai.plugin_bridge]",
        f"environment = {json.dumps(environment)}",
    ]
    if declared:
        lines.extend(
            [
                "",
                "[data.ai.plugin_bridge.capabilities.domain-brain]",
                'source_dir = "src/overlay-plugins/domain-brain"',
                f"hosts = {json.dumps(hosts)}",
                'environments = ["personal"]',
                "",
                "[data.ai.plugin_bridge.capabilities.domain-brain.skills]",
                'records = "present"',
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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


def _manifest_targets(destination: Path) -> dict[str, Path]:
    marketplace = destination / ".local/share/agent-plugins/marketplace/plugins/domain-brain"
    return {
        "claude": marketplace / "claude/.claude-plugin/plugin.json",
        "codex": marketplace / "codex/.codex-plugin/plugin.json",
        "cursor": marketplace / "cursor/.cursor-plugin/plugin.json",
        "cursor-local": destination / ".cursor/plugins/local/domain-brain/.cursor-plugin/plugin.json",
    }


def _plugin_snapshot(destination: Path) -> dict[str, bytes]:
    roots = (
        destination / ".local/share/agent-plugins/marketplace/plugins/domain-brain",
        destination / ".cursor/plugins/local/domain-brain",
    )
    return {
        path.relative_to(destination).as_posix(): path.read_bytes()
        for root in roots
        if root.exists()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize(
    ("change", "expected_hosts"),
    [
        ("host_removed", {"claude", "codex"}),
        ("environment_disabled", set()),
        ("declaration_removed", set()),
    ],
)
def test_disabled_capability_manifest_cleanup_converges_on_repeat_apply(tmp_path, change, expected_hosts):
    """Disabled authored plugin wrappers disappear and stay absent on the next apply."""
    overlay_root = tmp_path / "overlay"
    source = overlay_root / ".chezmoiroot.assembled/chezmoi"
    destination = tmp_path / "destination"
    destination.mkdir()
    config = tmp_path / "chezmoi.toml"

    (source / ".chezmoiexternals").mkdir(parents=True)
    (source / ".chezmoiscripts").mkdir()
    (source / ".chezmoitemplates/python").mkdir(parents=True)
    shutil.copy2(EXTERNALS, source / ".chezmoiexternals/ai-authored-capabilities.toml.tmpl")
    shutil.copy2(CLEANUP, source / ".chezmoiscripts" / CLEANUP.name)
    shutil.copy2(FILTER_INTERPRETER, source / ".chezmoitemplates/python/filter-interpreter")
    (source.parent / "python/skill_filter").mkdir(parents=True)
    shutil.copy2(FILTER_RESOLVER, source.parent / "python/skill_filter/resolve-interpreter.sh")
    (source / ".chezmoitemplates/ai").mkdir(parents=True)
    shutil.copy2(IGNORE_TEMPLATE_FRAGMENT, source / ".chezmoitemplates/ai/authored-plugin-manifest-ignore")
    (source / ".chezmoiignore.tmpl").write_text(
        '{{ includeTemplate "ai/authored-plugin-manifest-ignore" . }}\n', encoding="utf-8"
    )
    _write_wrappers(source)

    skill = source.parent / "overlay-plugins/domain-brain/skills/records/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# Records\n", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet", str(overlay_root)], check=True)

    targets = _manifest_targets(destination)
    _write_config(config, hosts=("claude", "codex", "cursor"), environment="personal")
    first_apply = _apply(source, destination, config)
    assert first_apply.returncode == 0, first_apply.stderr
    assert all(path.is_file() for path in targets.values())
    sibling = destination / ".local/share/agent-plugins/marketplace/plugins/domain-brain/notes.json"
    sibling.write_text('{"keep":true}\n', encoding="utf-8")

    if change == "host_removed":
        _write_config(config, hosts=("claude", "codex"), environment="personal")
    elif change == "environment_disabled":
        _write_config(config, hosts=("claude", "codex", "cursor"), environment="work")
    else:
        _write_config(config, hosts=(), environment="personal", declared=False)

    second_apply = _apply(source, destination, config)
    assert second_apply.returncode == 0, second_apply.stderr
    assert {host for host, path in targets.items() if path.is_file()} == expected_hosts
    assert sibling.read_text(encoding="utf-8") == '{"keep":true}\n'
    after_transition = _plugin_snapshot(destination)

    third_apply = _apply(source, destination, config)
    assert third_apply.returncode == 0, third_apply.stderr
    assert _plugin_snapshot(destination) == after_transition
