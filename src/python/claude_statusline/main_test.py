import unittest
from unittest.mock import patch, MagicMock
import sys
import json
import io
from pathlib import Path
from typing import Any, Dict

# Import the module under test
import src.python.claude_statusline.main as statusline


class TestStatusLine(unittest.TestCase):
    def test_format_context_usage(self) -> None:
        # Test low usage (Green)
        self.assertIn(statusline.GREEN, statusline.format_context_usage(10))
        # Test medium usage (Yellow)
        self.assertIn(statusline.YELLOW, statusline.format_context_usage(55))
        # Test high usage (Red)
        self.assertIn(statusline.RED, statusline.format_context_usage(95))
        # Test None (Unknown)
        self.assertIn(statusline.DIM, statusline.format_context_usage(None))

    def test_format_git_full(self) -> None:
        base_kwargs: Dict[str, Any] = {
            "branch": "main",
            "remote": "https://github.com/example/repo",
            "dirty": False,
            "staged": False,
            "untracked": False,
            "ahead": 0,
            "behind": 0,
            "is_repo": True,
        }

        # Clean
        info = statusline.GitInfo(
            branch=str(base_kwargs["branch"]),
            remote=str(base_kwargs["remote"]),
            dirty=bool(base_kwargs["dirty"]),
            staged=bool(base_kwargs["staged"]),
            untracked=bool(base_kwargs["untracked"]),
            ahead=int(base_kwargs["ahead"]),
            behind=int(base_kwargs["behind"]),
            is_repo=bool(base_kwargs["is_repo"]),
        )
        output = statusline.format_git_full(info)
        self.assertIn("main", output)
        self.assertIn(statusline.ICON_CLEAN, output)
        self.assertIn(statusline.ICON_REMOTE, output)

        # Dirty
        info = statusline.GitInfo(
            branch=str(base_kwargs["branch"]),
            remote=str(base_kwargs["remote"]),
            dirty=True,
            staged=bool(base_kwargs["staged"]),
            untracked=bool(base_kwargs["untracked"]),
            ahead=int(base_kwargs["ahead"]),
            behind=int(base_kwargs["behind"]),
            is_repo=bool(base_kwargs["is_repo"]),
        )
        output = statusline.format_git_full(info)
        self.assertIn(statusline.ICON_DIRTY, output)

        # Staged
        info = statusline.GitInfo(
            branch=str(base_kwargs["branch"]),
            remote=str(base_kwargs["remote"]),
            dirty=bool(base_kwargs["dirty"]),
            staged=True,
            untracked=bool(base_kwargs["untracked"]),
            ahead=int(base_kwargs["ahead"]),
            behind=int(base_kwargs["behind"]),
            is_repo=bool(base_kwargs["is_repo"]),
        )
        output = statusline.format_git_full(info)
        self.assertIn(statusline.ICON_STAGED, output)

        # Untracked
        info = statusline.GitInfo(
            branch=str(base_kwargs["branch"]),
            remote=str(base_kwargs["remote"]),
            dirty=bool(base_kwargs["dirty"]),
            staged=bool(base_kwargs["staged"]),
            untracked=True,
            ahead=int(base_kwargs["ahead"]),
            behind=int(base_kwargs["behind"]),
            is_repo=bool(base_kwargs["is_repo"]),
        )
        output = statusline.format_git_full(info)
        self.assertIn(statusline.ICON_UNTRACKED, output)

        # Ahead/Behind
        info = statusline.GitInfo(
            branch=str(base_kwargs["branch"]),
            remote=str(base_kwargs["remote"]),
            dirty=bool(base_kwargs["dirty"]),
            staged=bool(base_kwargs["staged"]),
            untracked=bool(base_kwargs["untracked"]),
            ahead=2,
            behind=1,
            is_repo=bool(base_kwargs["is_repo"]),
        )
        output = statusline.format_git_full(info)
        self.assertIn("↑2", output)
        self.assertIn("↓1", output)

    @patch("subprocess.check_output")
    def test_get_git_info_fresh(self, mock_check_output: MagicMock) -> None:
        # Mock git commands
        def side_effect(cmd: Any, **kwargs: Any) -> Any:
            cmd_list = cmd if isinstance(cmd, list) else cmd.split()
            if "is-inside-work-tree" in cmd_list:
                return b"true"
            if "rev-parse" in cmd_list and "HEAD" in cmd_list:
                return "feature-branch\n"
            if "ls-remote" in cmd_list:
                return "git@github.com:user/repo.git\n"
            if "status" in cmd_list:
                return " M modified_file.py\n?? untracked.py\n"
            if "rev-list" in cmd_list:
                return "1\t0\n"
            return ""

        mock_check_output.side_effect = side_effect

        # Mock Path.exists to return False (cache miss)
        with patch.object(Path, "exists", return_value=False):
            info = statusline.get_git_info(Path("/tmp/repo"))

        self.assertIsNotNone(info)
        assert info is not None
        self.assertEqual(info.branch, "feature-branch")
        self.assertEqual(info.remote, "https://github.com/user/repo")
        self.assertTrue(info.dirty)
        self.assertEqual(info.ahead, 1)
        self.assertEqual(info.behind, 0)

    @patch("builtins.print")
    @patch("sys.stdin", new_callable=io.StringIO)
    def test_main(self, mock_stdin: MagicMock, mock_print: MagicMock) -> None:
        # Mock stdin
        input_data = {
            "model": {"display_name": "Claude 3"},
            "workspace": {"current_dir": "/tmp/test"},
            "context_window": {"used_percentage": 50},
            "session_name": "MySession",
            "cost": {"total_cost_usd": 0.42},
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with patch.object(statusline, "get_git_info") as mock_get_git_info:
            # Mock git info
            mock_get_git_info.return_value = statusline.GitInfo(
                branch="main",
                dirty=False,
                staged=False,
                untracked=False,
                ahead=0,
                behind=0,
                remote=None,
                is_repo=True,
            )

            statusline.main()

            # Verify output
            # Expect 2 print calls
            self.assertEqual(mock_print.call_count, 2)

            # Check first line (Model, Context, Session, Cost)
            line1 = mock_print.call_args_list[0][0][0]
            self.assertIn("Claude 3", line1)
            self.assertIn("50%", line1)
            self.assertIn("#MySession", line1)
            self.assertIn("$0.42", line1)

            # Check second line (Git)
            line2 = mock_print.call_args_list[1][0][0]
            self.assertIn("main", line2)

    def test_shorten_path(self) -> None:
        home = Path("/home/user")

        with patch.object(Path, "home", return_value=home):
            # Case 1: Path inside home, shallow
            p1 = Path("/home/user/projects/repo")
            self.assertEqual(statusline.shorten_path(p1), "~/projects/repo")

            # Case 2: Path inside home, deep
            p2 = Path("/home/user/src/github.com/org/repo/subdir")
            self.assertEqual(statusline.shorten_path(p2), ".../repo/subdir")

            # Case 3: Path outside home
            p3 = Path("/opt/tool/src/main")
            self.assertEqual(statusline.shorten_path(p3), ".../src/main")

            # Case 4: Home itself
            p4 = Path("/home/user")
            self.assertEqual(statusline.shorten_path(p4), "~")


if __name__ == "__main__":
    unittest.main()
