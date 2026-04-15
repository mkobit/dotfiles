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
        self.assertIn(GREEN, res_low.segment.text)

        cw_med = ContextWindowInfo(used_percentage=55.0)
        res_med = format_context_usage(cw_med)
        self.assertIsNotNone(res_med)
        assert res_med is not None
        self.assertIn(YELLOW, res_med.segment.text)

        cw_high = ContextWindowInfo(used_percentage=95.0)
        res_high = format_context_usage(cw_high)
        self.assertIsNotNone(res_high)
        assert res_high is not None
        self.assertIn(RED, res_high.segment.text)

        cw_none = ContextWindowInfo(used_percentage=None)
        res_none = format_context_usage(cw_none)
        self.assertIsNotNone(res_none)
        assert res_none is not None
        self.assertIn("  0%", res_none.segment.text)
        self.assertIn(GREEN, res_none.segment.text)

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
        self.assertIn("main", res.segment.text)
        self.assertIn(get_icon("clean"), res.segment.text)
        self.assertIn(get_icon("remote"), res.segment.text)

        base_kwargs["dirty"] = True
        info = GitInfo(**base_kwargs)
        res = format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn(get_icon("dirty"), res.segment.text)

        base_kwargs["dirty"] = False
        base_kwargs["staged"] = True
        info = GitInfo(**base_kwargs)
        res = format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn(get_icon("staged"), res.segment.text)

        base_kwargs["staged"] = False
        base_kwargs["untracked"] = True
        info = GitInfo(**base_kwargs)
        res = format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn(get_icon("untracked"), res.segment.text)

        base_kwargs["untracked"] = False
        base_kwargs["ahead"] = 2
        base_kwargs["behind"] = 1
        info = GitInfo(**base_kwargs)
        res = format_git_full(info)
        self.assertIsNotNone(res)
        assert res is not None
        self.assertIn("↑2", res.segment.text)
        self.assertIn("↓1", res.segment.text)

    @patch("asyncio.create_subprocess_exec")
    def test_get_git_info_fresh(self, mock_run: MagicMock) -> None:
        async def side_effect(*cmd: Any, **kwargs: Any) -> Any:
            cmd_list = cmd
            stdout = ""
            if "rev-parse" in cmd_list and "HEAD" in cmd_list:
                stdout = "feature-branch\n"
            elif "ls-remote" in cmd_list:
                stdout = "git@github.com:user/repo.git\n"
            elif "status" in cmd_list:
                stdout = " M modified_file.py\n?? untracked.py\n"
            elif "rev-list" in cmd_list:
                stdout = "1\t0\n"
            elif "rev-parse" in cmd_list and "--is-inside-work-tree" in cmd_list:
                stdout = "true\n"

            async def mock_communicate():
                return stdout.encode(), b""

            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = mock_communicate
            return mock_proc

        mock_run.side_effect = side_effect

        with patch.object(Path, "exists", return_value=False):
            with patch(
                "claude_statusline.segments.git._check_is_repo", return_value=True
            ):
                import asyncio

                from claude_statusline.segments.git import generate_git_segment

                info = asyncio.run(generate_git_segment(Path("/tmp/repo"), False))

        self.assertTrue(len(info) > 0)
        assert info is not None
        self.assertTrue("feature-branch" in info[0].segment.text)
        self.assertTrue("https://github.com/user/repo" in info[0].segment.text)

        self.assertTrue("1" in info[0].segment.text)

    @patch("builtins.print")
    @patch("sys.stdin", new_callable=io.StringIO)
    @patch.dict("os.environ", {"XDG_CACHE_HOME": "/tmp/claude_statusline_test_cache"})
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

        with patch("claude_statusline.main.generate_git_segment") as mock_get_git_info:
            from claude_statusline.models import Segment, SegmentGenerationResult

            mock_get_git_info.return_value = [
                SegmentGenerationResult(
                    segment=Segment(text="main"), generator="internal.git", line=2
                )
            ]

            with patch("shutil.get_terminal_size") as mock_term:
                import os

                mock_term.return_value = os.terminal_size((80, 24))
                main_module.main(args=[], standalone_mode=False)

            self.assertEqual(mock_print.call_count, 3)

            line1 = mock_print.call_args_list[0][0][0]
            self.assertIn("Claude 3", line1)

            self.assertIn("MySession", line1)

            line3 = mock_print.call_args_list[2][0][0]
            self.assertIn("main", line3)
            self.assertIn("0.42", line3)
            self.assertIn("50%", line3)

    @patch("builtins.print")
    @patch("sys.stdin", new_callable=io.StringIO)
    @patch.dict("os.environ", {"XDG_CACHE_HOME": "/tmp/claude_statusline_test_cache"})
    def test_main_full_payload(
        self, mock_stdin: MagicMock, mock_print: MagicMock
    ) -> None:
        input_data = {
            "cwd": "/current/working/directory",
            "session_id": "abc12345",
            "session_name": "my-session",
            "transcript_path": "/path/to/transcript.jsonl",
            "model": {"id": "claude-opus-4-6", "display_name": "Opus"},
            "workspace": {
                "current_dir": "/current/working/directory",
                "project_dir": "/original/project/directory",
                "added_dirs": [],
                "git_worktree": "feature-xyz",
            },
            "version": "2.1.90",
            "output_style": {"name": "default"},
            "cost": {
                "total_cost_usd": 0.01234,
                "total_duration_ms": 45000,
                "total_api_duration_ms": 2300,
                "total_lines_added": 156,
                "total_lines_removed": 23,
            },
            "context_window": {
                "total_input_tokens": 15234,
                "total_output_tokens": 4521,
                "context_window_size": 200000,
                "used_percentage": 8,
                "remaining_percentage": 92,
                "current_usage": {
                    "input_tokens": 8500,
                    "output_tokens": 1200,
                    "cache_creation_input_tokens": 5000,
                    "cache_read_input_tokens": 2000,
                },
            },
            "exceeds_200k_tokens": False,
            "rate_limits": {
                "five_hour": {"used_percentage": 23.5, "resets_at": 1738425600},
                "seven_day": {"used_percentage": 41.2, "resets_at": 1738857600},
            },
            "vim": {"mode": "NORMAL"},
            "agent": {"name": "security-reviewer"},
            "worktree": {
                "name": "my-feature",
                "path": "/path/to/.claude/worktrees/my-feature",
                "branch": "worktree-my-feature",
                "original_cwd": "/path/to/project",
                "original_branch": "main",
            },
        }
        mock_stdin.write(json.dumps(input_data))
        mock_stdin.seek(0)

        with patch("claude_statusline.main.generate_git_segment") as mock_get_git_info:
            from claude_statusline.models import Segment, SegmentGenerationResult

            mock_get_git_info.return_value = [
                SegmentGenerationResult(
                    segment=Segment(text="feature-branch"),
                    generator="internal.git",
                    line=2,
                )
            ]

            with patch("shutil.get_terminal_size") as mock_term:
                import os

                mock_term.return_value = os.terminal_size((80, 24))
                main_module.main(args=[], standalone_mode=False)

            self.assertEqual(mock_print.call_count, 3)

            line1 = mock_print.call_args_list[0][0][0]
            self.assertIn("Opus", line1)
            self.assertIn("security-reviewer", line1)

            self.assertIn("my-session", line1)
            self.assertIn("[default]", line1)

            line3 = mock_print.call_args_list[2][0][0]
            self.assertIn("feature-branch", line3)
            self.assertIn("0.01", line3)
            self.assertIn("  8%", line3)
            self.assertIn("+156", line3)
            self.assertIn("-23", line3)

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
