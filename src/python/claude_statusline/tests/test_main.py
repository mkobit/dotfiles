import io
import json
import unittest
from unittest.mock import MagicMock, patch

import claude_statusline.main as main_module


class TestMainSmoke(unittest.TestCase):
    """Smoke tests verifying the CLI entry point runs end-to-end."""

    @patch("builtins.print")
    @patch("sys.stdin", new_callable=io.StringIO)
    @patch.dict("os.environ", {"XDG_CACHE_HOME": "/tmp/claude_statusline_test_cache"})
    def test_runs_with_minimal_payload(
        self, mock_stdin: MagicMock, mock_print: MagicMock
    ) -> None:
        mock_stdin.write(json.dumps({
            "model": {"display_name": "Claude 3"},
            "workspace": {"current_dir": "/tmp/test"},
            "context_window": {"used_percentage": 50.0, "context_window_size": 100000},
            "session_name": "MySession",
            "cost": {"total_cost_usd": 0.42},
        }))
        mock_stdin.seek(0)

        with patch("claude_statusline.main.generate_git_segment") as mock_git:
            from claude_statusline.models import (  # noqa: PLC0415
                Segment,
                SegmentGenerationResult,
            )

            mock_git.return_value = [
                SegmentGenerationResult(
                    segment=Segment(text="main"), generator="internal.git", line=1
                )
            ]
            main_module.main(args=[], standalone_mode=False)

        self.assertGreater(mock_print.call_count, 0)
        all_output = "\n".join(call[0][0] for call in mock_print.call_args_list)
        self.assertIn("Claude 3", all_output)
        self.assertIn("MySession", all_output)
        self.assertIn("0.42", all_output)
        self.assertIn("/100k", all_output)

    @patch("builtins.print")
    @patch("sys.stdin", new_callable=io.StringIO)
    @patch.dict("os.environ", {"XDG_CACHE_HOME": "/tmp/claude_statusline_test_cache"})
    def test_runs_with_empty_payload(
        self, mock_stdin: MagicMock, mock_print: MagicMock
    ) -> None:
        mock_stdin.write("{}")
        mock_stdin.seek(0)

        with patch("claude_statusline.main.generate_git_segment") as mock_git:
            mock_git.return_value = []
            main_module.main(args=[], standalone_mode=False)

        self.assertGreater(mock_print.call_count, 0)


if __name__ == "__main__":
    unittest.main()
