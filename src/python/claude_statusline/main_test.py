import io
import json
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import claude_statusline.main as statusline


class TestStatusLine(unittest.TestCase):
    def test_format_context_usage(self) -> None:
        cw_low = statusline.ContextWindowInfo(used_percentage=10.0)
        self.assertIn(statusline.GREEN, statusline.format_context_usage(cw_low))

        cw_med = statusline.ContextWindowInfo(used_percentage=55.0)
        self.assertIn(statusline.YELLOW, statusline.format_context_usage(cw_med))

        cw_high = statusline.ContextWindowInfo(used_percentage=95.0)
        self.assertIn(statusline.RED, statusline.format_context_usage(cw_high))

        cw_none = statusline.ContextWindowInfo(used_percentage=None)
        output_none = statusline.format_context_usage(cw_none)
        self.assertIn("0%", output_none)
        self.assertIn(statusline.GREEN, output_none)

        cw_cache = statusline.ContextWindowInfo(
            used_percentage=10.0, cache_read_input_tokens=25000
        )
        output_cache = statusline.format_context_usage(cw_cache)
        self.assertIn("25.0k cache", output_cache)

    def test_format_git_full(self) -> None:
        base_kwargs: dict[str, Any] = {
            "branch": "main",
            "remote": "https://github.com/example/repo",
            "dirty": False,
            "staged": False,
            "untracked": False,
            "ahead": 0,
            "behind": 0,
            "is_repo": True,
            "is_worktree": False,
        }

        info = statusline.GitInfo(**base_kwargs)
        output = statusline.format_git_full(info)
        self.assertIn("main", output)
        self.assertIn(statusline.ICON_CLEAN, output)
        self.assertIn(statusline.ICON_REMOTE, output)

        base_kwargs["dirty"] = True
        info = statusline.GitInfo(**base_kwargs)
        output = statusline.format_git_full(info)
        self.assertIn(statusline.ICON_DIRTY, output)

        base_kwargs["dirty"] = False
        base_kwargs["staged"] = True
        info = statusline.GitInfo(**base_kwargs)
        output = statusline.format_git_full(info)
        self.assertIn(statusline.ICON_STAGED, output)

        base_kwargs["staged"] = False
        base_kwargs["untracked"] = True
        info = statusline.GitInfo(**base_kwargs)
        output = statusline.format_git_full(info)
        self.assertIn(statusline.ICON_UNTRACKED, output)

        base_kwargs["untracked"] = False
        base_kwargs["ahead"] = 2
        base_kwargs["behind"] = 1
        info = statusline.GitInfo(**base_kwargs)
        output = statusline.format_git_full(info)
        self.assertIn("↑2", output)
        self.assertIn("↓1", output)

    @patch("subprocess.check_output")
    def test_get_git_info_fresh(self, mock_check_output: MagicMock) -> None:
        def side_effect(cmd: Any, **kwargs: Any) -> Any:
            cmd_list = cmd if isinstance(cmd, list) else cmd.split()
            if "is-inside-work-tree" in cmd_list:
                return b"true"
            if "rev-parse" in cmd_list and "HEAD" in cmd_list:
                return "feature-branch\n"
            if "absolute-git-dir" in cmd_list:
                return "/path/to/.git\n"
            if "ls-remote" in cmd_list:
                return "git@github.com:user/repo.git\n"
            if "status" in cmd_list:
                return " M modified_file.py\n?? untracked.py\n"
            if "rev-list" in cmd_list:
                return "1\t0\n"
            return ""

        mock_check_output.side_effect = side_effect

        with patch.object(Path, "exists", return_value=False):
            info = statusline.get_git_info(Path("/tmp/repo"))

        self.assertIsNotNone(info)
        assert info is not None
        self.assertEqual(info.branch, "feature-branch")
        self.assertEqual(info.remote, "https://github.com/user/repo")
        self.assertTrue(info.dirty)
        self.assertEqual(info.ahead, 1)
        self.assertEqual(info.behind, 0)
        self.assertFalse(info.is_worktree)

    @patch("builtins.print")
    @patch("sys.stdin", new_callable=io.StringIO)
    def test_main(self, mock_stdin: MagicMock, mock_print: MagicMock) -> None:
        input_data = {
            "model": {"display_name": "Claude 3"},
            "workspace": {"current_dir": "/tmp/test"},
            "context_window": {"used_percentage": 50.0},
            "session_name": "MySession",
            "cost": {"total_cost_usd": 0.42},
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with patch.object(statusline, "get_git_info") as mock_get_git_info:
            mock_get_git_info.return_value = statusline.GitInfo(
                branch="main",
                dirty=False,
                staged=False,
                untracked=False,
                ahead=0,
                behind=0,
                remote=None,
                is_repo=True,
                is_worktree=False,
            )

            with patch("shutil.get_terminal_size") as mock_term:
                import os

                mock_term.return_value = os.terminal_size((80, 24))
                statusline.main()

            self.assertEqual(mock_print.call_count, 2)

            line1 = mock_print.call_args_list[0][0][0]
            self.assertIn("Claude 3", line1)
            self.assertIn("50%", line1)
            self.assertIn("#MySession", line1)
            self.assertIn("0.42", line1)

            line2 = mock_print.call_args_list[1][0][0]
            self.assertIn("main", line2)

    def test_shorten_path(self) -> None:
        home = Path("/home/user")

        with patch.object(Path, "home", return_value=home):
            p1 = Path("/home/user/projects/repo")
            self.assertEqual(statusline.shorten_path(p1), "~/projects/repo")

            p2 = Path("/home/user/src/github.com/org/repo/subdir")
            self.assertEqual(statusline.shorten_path(p2), ".../repo/subdir")

            p3 = Path("/opt/tool/src/main")
            self.assertEqual(statusline.shorten_path(p3), ".../src/main")

            p4 = Path("/home/user")
            self.assertEqual(statusline.shorten_path(p4), "~")


if __name__ == "__main__":
    unittest.main()
