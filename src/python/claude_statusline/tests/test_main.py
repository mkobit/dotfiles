import io
import json
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import claude_statusline.main as main_module
import claude_statusline.segments as segments_module
from claude_statusline.models import ContextWindowInfo, GitInfo


class TestStatusLine(unittest.TestCase):
    def test_format_context_usage(self) -> None:
        cw_low = ContextWindowInfo(used_percentage=10.0)
        res_low = segments_module.format_context_usage(cw_low)
        self.assertIsNotNone(res_low)
        assert res_low is not None
        self.assertIn(segments_module.GREEN, res_low.text)

        cw_med = ContextWindowInfo(used_percentage=55.0)
        res_med = segments_module.format_context_usage(cw_med)
        self.assertIsNotNone(res_med)
        assert res_med is not None
        self.assertIn(segments_module.YELLOW, res_med.text)

        cw_high = ContextWindowInfo(used_percentage=95.0)
        res_high = segments_module.format_context_usage(cw_high)
        self.assertIsNotNone(res_high)
        assert res_high is not None
        self.assertIn(segments_module.RED, res_high.text)

        cw_none = ContextWindowInfo(used_percentage=None)
        res_none = segments_module.format_context_usage(cw_none)
        self.assertIsNotNone(res_none)
        assert res_none is not None
        self.assertIn("0%", res_none.text)
        self.assertIn(segments_module.GREEN, res_none.text)

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
        res = segments_module.format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn("main", res.text)
        self.assertIn(segments_module.ICON_CLEAN, res.text)
        self.assertIn(segments_module.ICON_REMOTE, res.text)

        base_kwargs["dirty"] = True
        info = GitInfo(**base_kwargs)
        res = segments_module.format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn(segments_module.ICON_DIRTY, res.text)

        base_kwargs["dirty"] = False
        base_kwargs["staged"] = True
        info = GitInfo(**base_kwargs)
        res = segments_module.format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn(segments_module.ICON_STAGED, res.text)

        base_kwargs["staged"] = False
        base_kwargs["untracked"] = True
        info = GitInfo(**base_kwargs)
        res = segments_module.format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn(segments_module.ICON_UNTRACKED, res.text)

        base_kwargs["untracked"] = False
        base_kwargs["ahead"] = 2
        base_kwargs["behind"] = 1
        info = GitInfo(**base_kwargs)
        res = segments_module.format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn("↑2", res.text)
        self.assertIn("↓1", res.text)

    @patch("subprocess.check_output")
    def test_get_git_info_fresh(self, mock_check_output: MagicMock) -> None:
        def side_effect(cmd: Any, **kwargs: Any) -> Any:
            cmd_list = cmd if isinstance(cmd, list) else cmd.split()
            if "is-inside-work-tree" in cmd_list:
                return b"true\n"
            if "rev-parse" in cmd_list and "HEAD" in cmd_list:
                return "feature-branch\n"
            if "ls-remote" in cmd_list:
                return "git@github.com:user/repo.git\n"
            if "status" in cmd_list:
                return " M modified_file.py\n?? untracked.py\n"
            if "rev-list" in cmd_list:
                return "1\t0\n"
            return b""

        mock_check_output.side_effect = side_effect

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
            self.assertEqual(segments_module.shorten_path(p1), "~/projects/repo")

            p2 = Path("/home/user/src/github.com/org/repo/subdir")
            self.assertEqual(segments_module.shorten_path(p2), ".../repo/subdir")

            p3 = Path("/opt/tool/src/main")
            self.assertEqual(segments_module.shorten_path(p3), ".../src/main")

            p4 = Path("/home/user")
            self.assertEqual(segments_module.shorten_path(p4), "~")


if __name__ == "__main__":
    unittest.main()
