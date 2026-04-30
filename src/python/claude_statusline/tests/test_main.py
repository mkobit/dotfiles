import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from claude_statusline.layout import Segment, SegmentGenerationResult
from claude_statusline.main import cli, run_external_generator
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


runner = CliRunner()


def test_main_with_external_generator_timeout():
    """Goals: Verify that a timeout in the external generator gracefully terminates and returns empty."""
    with patch("claude_statusline.main.asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.kill = Mock()
        mock_proc.communicate.side_effect = TimeoutError()
        mock_exec.return_value = mock_proc

        result = runner.invoke(cli, ["--generator", "sleep 10"])
        assert result.exit_code == 0


def test_main_show_errors_external():
    """Goals: Ensure that an explicit error flag correctly displays external generator failures."""
    with patch("claude_statusline.main.asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate.return_value = (b"", b"error")
        mock_exec.return_value = mock_proc

        result = runner.invoke(cli, ["--generator", "failing_cmd", "--show-errors"])
        assert result.exit_code == 0
        assert "Error: external:failing_cmd" in result.stdout


def test_main_with_stdin_and_external_success():
    """Goals: Validate that valid JSON via stdin is successfully processed and integrated."""
    with patch("claude_statusline.main.asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        segment_json = json.dumps([{"line": 1, "index": 0, "segment": {"text": "external_text"}}])
        mock_proc.communicate.return_value = (segment_json.encode(), b"")
        mock_exec.return_value = mock_proc

        result = runner.invoke(cli, ["--generator", "good_cmd"], input='{"cwd": "/tmp"}')
        assert result.exit_code == 0
        assert "external_text" in result.stdout


@pytest.mark.asyncio
async def test_run_external_generator_validation_error():
    """Goals: Ensure malformed segment formats from external generators are safely ignored."""
    with patch("claude_statusline.main.asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        # Invalid JSON for segment
        mock_proc.communicate.return_value = (b'{"invalid": "data"}', b"")
        mock_exec.return_value = mock_proc

        res = await run_external_generator("cmd", "{}")
        assert res == []


@pytest.mark.asyncio
async def test_run_external_generator_json_parse_error():
    """Goals: Validate that fundamentally invalid JSON from an external generator is safely caught."""
    with patch("claude_statusline.main.asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        # Malformed JSON
        mock_proc.communicate.return_value = (b"not json", b"")
        mock_exec.return_value = mock_proc

        res = await run_external_generator("cmd", "{}")
        assert res == []


def test_main_with_xdg_cache_home(tmp_path):
    """Goals: Verify that alternative cache directory overrides function correctly."""
    with patch.dict(os.environ, {"XDG_CACHE_HOME": str(tmp_path)}):
        result = runner.invoke(cli, [], input='{"cwd": "/tmp"}')
        assert result.exit_code == 0
        assert (tmp_path / "claude_statusline" / "cache.json").parent.exists()


def test_main_with_internal_error():
    """Goals: Ensure internal pipeline failures (like Git) are captured gracefully as errors when requested."""
    # Force an error in git generation
    with patch("claude_statusline.main.generate_git_segment", side_effect=Exception("Git error")):
        result = runner.invoke(cli, ["--show-errors"], input='{"cwd": "/tmp"}')
        assert result.exit_code == 0
        assert "Error: internal.git" in result.stdout or "[Error: internal.git" in result.stdout


def test_main_with_invalid_stdin():
    """Goals: Verify that garbage standard input falls back to a clean default state."""
    result = runner.invoke(cli, [], input="not json")
    assert result.exit_code == 0


if __name__ == "__main__":
    unittest.main()
