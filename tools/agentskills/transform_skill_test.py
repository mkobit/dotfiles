"""Tests for transform_skill.py — validates tool-specific skill Markdown rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from click.testing import CliRunner

from tools.agentskills.transform_skill import main


def _write_ir(tmp_path: Path, data: dict[str, object]) -> Path:
    p = tmp_path / "skill.ir.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _base_ir(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": "1",
        "atom_type": "skill",
        "source_format": "agentskills.io",
        "name": "my-skill",
        "description": "Does useful things",
        "body": "Use this skill to do useful things.",
        "allowed-tools": None,
        "argument-hint": None,
        "model": None,
        "effort": None,
        "context": None,
        "agent": None,
        "user-invocable": None,
        "disable-model-invocation": None,
        "paths": None,
        "shell": None,
        "extra": {},
        "associated_files": [],
    }
    for k, v in overrides.items():
        base[k] = v
    return base


def _parse_frontmatter(md: str) -> dict[str, object]:
    """Extract YAML frontmatter from a rendered Markdown string."""
    assert md.startswith("---\n")
    end = md.index("\n---\n", 4)
    result: dict[str, object] = yaml.safe_load(md[4:end])
    return result


# ---------------------------------------------------------------------------
# Claude output
# ---------------------------------------------------------------------------


def test_claude_includes_claude_only_fields(tmp_path: Path) -> None:
    ir = _base_ir(
        **{
            "context": "fork",
            "agent": "code-reviewer",
            "user-invocable": True,
            "disable-model-invocation": False,
        }
    )
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "claude", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert fm["context"] == "fork"
    assert fm["agent"] == "code-reviewer"
    assert fm["user-invocable"] is True
    assert fm["disable-model-invocation"] is False


def test_claude_basic_fields(tmp_path: Path) -> None:
    ir = _base_ir(
        **{"allowed-tools": "Read Bash", "model": "claude-opus-4-5", "effort": "high"}
    )
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "claude", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert fm["name"] == "my-skill"
    assert fm["description"] == "Does useful things"
    assert fm["allowed-tools"] == "Read Bash"
    assert fm["model"] == "claude-opus-4-5"
    assert fm["effort"] == "high"


def test_claude_body_preserved(tmp_path: Path) -> None:
    ir = _base_ir(body="First paragraph.\n\nSecond paragraph.")
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "claude", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    content = out.read_text()
    assert "First paragraph." in content
    assert "Second paragraph." in content


# ---------------------------------------------------------------------------
# Gemini / Cursor output — Claude-only fields stripped
# ---------------------------------------------------------------------------


def test_gemini_strips_claude_only_fields(tmp_path: Path) -> None:
    ir = _base_ir(
        **{
            "context": "fork",
            "agent": "code-reviewer",
            "user-invocable": True,
            "disable-model-invocation": True,
        }
    )
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "gemini", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert "context" not in fm
    assert "agent" not in fm
    assert "user-invocable" not in fm
    assert "disable-model-invocation" not in fm


def test_cursor_strips_claude_only_fields(tmp_path: Path) -> None:
    ir = _base_ir(**{"context": "fork", "agent": "reviewer", "user-invocable": False})
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "cursor", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert "context" not in fm
    assert "agent" not in fm
    assert "user-invocable" not in fm


def test_gemini_retains_shared_fields(tmp_path: Path) -> None:
    ir = _base_ir(**{"allowed-tools": "Read", "effort": "low", "paths": "src/**"})
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "gemini", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert fm["allowed-tools"] == "Read"
    assert fm["effort"] == "low"
    assert fm["paths"] == "src/**"


# ---------------------------------------------------------------------------
# Extra fields passthrough / filtering
# ---------------------------------------------------------------------------


def test_extra_fields_pass_through_for_claude(tmp_path: Path) -> None:
    ir = _base_ir(extra={"x-custom": "value", "context": "fork"})
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "claude", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert fm["x-custom"] == "value"
    assert fm["context"] == "fork"


def test_extra_claude_only_keys_stripped_for_gemini(tmp_path: Path) -> None:
    ir = _base_ir(extra={"context": "fork", "agent": "reviewer", "safe-key": "kept"})
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "gemini", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert "context" not in fm
    assert "agent" not in fm
    assert fm["safe-key"] == "kept"


# ---------------------------------------------------------------------------
# Invalid IR
# ---------------------------------------------------------------------------


def test_invalid_ir_exits_nonzero(tmp_path: Path) -> None:
    bad = tmp_path / "bad.ir.json"
    bad.write_text('{"not": "valid"}', encoding="utf-8")
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main, [str(bad), str(out), "--tool", "claude", "--scope", "user"]
    )
    assert result.exit_code != 0


def test_output_has_yaml_frontmatter_delimiters(tmp_path: Path) -> None:
    ir = _base_ir()
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "claude", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    content = out.read_text()
    assert content.startswith("---\n")
    assert "\n---\n" in content
