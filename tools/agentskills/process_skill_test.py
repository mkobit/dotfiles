"""Tests for process_skill.py — validates SkillIR emission for each source format."""

from __future__ import annotations

import json
import os
import stat
import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from tools.agentskills.process_skill import (
    main,
    _project_agentskills,
    _project_plugin,
    _scan_associated_files,
)
from tools.agentskills.models import AssociatedFile, SkillIR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_skill_dir(
    tmp_path: Path, skill_md_content: str, extra_files: dict[str, str] | None = None
) -> Path:
    """Create a skill directory with a SKILL.md and optional extra files."""
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")
    for rel_path, content in (extra_files or {}).items():
        p = skill_dir / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return skill_dir


_VALID_AGENTSKILLS_MD = textwrap.dedent("""\
    ---
    name: test-skill
    description: A mock skill for testing transformation rules
    license: MIT
    compatibility: unix
    ---

    # Test skill

    This is a test skill markdown body.
""")

_VALID_PLUGIN_MD = textwrap.dedent("""\
    ---
    name: my-plugin-skill
    description: A plugin skill with extras
    allowed-tools: bash grep
    effort: medium
    custom-field: hello
    another-extra: 42
    ---

    Plugin body here.
""")

_MISSING_REQUIRED_MD = textwrap.dedent("""\
    ---
    license: MIT
    ---

    Body with no name or description.
""")


# ---------------------------------------------------------------------------
# Unit: _scan_associated_files
# ---------------------------------------------------------------------------


def test_scan_associated_files_empty_dir(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\n---\n", encoding="utf-8")

    result = _scan_associated_files(skill_dir)
    assert result == []


def test_scan_associated_files_skips_skill_md(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\n---\n", encoding="utf-8")
    (skill_dir / "README.md").write_text("readme", encoding="utf-8")

    result = _scan_associated_files(skill_dir)
    assert len(result) == 1
    assert result[0].path == "README.md"


def test_scan_associated_files_detects_executable(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\n---\n", encoding="utf-8")

    script = skill_dir / "run.sh"
    script.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    os.chmod(script, script.stat().st_mode | stat.S_IXUSR)

    non_exec = skill_dir / "data.txt"
    non_exec.write_text("data", encoding="utf-8")
    # Remove execute bit explicitly
    os.chmod(non_exec, 0o644)

    result = {af.path: af.executable for af in _scan_associated_files(skill_dir)}
    assert result["run.sh"] is True
    assert result["data.txt"] is False


def test_scan_associated_files_nested(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("---\n---\n", encoding="utf-8")
    sub = skill_dir / "docs"
    sub.mkdir()
    (sub / "guide.md").write_text("guide", encoding="utf-8")

    result = _scan_associated_files(skill_dir)
    assert any(af.path == "docs/guide.md" for af in result)


# ---------------------------------------------------------------------------
# Unit: _project_agentskills
# ---------------------------------------------------------------------------


def test_project_agentskills_valid() -> None:
    metadata = {"name": "my-skill", "description": "Does things"}
    ir = _project_agentskills(metadata, "body text", [])
    assert ir.name == "my-skill"
    assert ir.description == "Does things"
    assert ir.body == "body text"
    assert ir.source_format == "agentskills.io"
    assert ir.atom_type == "skill"
    assert ir.associated_files == []


def test_project_agentskills_invalid_missing_fields() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _project_agentskills({}, "body", [])


def test_project_agentskills_rejects_extra_fields() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _project_agentskills(
            {"name": "ok-skill", "description": "desc", "unknown-field": "oops"},
            "body",
            [],
        )


# ---------------------------------------------------------------------------
# Unit: _project_plugin
# ---------------------------------------------------------------------------


def test_project_plugin_known_fields() -> None:
    metadata = {
        "name": "plugin-skill",
        "description": "A plugin",
        "allowed-tools": "bash",
        "effort": "high",
    }
    ir = _project_plugin(metadata, "body", [])
    assert ir.name == "plugin-skill"
    assert ir.source_format == "claude-plugin"
    assert ir.allowed_tools == "bash"
    assert ir.effort == "high"
    assert ir.extra == {}


def test_project_plugin_extra_fields_captured() -> None:
    metadata = {
        "name": "plugin-skill",
        "description": "A plugin",
        "custom-field": "hello",
        "another-extra": 42,
    }
    ir = _project_plugin(metadata, "body", [])
    assert ir.extra == {"custom-field": "hello", "another-extra": 42}


def test_project_plugin_accepts_missing_name() -> None:
    # PluginSkill allows name=None; _project_plugin defaults to empty string
    ir = _project_plugin({"description": "desc"}, "body", [])
    assert ir.name == ""


# ---------------------------------------------------------------------------
# CLI integration: process_skill main
# ---------------------------------------------------------------------------


def test_cli_valid_agentskills(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(tmp_path, _VALID_AGENTSKILLS_MD)
    output = tmp_path / "out.ir.json"

    runner = CliRunner()
    result = runner.invoke(
        main, [str(skill_dir), str(output), "--source-format", "agentskills.io"]
    )

    assert result.exit_code == 0, result.output
    assert output.exists()

    data = json.loads(output.read_text())
    assert data["atom_type"] == "skill"
    assert data["source_format"] == "agentskills.io"
    assert data["name"] == "test-skill"
    assert data["description"] == "A mock skill for testing transformation rules"
    assert "Test skill" in data["body"]


def test_cli_invalid_agentskills_exits_nonzero(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(tmp_path, _MISSING_REQUIRED_MD)
    output = tmp_path / "out.ir.json"

    runner = CliRunner()
    result = runner.invoke(main, [str(skill_dir), str(output)])

    assert result.exit_code != 0


def test_cli_plugin_format_captures_extra(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(tmp_path, _VALID_PLUGIN_MD)
    output = tmp_path / "out.ir.json"

    runner = CliRunner()
    result = runner.invoke(
        main, [str(skill_dir), str(output), "--source-format", "claude-plugin"]
    )

    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text())
    assert data["source_format"] == "claude-plugin"
    assert data["extra"]["custom-field"] == "hello"
    assert data["extra"]["another-extra"] == 42


def test_cli_associated_files_included(tmp_path: Path) -> None:
    skill_dir = _make_skill_dir(
        tmp_path,
        _VALID_AGENTSKILLS_MD,
        extra_files={"docs/guide.md": "# Guide", "scripts/run.sh": "#!/bin/sh"},
    )
    # Make run.sh executable
    run_sh = skill_dir / "scripts" / "run.sh"
    os.chmod(run_sh, run_sh.stat().st_mode | stat.S_IXUSR)

    output = tmp_path / "out.ir.json"
    runner = CliRunner()
    result = runner.invoke(main, [str(skill_dir), str(output)])

    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text())
    assoc = {af["path"]: af["executable"] for af in data["associated_files"]}
    assert "docs/guide.md" in assoc
    assert assoc["docs/guide.md"] is False
    assert "scripts/run.sh" in assoc
    assert assoc["scripts/run.sh"] is True


def test_cli_missing_skill_md(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    output = tmp_path / "out.ir.json"

    runner = CliRunner()
    result = runner.invoke(main, [str(empty_dir), str(output)])

    assert result.exit_code != 0
