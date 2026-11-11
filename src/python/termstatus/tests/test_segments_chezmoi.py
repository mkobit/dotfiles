from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from termstatus.segments.chezmoi import (
    _BASE_RELATIVE_PATH,
    _format_repo,
    detect_chezmoi_root,
    generate_chezmoi_segment,
)
from termstatus.segments.git import GitInfo


class TestDetectChezmoiRoot:
    def test_returns_none_when_no_chezmoiroot(self, tmp_path: Path):
        subdir = tmp_path / "a" / "b"
        subdir.mkdir(parents=True)
        assert detect_chezmoi_root(subdir) is None

    def test_detects_when_chezmoiroot_without_base(self, tmp_path: Path):
        (tmp_path / ".chezmoiroot").write_text("src/chezmoi")
        subdir = tmp_path / "src" / "chezmoi"
        subdir.mkdir(parents=True)
        assert detect_chezmoi_root(subdir) == tmp_path

    def test_returns_root_when_both_present(self, tmp_path: Path):
        (tmp_path / ".chezmoiroot").write_text("src/chezmoi")
        base_git = tmp_path / _BASE_RELATIVE_PATH / ".git"
        base_git.mkdir(parents=True)
        assert detect_chezmoi_root(tmp_path) == tmp_path

    def test_detects_from_subdirectory(self, tmp_path: Path):
        (tmp_path / ".chezmoiroot").write_text("src/chezmoi")
        base_git = tmp_path / _BASE_RELATIVE_PATH / ".git"
        base_git.mkdir(parents=True)
        subdir = tmp_path / "src" / "chezmoi" / "dot_config"
        subdir.mkdir(parents=True)
        assert detect_chezmoi_root(subdir) == tmp_path

    def test_detects_from_base_subdirectory(self, tmp_path: Path):
        (tmp_path / ".chezmoiroot").write_text("src/chezmoi")
        base_git = tmp_path / _BASE_RELATIVE_PATH / ".git"
        base_git.mkdir(parents=True)
        subdir = tmp_path / "src" / "base" / "src" / "python"
        subdir.mkdir(parents=True)
        assert detect_chezmoi_root(subdir) == tmp_path


class TestFormatRepo:
    def test_clean_repo(self):
        info = GitInfo(branch="main", remote="https://github.com/user/repo")
        results = _format_repo("ovl", info, line=2)
        assert len(results) == 4
        assert results[0].line == 2
        assert results[0].column == 0
        assert results[1].column == 1
        assert "ovl" in results[1].segment.text
        assert "main" in results[1].segment.text
        assert results[2].column == 2
        assert results[2].segment.text.startswith("[") and results[2].segment.text.endswith("]")
        assert results[3].column == 4

    def test_dirty_repo_with_ahead_behind(self):
        info = GitInfo(branch="feature", dirty=True, staged=True, ahead=2, behind=1)
        results = _format_repo("base", info, line=3)
        assert len(results) == 4
        assert results[0].line == 3
        assert results[0].column == 0
        assert results[1].column == 1
        assert "base" in results[1].segment.text
        assert "feature" in results[1].segment.text
        assert results[2].column == 2
        assert results[3].column == 4
        assert "↑2" in results[3].segment.text
        assert "↓1" in results[3].segment.text

    def test_clean_no_remote_no_right_segment(self):
        info = GitInfo(branch="main")
        results = _format_repo("ovl", info, line=2)
        assert len(results) == 3
        assert results[0].column == 0
        assert results[1].column == 1
        assert results[2].column == 2

    def test_lead_is_branch_icon_not_label(self):
        info = GitInfo(branch="main")
        with_label = _format_repo("overlay", info, line=2)
        without_label = _format_repo("", info, line=2)
        assert with_label[0].segment.text == without_label[0].segment.text
        assert "overlay" not in with_label[0].segment.text
        assert "overlay" in with_label[1].segment.text

    def test_long_branch_name_truncated(self):
        info = GitInfo(branch="feature/a-very-long-branch-name-that-should-be-truncated")
        results = _format_repo("ovl", info, line=2)
        body_text = results[1].segment.text
        assert "…" in body_text
        assert "feature/a-very-long-branch-name-that-should-be-truncated" not in body_text


@pytest.mark.asyncio
class TestGenerateChezmoiSegment:
    @patch("termstatus.segments.chezmoi.fetch_git_info", new_callable=AsyncMock)
    async def test_both_repos_present(self, mock_fetch: AsyncMock, tmp_path: Path):
        mock_fetch.return_value = GitInfo(branch="main", remote="https://github.com/user/repo")

        (tmp_path / ".chezmoiroot").write_text("src/chezmoi")
        (tmp_path / "src" / "base" / ".git").mkdir(parents=True)

        results = await generate_chezmoi_segment(tmp_path, tmp_path)

        assert len(results) >= 2
        generators = {r.generator for r in results}
        assert "internal.chezmoi" in generators
        lines = {r.line for r in results}
        assert 2 in lines
        assert 3 in lines

    @patch("termstatus.segments.chezmoi.fetch_git_info", new_callable=AsyncMock)
    async def test_no_repos_returns_empty(self, mock_fetch: AsyncMock, tmp_path: Path):
        mock_fetch.return_value = None
        (tmp_path / ".chezmoiroot").write_text("src/chezmoi")
        (tmp_path / "src" / "base" / ".git").mkdir(parents=True)

        results = await generate_chezmoi_segment(tmp_path, tmp_path)
        assert results == []

    @patch("termstatus.segments.chezmoi.fetch_git_info", new_callable=AsyncMock)
    async def test_single_repo_without_base(self, mock_fetch: AsyncMock, tmp_path: Path):
        mock_fetch.return_value = GitInfo(branch="main", remote="https://github.com/user/repo")
        (tmp_path / ".chezmoiroot").write_text("src/chezmoi")

        results = await generate_chezmoi_segment(tmp_path, tmp_path)

        assert len(results) >= 1
        assert all(r.line == 2 for r in results)
        assert {r.generator for r in results} == {"internal.chezmoi"}

    @patch("termstatus.segments.chezmoi.fetch_git_info", new_callable=AsyncMock)
    async def test_single_repo_fetch_fails_returns_empty(self, mock_fetch: AsyncMock, tmp_path: Path):
        mock_fetch.return_value = None
        (tmp_path / ".chezmoiroot").write_text("src/chezmoi")

        results = await generate_chezmoi_segment(tmp_path, tmp_path)
        assert results == []
