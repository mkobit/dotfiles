import io
import json
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import claude_statusline.main as main_module
from claude_statusline.models import ContextWindowInfo, GitInfo
from claude_statusline.segments.claude import format_context_usage
from claude_statusline.segments.constants import (
    GREEN,
    RED,
    YELLOW,
    get_icon,
)
from claude_statusline.segments.git import format_git_full
from claude_statusline.segments.workspace import shorten_path


class TestStatusLine(unittest.TestCase):
    def test_format_context_usage(self) -> None:
        cw_low = ContextWindowInfo(used_percentage=10.0)
        res_low = format_context_usage(cw_low)
        self.assertIsNotNone(res_low)
        assert res_low is not None
        self.assertIn(GREEN, res_low.text)

        cw_med = ContextWindowInfo(used_percentage=55.0)
        res_med = format_context_usage(cw_med)
        self.assertIsNotNone(res_med)
        assert res_med is not None
        self.assertIn(YELLOW, res_med.text)

        cw_high = ContextWindowInfo(used_percentage=95.0)
        res_high = format_context_usage(cw_high)
        self.assertIsNotNone(res_high)
        assert res_high is not None
        self.assertIn(RED, res_high.text)

        cw_none = ContextWindowInfo(used_percentage=None)
        res_none = format_context_usage(cw_none)
        self.assertIsNotNone(res_none)
        assert res_none is not None
        self.assertIn("0%", res_none.text)
        self.assertIn(GREEN, res_none.text)

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

        info = GitInfo(**base_kwargs)
        res = format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn("main", res.text)
        self.assertIn(get_icon("clean"), res.text)
        self.assertIn(get_icon("remote"), res.text)

        base_kwargs["dirty"] = True
        info = GitInfo(**base_kwargs)
        res = format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn(get_icon("dirty"), res.text)

        base_kwargs["dirty"] = False
        base_kwargs["staged"] = True
        info = GitInfo(**base_kwargs)
        res = format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn(get_icon("staged"), res.text)

        base_kwargs["staged"] = False
        base_kwargs["untracked"] = True
        info = GitInfo(**base_kwargs)
        res = format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn(get_icon("untracked"), res.text)

        base_kwargs["untracked"] = False
        base_kwargs["ahead"] = 2
        base_kwargs["behind"] = 1
        info = GitInfo(**base_kwargs)
        res = format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn("↑2", res.text)
        self.assertIn("↓1", res.text)

    @patch("subprocess.run")
    def test_get_git_info_fresh(self, mock_run: MagicMock) -> None:
        def side_effect(cmd: Any, **kwargs: Any) -> Any:
            cmd_list = cmd if isinstance(cmd, list) else cmd.split()
            mock_res = MagicMock()
            mock_res.returncode = 0
            if "rev-parse" in cmd_list and "HEAD" in cmd_list:
                mock_res.stdout = "feature-branch\n"
            elif "ls-remote" in cmd_list:
                mock_res.stdout = "git@github.com:user/repo.git\n"
            elif "status" in cmd_list:
                mock_res.stdout = " M modified_file.py\n?? untracked.py\n"
            elif "rev-list" in cmd_list:
                mock_res.stdout = "1\t0\n"
            else:
                mock_res.stdout = ""
            return mock_res

        mock_run.side_effect = side_effect

        with patch.object(Path, "exists", return_value=False):
            with patch("claude_statusline.main._check_is_repo", return_value=True):
                info = main_module.get_git_info(Path("/tmp/repo"), None)

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

        with patch.object(main_module, "get_git_info") as mock_get_git_info:
            mock_get_git_info.return_value = GitInfo(
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
                main_module.main()

            self.assertEqual(mock_print.call_count, 3)

            line1 = mock_print.call_args_list[0][0][0]
            self.assertIn("Claude 3", line1)

            line2 = mock_print.call_args_list[1][0][0]
            self.assertIn("MySession", line2)

            line3 = mock_print.call_args_list[2][0][0]
            self.assertIn("main", line3)
            self.assertIn("0.42", line3)
            self.assertIn("50%", line3)

    def test_shorten_path(self) -> None:
        home = Path("/home/user")

        with patch.object(Path, "home", return_value=home):
            p1 = Path("/home/user/projects/repo")
            self.assertEqual(shorten_path(p1), "~/projects/repo")

            p2 = Path("/home/user/src/github.com/org/repo/subdir")
            self.assertEqual(shorten_path(p2), ".../repo/subdir")

            p3 = Path("/opt/tool/src/main")
            self.assertEqual(shorten_path(p3), ".../src/main")

            p4 = Path("/home/user")
            self.assertEqual(shorten_path(p4), "~")


if __name__ == "__main__":
    unittest.main()
