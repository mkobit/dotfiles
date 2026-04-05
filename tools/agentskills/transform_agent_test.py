"""Tests for transform_agent.py — validates tool-specific agent Markdown rendering."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from click.testing import CliRunner

from tools.agentskills.transform_agent import main


def _write_ir(tmp_path: Path, data: dict[str, object]) -> Path:
    p = tmp_path / "agent.ir.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _base_ir(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": "1",
        "atom_type": "agent",
        "source_format": "claude-agents",
        "name": "my-agent",
        "description": "Does things",
        "body": "You are helpful.",
        "model": None,
        "effort": None,
        "tools": None,
        "disallowedTools": None,
        "maxTurns": None,
        "isolation": None,
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


def test_claude_includes_all_claude_fields(tmp_path: Path) -> None:
    ir = _base_ir(
        tools=["Read", "Bash"],
        disallowedTools=["Write"],
        maxTurns=5,
        isolation="worktree",
    )
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "claude", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert fm["disallowedTools"] == ["Write"]
    assert fm["maxTurns"] == 5
    assert fm["isolation"] == "worktree"


def test_claude_basic_fields(tmp_path: Path) -> None:
    ir = _base_ir(model="claude-opus-4-5", effort="high")
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "claude", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert fm["name"] == "my-agent"
    assert fm["description"] == "Does things"
    assert fm["model"] == "claude-opus-4-5"
    assert fm["effort"] == "high"


def test_claude_body_preserved(tmp_path: Path) -> None:
    ir = _base_ir(body="You are a helpful agent.\n\nBe concise.")
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "claude", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    content = out.read_text()
    assert "You are a helpful agent." in content
    assert "Be concise." in content


# ---------------------------------------------------------------------------
# Gemini output — Claude-only fields stripped
# ---------------------------------------------------------------------------


def test_gemini_strips_claude_only_fields(tmp_path: Path) -> None:
    ir = _base_ir(
        tools=["Read"],
        disallowedTools=["Write"],
        maxTurns=10,
        isolation="worktree",
    )
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "gemini", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert "disallowedTools" not in fm
    assert "maxTurns" not in fm
    assert "isolation" not in fm
    assert fm["tools"] == ["Read"]


def test_cursor_strips_claude_only_fields(tmp_path: Path) -> None:
    ir = _base_ir(disallowedTools=["Bash"], maxTurns=3, isolation="worktree")
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "cursor", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert "disallowedTools" not in fm
    assert "maxTurns" not in fm
    assert "isolation" not in fm


# ---------------------------------------------------------------------------
# Extra fields passthrough / filtering
# ---------------------------------------------------------------------------


def test_extra_fields_pass_through_for_claude(tmp_path: Path) -> None:
    ir = _base_ir(extra={"custom-field": "hello", "isolation": "worktree"})
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "claude", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert fm["custom-field"] == "hello"
    assert fm["isolation"] == "worktree"


def test_extra_claude_only_keys_stripped_for_gemini(tmp_path: Path) -> None:
    ir = _base_ir(extra={"isolation": "worktree", "safe-key": "kept"})
    out = tmp_path / "out.md"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(_write_ir(tmp_path, ir)), str(out), "--tool", "gemini", "--scope", "user"],
    )
    assert result.exit_code == 0, result.output
    fm = _parse_frontmatter(out.read_text())
    assert "isolation" not in fm
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
