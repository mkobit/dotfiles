import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from claude_statusline.main import cli
from claude_statusline.models import Segment, SegmentGenerationResult
from claude_statusline.segments.workspace import shorten_path


class TestMainSmoke(unittest.TestCase):
    """Smoke tests verifying the CLI entry point runs end-to-end."""

    @patch.dict("os.environ", {"XDG_CACHE_HOME": "/tmp/claude_statusline_test_cache"})
    def test_runs_with_minimal_payload(self) -> None:
        payload = json.dumps(
            {
                "model": {"display_name": "Claude 3"},
                "workspace": {"current_dir": "/tmp/test"},
                "context_window": {
                    "used_percentage": 50.0,
                    "context_window_size": 100000,
                },
                "session_name": "MySession",
                "cost": {"total_cost_usd": 0.42},
            }
        )

        class MockStdin(io.StringIO):
            def isatty(self):
                return False

        mock_stdin = MockStdin(payload)

        # Typer/Click might replace sys.stdin during invoke.
        # Let's write the test so we test the main python function itself or mock read().
        with patch("sys.stdin", mock_stdin), patch("claude_statusline.main.generate_git_segment") as mock_git:
            mock_git.return_value = [
                SegmentGenerationResult(segment=Segment(text="main"), generator="internal.git", line=1)
            ]
            runner = CliRunner()
            # runner.invoke might replace stdin with a pipe. If we want it to read from sys.stdin,
            # we should mock sys.stdin.read directly or pass input parameter.

            # Since click.testing (and Typer) will hook sys.stdin with what is passed via `input`,
            # we should pass the payload directly to `invoke`.
            result = runner.invoke(cli, [], input=payload)

        self.assertEqual(result.exit_code, 0)
        all_output = result.stdout
        self.assertIn("Claude 3", all_output)
        self.assertIn("MySession", all_output)
        self.assertIn("0.42", all_output)
        self.assertIn("/100k", all_output)

    @patch.dict("os.environ", {"XDG_CACHE_HOME": "/tmp/claude_statusline_test_cache"})
    def test_runs_with_empty_payload(self) -> None:
        with patch("claude_statusline.main.generate_git_segment") as mock_git:
            mock_git.return_value = []
            runner = CliRunner()
            result = runner.invoke(cli, [], input="{}")

        self.assertEqual(result.exit_code, 0)
        self.assertGreater(len(result.stdout), 0)


class TestShortenPath(unittest.TestCase):
    def test_home_relative_short(self) -> None:
        home = Path("/home/user")
        with patch.object(Path, "home", return_value=home):
            assert shorten_path(home / "projects" / "repo") == "~/projects/repo"

    def test_home_relative_long(self) -> None:
        home = Path("/home/user")
        with patch.object(Path, "home", return_value=home):
            p = home / "src" / "github.com" / "org" / "repo" / "subdir"
            assert shorten_path(p) == ".../repo/subdir"

    def test_absolute_long(self) -> None:
        home = Path("/home/user")
        with patch.object(Path, "home", return_value=home):
            assert shorten_path(Path("/opt/tool/src/main")) == ".../src/main"

    def test_home_itself(self) -> None:
        home = Path("/home/user")
        with patch.object(Path, "home", return_value=home):
            assert shorten_path(home) == "~"


if __name__ == "__main__":
    unittest.main()
