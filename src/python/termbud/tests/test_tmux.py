import subprocess
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from termbud.main import app

runner = CliRunner()


@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock:
        yield mock


@pytest.fixture
def mock_os_execvpe():
    with patch("os.execvpe") as mock:
        yield mock


def test_tmux_open_url_success_linux(mock_subprocess_run, mock_os_execvpe):
    mock_subprocess_run.return_value = MagicMock(stdout="Some text with https://example.com inside")
    with patch("sys.platform", "linux"), patch("os.uname") as mock_uname:
        mock_uname.return_value = MagicMock(release="5.15.0-generic")
        result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 0
    mock_subprocess_run.assert_any_call(
        ["tmux", "capture-pane", "-J", "-S", "-", "-t", "%1", "-p"],
        capture_output=True,
        text=True,
        check=True,
    )
    mock_os_execvpe.assert_called_once()
    args = mock_os_execvpe.call_args[0][1]
    assert any("xdg-open" in str(arg) for arg in args)


def test_tmux_open_url_success_darwin(mock_subprocess_run, mock_os_execvpe):
    mock_subprocess_run.return_value = MagicMock(stdout="https://apple.com")
    with patch("sys.platform", "darwin"):
        result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 0
    mock_os_execvpe.assert_called_once()
    args = mock_os_execvpe.call_args[0][1]
    assert any("open " in str(arg) or arg == "open" for arg in args)


def test_tmux_open_url_success_wsl(mock_subprocess_run, mock_os_execvpe):
    mock_subprocess_run.return_value = MagicMock(stdout="https://microsoft.com")
    with patch("sys.platform", "linux"), patch("os.uname") as mock_uname:
        mock_uname.return_value = MagicMock(release="5.15.90.1-microsoft-standard-WSL2")
        result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 0
    mock_os_execvpe.assert_called_once()
    args = mock_os_execvpe.call_args[0][1]
    assert any("wslview" in str(arg) for arg in args)


def test_tmux_open_url_capture_fail(mock_subprocess_run, mock_os_execvpe):
    mock_subprocess_run.side_effect = [subprocess.CalledProcessError(1, "tmux"), MagicMock()]
    result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 1
    mock_subprocess_run.assert_called_with(["tmux", "display-message", "Failed to capture pane"], check=False)
    mock_os_execvpe.assert_not_called()


def test_tmux_open_url_no_urls(mock_subprocess_run, mock_os_execvpe):
    mock_subprocess_run.return_value = MagicMock(stdout="No links here")
    result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 0
    mock_subprocess_run.assert_called_with(["tmux", "display-message", "No URLs found."], check=False)
    mock_os_execvpe.assert_not_called()


def test_tmux_open_url_fzf_fail(mock_subprocess_run, mock_os_execvpe):
    mock_subprocess_run.return_value = MagicMock(stdout="https://example.com")
    mock_os_execvpe.side_effect = OSError("fzf failed")
    result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 1
    assert "Failed to execute fzf" in result.stderr
