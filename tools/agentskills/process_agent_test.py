"""Tests for process_agent.py — validates AgentIR emission."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
from click.testing import CliRunner

from tools.agentskills.process_agent import main
from tools.agentskills.models import AgentIR


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_VALID_AGENT_MD = textwrap.dedent("""\
    ---
    name: my-reviewer
    description: Reviews code for correctness
    model: claude-opus-4-5
    effort: high
    tools:
      - Read
      - Bash
    maxTurns: 10
    ---

    You are a code reviewer. Be thorough.
""")

_AGENT_WITH_EXTRAS_MD = textwrap.dedent("""\
    ---
    name: extra-agent
    description: Agent with unknown fields
    tools:
      - Read
    custom-field: hello
    anotherExtra: 99
    ---

    Agent body.
""")

_AGENT_MINIMAL_MD = textwrap.dedent("""\
    ---
    description: Minimal agent
    ---

    Minimal body.
""")

_AGENT_DISALLOWED_TOOLS_MD = textwrap.dedent("""\
    ---
    name: safe-agent
    description: Agent with disallowed tools
    disallowedTools:
      - Bash
      - Write
    isolation: worktree
    ---

    Safe agent body.
""")


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


def test_cli_valid_agent(tmp_path: Path) -> None:
    agent_md = tmp_path / "my-reviewer.md"
    agent_md.write_text(_VALID_AGENT_MD, encoding="utf-8")
    output = tmp_path / "out.ir.json"

    runner = CliRunner()
    result = runner.invoke(main, [str(agent_md), str(output)])

    assert result.exit_code == 0, result.output
    assert output.exists()

    data = json.loads(output.read_text())
    assert data["atom_type"] == "agent"
    assert data["source_format"] == "claude-agents"
    assert data["name"] == "my-reviewer"
    assert data["description"] == "Reviews code for correctness"
    assert data["model"] == "claude-opus-4-5"
    assert data["effort"] == "high"
    assert data["tools"] == ["Read", "Bash"]
    assert data["maxTurns"] == 10
    assert "You are a code reviewer" in data["body"]


def test_cli_unknown_fields_go_to_extra(tmp_path: Path) -> None:
    agent_md = tmp_path / "extra-agent.md"
    agent_md.write_text(_AGENT_WITH_EXTRAS_MD, encoding="utf-8")
    output = tmp_path / "out.ir.json"

    runner = CliRunner()
    result = runner.invoke(main, [str(agent_md), str(output)])

    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text())
    assert data["extra"]["custom-field"] == "hello"
    assert data["extra"]["anotherExtra"] == 99
    # Known fields should not be in extra
    assert "name" not in data["extra"]
    assert "tools" not in data["extra"]


def test_cli_name_falls_back_to_stem(tmp_path: Path) -> None:
    agent_md = tmp_path / "inferred-name.md"
    agent_md.write_text(_AGENT_MINIMAL_MD, encoding="utf-8")
    output = tmp_path / "out.ir.json"

    runner = CliRunner()
    result = runner.invoke(main, [str(agent_md), str(output)])

    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text())
    assert data["name"] == "inferred-name"


def test_cli_disallowed_tools_and_isolation(tmp_path: Path) -> None:
    agent_md = tmp_path / "safe-agent.md"
    agent_md.write_text(_AGENT_DISALLOWED_TOOLS_MD, encoding="utf-8")
    output = tmp_path / "out.ir.json"

    runner = CliRunner()
    result = runner.invoke(main, [str(agent_md), str(output)])

    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text())
    assert data["disallowedTools"] == ["Bash", "Write"]
    assert data["isolation"] == "worktree"


def test_cli_source_format_option(tmp_path: Path) -> None:
    agent_md = tmp_path / "plugin-agent.md"
    agent_md.write_text(_VALID_AGENT_MD, encoding="utf-8")
    output = tmp_path / "out.ir.json"

    runner = CliRunner()
    result = runner.invoke(
        main, [str(agent_md), str(output), "--source-format", "claude-plugin"]
    )

    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text())
    assert data["source_format"] == "claude-plugin"


def test_cli_no_associated_files_in_output(tmp_path: Path) -> None:
    agent_md = tmp_path / "my-agent.md"
    agent_md.write_text(_VALID_AGENT_MD, encoding="utf-8")
    output = tmp_path / "out.ir.json"

    runner = CliRunner()
    result = runner.invoke(main, [str(agent_md), str(output)])

    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text())
    assert data["associated_files"] == []


# ---------------------------------------------------------------------------
# Schema version and atom_type
# ---------------------------------------------------------------------------


def test_cli_schema_version_and_atom_type(tmp_path: Path) -> None:
    agent_md = tmp_path / "versioned.md"
    agent_md.write_text(_VALID_AGENT_MD, encoding="utf-8")
    output = tmp_path / "out.ir.json"

    runner = CliRunner()
    result = runner.invoke(main, [str(agent_md), str(output)])

    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text())
    assert data["schema_version"] == "1"
    assert data["atom_type"] == "agent"
