"""Test metadata validation against rendered plugin configuration."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).resolve().parents[2] / "scripts/check_skill_metadata.py"
PLUGINS = "dot_local/share/agent-plugins/marketplace/exact_plugins"


def skill(root, plugin, name, metadata=None, host_dir=None):
    path = root / PLUGINS / f"exact_{plugin}"
    if host_dir:
        path /= f"exact_{host_dir}"
    path /= f"exact_skills/exact_{name}"
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text("---\nname: test\n---\n")
    if metadata is not None:
        (path / "exact_agents").mkdir()
        (path / "exact_agents/openai.yaml").write_text(metadata)
    return path


def check(root, data):
    return subprocess.run(
        [sys.executable, str(CHECKER), "--source-root", str(root), "--host", "codex", "--config", "-"],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        check=False,
    )


def test_selects_enabled_codex_skills_and_preserves_policy(tmp_path):
    content = 'interface:\n  display_name: "Readable name"\npolicy:\n  allow_implicit_invocation: false\n'
    chosen = skill(tmp_path, "selected", "chosen", content, "codex")
    skill(tmp_path, "selected", "absent", host_dir="codex")
    skill(tmp_path, "selected", "claude-only", host_dir="claude")
    skill(tmp_path, "disabled", "disabled")
    skill(tmp_path, "claude", "only")
    skill(tmp_path, "other-env", "other")
    outside = tmp_path / "third-party/SKILL.md"
    outside.parent.mkdir()
    outside.write_text("third party")
    config = {
        "ai": {
            "plugins": {"selected": {"host_dirs": {"codex": "codex", "claude": "claude"}}},
            "plugin_bridge": {
                "environment": "local",
                "capabilities": {
                    "selected": {"skills": {"absent": "absent"}},
                    "disabled": {"enabled": False},
                    "claude": {"hosts": ["claude"]},
                    "other-env": {"environments": ["remote"]},
                },
            },
        }
    }
    result = check(tmp_path, config)
    assert result.returncode == 0, result.stderr
    assert "selected/chosen" in result.stdout
    assert "absent" not in result.stdout
    assert "claude-only" not in result.stdout
    assert (chosen / "exact_agents/openai.yaml").read_text() == content


@pytest.mark.parametrize(
    "metadata",
    [
        None,
        "[",
        "{}",
        "interface: {}",
        "interface:\n  display_name: '   '",
        "interface:\n  display_name: 42",
        "interface:\n  display_name: unquoted",
    ],
)
def test_rejects_missing_or_invalid_display_name(tmp_path, metadata):
    path = skill(tmp_path, "sample", "broken", metadata)
    result = check(tmp_path, {})
    assert result.returncode != 0
    assert "sample/broken" in result.stderr
    assert str(path) in result.stderr
    assert "interface.display_name" in result.stderr
