import asyncio
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from claude_statusline.segments.constants import (
    CYAN,
    GREEN,
    RED,
    YELLOW,
    get_icon,
)
from claude_statusline.segments.git import format_git_full, generate_git_segment
from claude_statusline.types.git import GitInfo


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


class TestFormatGitFull(unittest.TestCase):
    def test_branch_name_shown(self) -> None:
        res = format_git_full(_git_info())
        assert res is not None
        self.assertIn("main", res.segment.text)

    def test_clean_icon_in_brackets(self) -> None:
        res = format_git_full(_git_info())
        assert res is not None
        self.assertIn(get_icon("clean"), res.segment.text)
        self.assertIn("[", res.segment.text)
        self.assertIn("]", res.segment.text)

    def test_dirty_icon_in_brackets(self) -> None:
        res = format_git_full(_git_info(dirty=True))
        assert res is not None
        self.assertIn(RED, res.segment.text)
        self.assertIn(get_icon("dirty"), res.segment.text)
        self.assertIn("[", res.segment.text)

    def test_staged_icon_in_brackets(self) -> None:
        res = format_git_full(_git_info(staged=True))
        assert res is not None
        self.assertIn(YELLOW, res.segment.text)
        self.assertIn(get_icon("staged"), res.segment.text)

    def test_untracked_icon_in_brackets(self) -> None:
        res = format_git_full(_git_info(untracked=True))
        assert res is not None
        self.assertIn(CYAN, res.segment.text)
        self.assertIn(get_icon("untracked"), res.segment.text)

    def test_ahead_behind_shown(self) -> None:
        res = format_git_full(_git_info(ahead=3, behind=1))
        assert res is not None
        self.assertIn("↑3", res.segment.text)
        self.assertIn("↓1", res.segment.text)

    def test_stash_shown(self) -> None:
        res = format_git_full(_git_info(stash_count=2))
        assert res is not None
        self.assertIn("2", res.segment.text)
        self.assertIn(get_icon("stash"), res.segment.text)

    def test_stash_hidden_when_zero(self) -> None:
        res = format_git_full(_git_info(stash_count=0))
        assert res is not None
        self.assertNotIn(get_icon("stash"), res.segment.text)

    def test_remote_link_points_to_branch(self) -> None:
        res = format_git_full(_git_info(branch="feat/my-feature"))
        assert res is not None
        expected = "https://github.com/example/repo/tree/feat/my-feature"
        self.assertIn(expected, res.segment.text)

    def test_gitlab_remote_link_uses_dash_tree(self) -> None:
        res = format_git_full(
            _git_info(
                remote="https://gitlab.com/org/project",
                branch="main",
            )
        )
        assert res is not None
        self.assertIn("https://gitlab.com/org/project/-/tree/main", res.segment.text)

    def test_no_remote_no_link(self) -> None:
        res = format_git_full(_git_info(remote=None))
        assert res is not None
        self.assertNotIn(get_icon("remote"), res.segment.text)

    def test_worktree_uses_worktree_icon(self) -> None:
        res = format_git_full(_git_info(is_worktree=True))
        assert res is not None
        self.assertIn(get_icon("worktree"), res.segment.text)
        self.assertNotIn(get_icon("branch"), res.segment.text)

    def test_placed_on_line_1(self) -> None:
        res = format_git_full(_git_info())
        assert res is not None
        self.assertEqual(res.line, 1)

    def test_returns_none_for_none_input(self) -> None:
        self.assertIsNone(format_git_full(None))


class TestGenerateGitSegment(unittest.TestCase):
    @patch("asyncio.create_subprocess_exec")
    def test_generates_segment_from_git_commands(self, mock_run: MagicMock) -> None:
        async def side_effect(*cmd: Any, **kwargs: Any) -> Any:
            stdout = ""
            if "rev-parse" in cmd and "HEAD" in cmd:
                stdout = "feature-branch\n"
            elif "ls-remote" in cmd:
                stdout = "git@github.com:user/repo.git\n"
            elif "status" in cmd:
                stdout = " M modified_file.py\n?? untracked.py\n"
            elif "rev-list" in cmd:
                stdout = "1\t0\n"
            elif "rev-parse" in cmd and "--is-inside-work-tree" in cmd:
                stdout = "true\n"

            async def mock_communicate() -> tuple[bytes, bytes]:
                return stdout.encode(), b""

            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = mock_communicate
            return mock_proc

        mock_run.side_effect = side_effect

        with (
            patch.object(Path, "exists", return_value=False),
            patch("claude_statusline.segments.git._check_is_repo", return_value=True),
        ):
            results = asyncio.run(generate_git_segment(Path("/tmp/repo"), False))

        self.assertGreater(len(results), 0)
        text = results[0].segment.text
        self.assertIn("feature-branch", text)
        self.assertIn("https://github.com/user/repo", text)
        self.assertIn(GREEN, text)


if __name__ == "__main__":
    unittest.main()
