import os
from pathlib import Path
from typing import Any
import pytest
from tools.agents.generate_config import load_agents_data, generate_claude, generate_cursor, generate_gemini

def test_load_agents_data(tmp_path: Path) -> None:
    # Setup
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    commands_dir = agents_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "test_cmd.toml").write_text('name = "test:cmd"\ndescription = "desc"\ntype = "command"\ninstruction = "run"\n')

    skills_dir = agents_dir / "skills"
    skills_dir.mkdir()
    (skills_dir / "test_skill.toml").write_text('name = "test-skill"\ndescription = "skill desc"\n') # type inferred from dir?

    roles_dir = agents_dir / "roles"
    roles_dir.mkdir()
    (roles_dir / "test_role.toml").write_text('name = "test-role"\ninstruction = "be helpful"\ntype = "role"\n')

    # Execution
    data = load_agents_data(agents_dir)

    # Verification
    assert len(data["command"]) == 1
    assert data["command"][0]["name"] == "test:cmd"

    assert len(data["skill"]) == 1
    assert data["skill"][0]["name"] == "test-skill"

    assert len(data["role"]) == 1
    assert data["role"][0]["name"] == "test-role"

def test_generate_claude(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    data: dict[str, list[dict[str, Any]]] = {
        "command": [{"name": "foo:bar", "description": "d", "instruction": "i"}],
        "skill": [{"name": "my-skill", "description": "sd", "instruction": "si"}]
    }

    generate_claude(data, output_dir)

    assert (output_dir / "dot_claude/commands/foo/bar.md").exists()
    assert (output_dir / "dot_claude/skills/my-skill/SKILL.md").exists()

    cmd_content = (output_dir / "dot_claude/commands/foo/bar.md").read_text()
    assert "description: d" in cmd_content
    assert "# WARNING: This file is auto-generated" in cmd_content

def test_generate_cursor(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    data: dict[str, list[dict[str, Any]]] = {
        "role": [{"name": "System", "instruction": "sys prompt"}],
        "command": [{"name": "cmd1", "description": "d1"}]
    }

    generate_cursor(data, output_dir)

    rules_file = output_dir / "dot_cursorrules"
    assert rules_file.exists()
    content = rules_file.read_text()
    assert "sys prompt" in content
    assert "## cmd1" in content
    assert "# WARNING: This file is auto-generated" in content

def test_generate_gemini(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    data: dict[str, list[dict[str, Any]]] = {
        "role": [{"name": "System", "instruction": "sys prompt"}],
        "command": [{"name": "cmd1", "instruction": "instr1"}]
    }

    generate_gemini(data, output_dir)

    instr_file = output_dir / "dot_config/google-gemini-cli/instructions.md"
    assert instr_file.exists()
    content = instr_file.read_text()
    assert "sys prompt" in content
    assert "## cmd1" in content
    assert "instr1" in content
