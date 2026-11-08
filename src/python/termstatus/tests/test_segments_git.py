from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from termstatus.git_status import VcsState
from termstatus.segments.constants import (
    CYAN,
    RED,
    YELLOW,
    get_icon,
)
from termstatus.segments.git import GitInfo, build_branch_url, fetch_git_info, format_git_full, generate_git_segment


def _git_info(**overrides: Any) -> GitInfo:
    defaults: dict[str, Any] = {
        "branch": "main",
        "remote": "https://github.com/example/repo",
        "dirty": False,
        "staged": False,
        "untracked": False,
        "ahead": 0,
        "behind": 0,
        "is_repo": True,
        "is_worktree": False,
        "stash_count": 0,
    }
    return GitInfo(**{**defaults, **overrides})


class TestFormatGitFull:
    def test_branch_name_shown(self) -> None:
        res = format_git_full(_git_info())
        assert res is not None
        assert "main" in " ".join([r.segment.text for r in res])

    def test_clean_icon_in_brackets(self) -> None:
        res = format_git_full(_git_info())
        assert res is not None
        assert get_icon("clean") in " ".join([r.segment.text for r in res])
        assert "[" in " ".join([r.segment.text for r in res])
        assert "]" in " ".join([r.segment.text for r in res])

    def test_dirty_icon_in_brackets(self) -> None:
        res = format_git_full(_git_info(dirty=True))
        assert res is not None
        assert RED in " ".join([r.segment.text for r in res])
        assert get_icon("dirty") in " ".join([r.segment.text for r in res])
        assert "[" in " ".join([r.segment.text for r in res])

    def test_staged_icon_in_brackets(self) -> None:
        res = format_git_full(_git_info(staged=True))
        assert res is not None
        assert YELLOW in " ".join([r.segment.text for r in res])
        assert get_icon("staged") in " ".join([r.segment.text for r in res])

    def test_untracked_icon_in_brackets(self) -> None:
        res = format_git_full(_git_info(untracked=True))
        assert res is not None
        assert CYAN in " ".join([r.segment.text for r in res])
        assert get_icon("untracked") in " ".join([r.segment.text for r in res])

    def test_ahead_behind_shown(self) -> None:
        res = format_git_full(_git_info(ahead=3, behind=1))
        assert res is not None
        assert "↑3" in " ".join([r.segment.text for r in res])
        assert "↓1" in " ".join([r.segment.text for r in res])

    def test_stash_shown(self) -> None:
        res = format_git_full(_git_info(stash_count=2))
        assert res is not None
        assert "2" in " ".join([r.segment.text for r in res])
        assert get_icon("stash") in " ".join([r.segment.text for r in res])

    def test_stash_hidden_when_zero(self) -> None:
        res = format_git_full(_git_info(stash_count=0))
        assert res is not None
        assert get_icon("stash") not in " ".join([r.segment.text for r in res])

    def test_remote_link_points_to_branch(self) -> None:
        res = format_git_full(_git_info(branch="feat/my-feature"))
        assert res is not None
        expected = "https://github.com/example/repo/tree/feat/my-feature"
        assert expected in " ".join([r.segment.text for r in res])

    def test_gitlab_remote_link_uses_dash_tree(self) -> None:
        res = format_git_full(
            _git_info(
                remote="https://gitlab.com/org/project",
                branch="main",
            )
        )
        assert res is not None
        assert "https://gitlab.com/org/project/-/tree/main" in " ".join([r.segment.text for r in res])

    def test_no_remote_no_link(self) -> None:
        res = format_git_full(_git_info(remote=None))
        assert res is not None
        assert get_icon("remote") not in " ".join([r.segment.text for r in res])

    def test_worktree_uses_worktree_icon(self) -> None:
        res = format_git_full(_git_info(is_worktree=True))
        assert res is not None
        assert get_icon("worktree") in " ".join([r.segment.text for r in res])
        assert get_icon("branch") not in " ".join([r.segment.text for r in res])

    def test_placed_on_line_1(self) -> None:
        res = format_git_full(_git_info())
        assert res is not None
        assert (res[0].line if res else None) == 1

    def test_returns_none_for_none_input(self) -> None:
        assert format_git_full(None) == []


class TestGenerateGitSegment:
    @pytest.mark.asyncio
    async def test_generates_segment_from_probe(self) -> None:
        vcs = VcsState(
            "feature-branch",
            True,
            True,
            ahead=1,
            origin_url="git@github.com:user/repo.git",
            untracked=True,
            stash_count=2,
        )
        with patch("termstatus.segments.git.probe_git", new=AsyncMock(return_value=vcs)):
            results = await generate_git_segment(Path("/tmp/repo"), False)

        text = " ".join(r.segment.text for r in results)
        assert "feature-branch" in text
        assert "https://github.com/user/repo/tree/feature-branch" in text
        assert RED in text and CYAN in text
        assert "↑1" in text and get_icon("stash") in text

    @pytest.mark.asyncio
    async def test_detached_head_uses_head_label(self) -> None:
        with patch("termstatus.segments.git.probe_git", new=AsyncMock(return_value=VcsState(None, False, True))):
            info = await fetch_git_info(Path("/tmp/repo"), True)

        assert info == GitInfo(branch="HEAD", is_worktree=True)

    @pytest.mark.asyncio
    async def test_not_a_repo_returns_nothing(self) -> None:
        with patch("termstatus.segments.git.probe_git", new=AsyncMock(return_value=None)):
            assert await generate_git_segment(Path("/tmp/repo"), False) == []


class TestBuildBranchUrl:
    def test_head_returns_remote_directly(self) -> None:
        assert build_branch_url("https://github.com/user/repo", "HEAD") == "https://github.com/user/repo"

    def test_gitlab_remote_uses_dash_tree(self) -> None:
        url = build_branch_url("https://gitlab.com/group/repo", "main")
        assert url == "https://gitlab.com/group/repo/-/tree/main"

    def test_standard_remote_uses_tree(self) -> None:
        url = build_branch_url("https://github.com/user/repo", "feature-branch")
        assert url == "https://github.com/user/repo/tree/feature-branch"
