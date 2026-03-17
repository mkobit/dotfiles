"""Unit tests for skills_cli core logic."""

import shutil
from pathlib import Path

import pytest

from tools.agents.skills_cli.core import (
    _dirs_match,
    check_skill,
    discover_local_skills,
    discover_tools,
    sync_skill,
)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Create a minimal workspace layout."""
    # Chezmoi tool dirs
    for tool in ("claude", "cursor", "gemini"):
        (tmp_path / "src" / "chezmoi" / f"dot_{tool}" / "skills").mkdir(parents=True)

    # Canonical skills dir
    (tmp_path / "src" / "agents" / "skills").mkdir(parents=True)

    return tmp_path


def _make_skill(base: Path, name: str, content: str = "# Skill") -> Path:
    """Create a minimal skill directory with SKILL.md."""
    skill_dir = base / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


class TestDiscoverTools:
    def test_finds_tools(self, workspace: Path) -> None:
        tools = discover_tools(workspace / "src" / "chezmoi")
        assert tools == ["claude", "cursor", "gemini"]

    def test_empty_when_no_tools(self, tmp_path: Path) -> None:
        tools = discover_tools(tmp_path / "nonexistent")
        assert tools == []


class TestDiscoverLocalSkills:
    def test_finds_skills_with_skill_md(self, workspace: Path) -> None:
        canonical = workspace / "src" / "agents" / "skills"
        _make_skill(canonical, "my-skill")
        _make_skill(canonical, "other-skill")

        skills = discover_local_skills(canonical)
        assert len(skills) == 2
        assert skills[0].name == "my-skill"
        assert skills[0].origin == "local"
        assert skills[1].name == "other-skill"

    def test_skips_dirs_without_skill_md(self, workspace: Path) -> None:
        canonical = workspace / "src" / "agents" / "skills"
        (canonical / "no-skill-md").mkdir()

        skills = discover_local_skills(canonical)
        assert len(skills) == 0


class TestDirsMatch:
    def test_identical_dirs(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (a / "file.txt").write_text("hello")
        (b / "file.txt").write_text("hello")

        assert _dirs_match(a, b)

    def test_different_content(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (a / "file.txt").write_text("hello")
        (b / "file.txt").write_text("world")

        assert not _dirs_match(a, b)

    def test_extra_file(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (a / "file.txt").write_text("hello")
        (b / "file.txt").write_text("hello")
        (b / "extra.txt").write_text("extra")

        assert not _dirs_match(a, b)

    def test_nested_dirs(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        b = tmp_path / "b"
        (a / "sub").mkdir(parents=True)
        (b / "sub").mkdir(parents=True)
        (a / "sub" / "file.txt").write_text("hello")
        (b / "sub" / "file.txt").write_text("hello")

        assert _dirs_match(a, b)


class TestSyncSkill:
    def test_copies_when_target_missing(self, tmp_path: Path) -> None:
        source = _make_skill(tmp_path / "source", "my-skill")
        target = tmp_path / "target" / "my-skill"

        updated = sync_skill(source, target)
        assert updated
        assert (target / "SKILL.md").read_text() == "# Skill"

    def test_skips_when_identical(self, tmp_path: Path) -> None:
        source = _make_skill(tmp_path / "source", "my-skill", "# Same")
        target = _make_skill(tmp_path / "target", "my-skill", "# Same")

        updated = sync_skill(source, target)
        assert not updated

    def test_overwrites_when_different(self, tmp_path: Path) -> None:
        source = _make_skill(tmp_path / "source", "my-skill", "# New")
        target = _make_skill(tmp_path / "target", "my-skill", "# Old")

        updated = sync_skill(source, target)
        assert updated
        assert (target / "SKILL.md").read_text() == "# New"


class TestCheckSkill:
    def test_no_drift_when_identical(self, tmp_path: Path) -> None:
        source = _make_skill(tmp_path / "source", "my-skill", "# Same")
        target = _make_skill(tmp_path / "target", "my-skill", "# Same")

        result = check_skill(source, target)
        assert not result.drifted

    def test_drift_when_different(self, tmp_path: Path) -> None:
        source = _make_skill(tmp_path / "source", "my-skill", "# New")
        target = _make_skill(tmp_path / "target", "my-skill", "# Old")

        result = check_skill(source, target)
        assert result.drifted
        assert "DRIFT" in (result.details or "")

    def test_drift_when_missing(self, tmp_path: Path) -> None:
        source = _make_skill(tmp_path / "source", "my-skill")
        target = tmp_path / "target" / "my-skill"

        result = check_skill(source, target)
        assert result.drifted
        assert "MISSING" in (result.details or "")
