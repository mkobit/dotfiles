import asyncio
import io
import json
import os
from pathlib import Path
from typing import override
from unittest.mock import AsyncMock, Mock, patch

import pytest
from typer.testing import CliRunner

from termstatus.git_status import probe_git
from termstatus.layout import Segment, SegmentGenerationResult
from termstatus.main import cli
from termstatus.segments.git import _GIT_TIMEOUT
from termstatus.segments.workspace import format_obsidian_vault, shorten_path


@pytest.fixture(autouse=True)
def wide_terminal(monkeypatch):
    # Rendering truncates to the terminal width (render.py reads COLUMNS via
    # shutil.get_terminal_size), so narrow terminals cut off asserted text.
    monkeypatch.setenv("COLUMNS", "200")


class TestMainSmoke:
    """Smoke tests verifying the CLI entry point runs end-to-end."""

    @patch.dict("os.environ", {"XDG_CACHE_HOME": "/tmp/termstatus_test_cache"})
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
            @override
            def isatty(self):
                return False

        mock_stdin = MockStdin(payload)

        # Typer/Click might replace sys.stdin during invoke.
        # Let's write the test so we test the main python function itself or mock read().
        with patch("sys.stdin", mock_stdin), patch("termstatus.main.generate_git_segment") as mock_git:
            mock_git.return_value = [
                SegmentGenerationResult(segment=Segment(text="main"), generator="internal.git", line=1)
            ]
            runner = CliRunner()
            # runner.invoke might replace stdin with a pipe. If we want it to read from sys.stdin,
            # we should mock sys.stdin.read directly or pass input parameter.

            # Since click.testing (and Typer) will hook sys.stdin with what is passed via `input`,
            # we should pass the payload directly to `invoke`.
            result = runner.invoke(cli, ["claude", "render"], input=payload)

        assert result.exit_code == 0
        all_output = result.stdout
        assert "Claude 3" in all_output
        assert "MySession" in all_output
        assert "0.42" in all_output
        assert "/100k" in all_output

    @patch.dict("os.environ", {"XDG_CACHE_HOME": "/tmp/termstatus_test_cache"})
    def test_runs_with_empty_payload(self) -> None:
        with patch("termstatus.main.generate_git_segment") as mock_git:
            mock_git.return_value = []
            runner = CliRunner()
            result = runner.invoke(cli, ["claude", "render"], input="{}")

        assert result.exit_code == 0
        assert len(result.stdout) > 0


class TestShortenPath:
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


class TestFormatObsidianVault:
    def test_vault_detected_in_ancestor(self, tmp_path: Path) -> None:
        vault = tmp_path / "MyNotes"
        vault_config = vault / ".obsidian"
        vault_config.mkdir(parents=True)
        sub_dir = vault / "nested" / "folder"
        sub_dir.mkdir(parents=True)

        results = format_obsidian_vault(sub_dir)
        assert len(results) == 1
        assert results[0].line == 1
        assert results[0].index == 40
        assert results[0].column == 4
        assert "MyNotes" in results[0].segment.text

    def test_no_vault_returns_empty(self, tmp_path: Path) -> None:
        assert format_obsidian_vault(tmp_path) == []


runner = CliRunner()


def test_main_with_xdg_cache_home(tmp_path):
    """Goals: Verify that alternative cache directory overrides function correctly."""
    with patch.dict(os.environ, {"XDG_CACHE_HOME": str(tmp_path)}):
        result = runner.invoke(cli, ["claude", "render"], input='{"cwd": "/tmp"}')
        assert result.exit_code == 0
        assert (tmp_path / "termstatus" / "cache.json").parent.exists()


def test_main_with_internal_error(tmp_path):
    """Goals: Ensure internal pipeline failures (like Git) are captured gracefully as errors when requested."""
    # Isolate the cache: a populated user cache would mask the error with a cached git segment.
    with (
        patch.dict(os.environ, {"XDG_CACHE_HOME": str(tmp_path)}),
        patch("termstatus.main.detect_chezmoi_root", return_value=None),
        patch("termstatus.main.generate_git_segment", side_effect=Exception("Git error")),
    ):
        result = runner.invoke(cli, ["claude", "render", "--show-errors"], input='{"cwd": "/tmp"}')
        assert result.exit_code == 0
        assert "Error: internal.git" in result.stdout or "[Error: internal.git" in result.stdout


def test_main_with_invalid_stdin():
    """Goals: Verify that garbage standard input falls back to a clean default state."""
    result = runner.invoke(cli, ["claude", "render"], input="not json")
    assert result.exit_code == 0


def test_git_cancellation_under_slow_git(tmp_path):
    """The CLI uses the configured Git budget and cleans up blocked subprocesses."""
    cancelled_reads = []

    async def slow_read(*args, **kwargs):
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled_reads.append(True)
            raise
        return b""

    processes = [AsyncMock(), AsyncMock()]
    for process in processes:
        process.kill = Mock()
        process.returncode = None
        process.stdout.read.side_effect = slow_read
        process.wait.return_value = 0

    with (
        patch.dict(os.environ, {"XDG_CACHE_HOME": str(tmp_path)}),
        patch("termstatus.main.detect_chezmoi_root", return_value=None),
        patch("asyncio.create_subprocess_exec", side_effect=processes) as create_process,
        patch("termstatus.segments.git.probe_git", wraps=probe_git) as git_probe,
    ):
        result = runner.invoke(
            cli, ["claude", "render"], input=json.dumps({"workspace": {"current_dir": str(tmp_path)}})
        )

    assert result.exit_code == 0
    git_probe.assert_awaited_once_with(str(tmp_path.resolve()), _GIT_TIMEOUT)
    assert _GIT_TIMEOUT.total("milliseconds") == 300
    assert create_process.await_count == 2
    assert len(cancelled_reads) == 2
    for process in processes:
        process.kill.assert_called_once()
        process.wait.assert_awaited_once()


def test_claude_render_with_unknown_payload_fields(tmp_path):
    """Goals: Verify that unknown fields in payload sub-objects do not cause validation failure."""
    raw = json.dumps(
        {
            "model": {"id": "claude-3-7-sonnet", "display_name": "Sonnet 3.7 Custom", "extra_vendor": "anthropic"},
            "cost": {"total_cost_usd": 3.50, "total_duration_ms": 12000, "extra_metric": 99},
            "workspace": {"current_dir": "/tmp", "extra_ws": True},
        }
    )
    with patch.dict(os.environ, {"XDG_CACHE_HOME": str(tmp_path)}):
        result = runner.invoke(cli, ["claude", "render"], input=raw)
        assert result.exit_code == 0
        assert "Sonnet 3.7 Custom" in result.stdout
        assert "$3.50" in result.stdout
