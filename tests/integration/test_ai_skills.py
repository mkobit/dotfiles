from pathlib import Path

import pytest

# Tool skill directories actively deployed to by .chezmoiexternals/ai-skills.toml.tmpl.
ACTIVE_SKILL_DIRS = [
    pytest.param(Path(".claude/skills"), id="claude"),
    pytest.param(Path(".gemini/antigravity-cli/skills"), id="antigravity"),
    pytest.param(Path(".cursor/skills"), id="cursor"),
]


def assert_entries_are_valid_skills(skills_dir: Path) -> None:
    """Assert every entry in a skills directory is a directory with a non-empty SKILL.md."""
    for entry in sorted(skills_dir.iterdir()):
        if entry.name == ".DS_Store":
            continue
        assert entry.is_dir(), f"{entry} is not a directory; deployed skills must be directories"
        skill_md = entry / "SKILL.md"
        assert skill_md.is_file(), f"{entry} is missing SKILL.md"
        assert skill_md.stat().st_size > 0, f"{skill_md} is empty"


@pytest.mark.integration
@pytest.mark.parametrize("relative_dir", ACTIVE_SKILL_DIRS)
def test_tool_skill_dir_deployed_and_valid(chezmoi_dest, relative_dir):
    """Verify each active tool's skills directory exists and every skill in it is valid."""
    skills_dir = chezmoi_dest / relative_dir
    assert skills_dir.is_dir(), f"{skills_dir} does not exist after chezmoi apply"
    assert any(skills_dir.iterdir()), f"{skills_dir} contains no skills"
    assert_entries_are_valid_skills(skills_dir)


# Tool agent directories actively deployed to by .chezmoiexternals/ai-agents.toml.tmpl.
ACTIVE_AGENT_DIRS = [
    pytest.param(Path(".claude/agents"), id="claude"),
    pytest.param(Path(".config/opencode/agents"), id="opencode"),
]


@pytest.mark.integration
@pytest.mark.parametrize("relative_dir", ACTIVE_AGENT_DIRS)
def test_agents_dir_deployed_and_valid(chezmoi_dest, relative_dir):
    """Verify each deployed agent source directory contains only non-empty .md agent files."""
    agents_dir = chezmoi_dest / relative_dir
    assert agents_dir.is_dir(), f"{agents_dir} does not exist after chezmoi apply"
    source_dirs = [entry for entry in sorted(agents_dir.iterdir()) if entry.name != ".DS_Store"]
    assert source_dirs, f"{agents_dir} contains no agent sources"
    for source_dir in source_dirs:
        assert source_dir.is_dir(), f"{source_dir} is not a directory; agent sources must be directories"
        agent_files = [entry for entry in sorted(source_dir.iterdir()) if entry.name != ".DS_Store"]
        assert agent_files, f"{source_dir} contains no agents"
        for agent_file in agent_files:
            assert agent_file.suffix == ".md", f"{agent_file} is not an .md agent file"
            assert agent_file.stat().st_size > 0, f"{agent_file} is empty"
