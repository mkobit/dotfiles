from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from termstatus.segments.chezmoi import (
    _BASE_RELATIVE_PATH,
    _format_repo,
    detect_chezmoi_root,
    generate_chezmoi_segment,
)
from termstatus.segments.git import AheadBehindInfo, BranchRemoteInfo, GitInfo, GitStatusInfo


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
        info = GitInfo(
            branch="main",
            remote="https://github.com/user/repo",
            dirty=False,
            staged=False,
            untracked=False,
            ahead=0,
            behind=0,
            is_repo=True,
            stash_count=0,
        )
        results = _format_repo("ovl", info, line=2)
        assert len(results) == 4
        assert results[0].line == 2
        assert results[0].column == 0
        assert "ovl" in results[0].segment.text
        assert results[1].column == 1
        assert "main" in results[1].segment.text
        assert results[2].column == 2
        assert results[3].column == 3

    def test_dirty_repo_with_ahead_behind(self):
        info = GitInfo(
            branch="feature",
            remote=None,
            dirty=True,
            staged=True,
            untracked=False,
            ahead=2,
            behind=1,
            is_repo=True,
            stash_count=0,
        )
        results = _format_repo("base", info, line=3)
        assert len(results) == 4
        assert results[0].line == 3
        assert results[0].column == 0
        assert "base" in results[0].segment.text
        assert results[1].column == 1
        assert "feature" in results[1].segment.text
        assert results[2].column == 2
        assert results[3].column == 3
        assert "↑2" in results[3].segment.text
        assert "↓1" in results[3].segment.text

    def test_clean_no_remote_no_right_segment(self):
        info = GitInfo(
            branch="main",
            remote=None,
            dirty=False,
            staged=False,
            untracked=False,
            ahead=0,
            behind=0,
            is_repo=True,
            stash_count=0,
        )
        results = _format_repo("ovl", info, line=2)
        assert len(results) == 3
        assert results[0].column == 0
        assert results[1].column == 1
        assert results[2].column == 2


@pytest.mark.asyncio
class TestGenerateChezmoiSegment:
    @patch("termstatus.segments.chezmoi._check_is_repo", new_callable=AsyncMock)
    @patch("termstatus.segments.chezmoi._get_branch_and_remote", new_callable=AsyncMock)
    @patch("termstatus.segments.chezmoi._get_status", new_callable=AsyncMock)
    @patch("termstatus.segments.chezmoi._get_ahead_behind", new_callable=AsyncMock)
    @patch("termstatus.segments.chezmoi._get_stash_count", new_callable=AsyncMock)
    async def test_both_repos_present(
        self,
        mock_stash: AsyncMock,
        mock_ab: AsyncMock,
        mock_status: AsyncMock,
        mock_branch: AsyncMock,
        mock_is_repo: AsyncMock,
        tmp_path: Path,
    ):
        mock_is_repo.return_value = True
        mock_branch.return_value = BranchRemoteInfo(branch="main", remote="https://github.com/user/repo")
        mock_status.return_value = GitStatusInfo(dirty=False, staged=False, untracked=False)
        mock_ab.return_value = AheadBehindInfo(ahead=0, behind=0)
        mock_stash.return_value = 0

        (tmp_path / ".chezmoiroot").write_text("src/chezmoi")
        (tmp_path / "src" / "base" / ".git").mkdir(parents=True)

        results = await generate_chezmoi_segment(tmp_path, tmp_path)

        assert len(results) >= 2
        generators = {r.generator for r in results}
        assert "internal.chezmoi" in generators
        lines = {r.line for r in results}
        assert 2 in lines
        assert 3 in lines

    @patch("termstatus.segments.chezmoi._check_is_repo", new_callable=AsyncMock)
    async def test_no_repos_returns_empty(self, mock_is_repo: AsyncMock, tmp_path: Path):
        mock_is_repo.return_value = False
        (tmp_path / ".chezmoiroot").write_text("src/chezmoi")
        (tmp_path / "src" / "base" / ".git").mkdir(parents=True)

        results = await generate_chezmoi_segment(tmp_path, tmp_path)
        assert results == []
