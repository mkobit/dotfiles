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


def test_tmux_open_url_success_linux(mock_subprocess_run):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "tmux":
            if cmd[1] == "capture-pane":
                mock = MagicMock()
                mock.stdout = "Some text with https://example.com inside"
                return mock
            return MagicMock()
        if cmd[0] == "fzf":
            mock = MagicMock()
            mock.stdout = "enter\nhttps://example.com\n"
            return mock
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run
    with patch("sys.platform", "linux"), patch("os.uname") as mock_uname:
        mock_uname.return_value = MagicMock(release="5.15.0-generic")
        result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 0
    # capture-pane, fzf, xdg-open
    assert mock_subprocess_run.call_count == 3
    last_call = mock_subprocess_run.call_args_list[-1]
    assert last_call[0][0] == ["xdg-open", "https://example.com"]


def test_tmux_open_url_success_darwin(mock_subprocess_run):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "tmux":
            mock = MagicMock()
            mock.stdout = "https://apple.com"
            return mock
        if cmd[0] == "fzf":
            mock = MagicMock()
            mock.stdout = "enter\nhttps://apple.com\n"
            return mock
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run
    with patch("sys.platform", "darwin"):
        result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 0
    assert mock_subprocess_run.call_count == 3
    last_call = mock_subprocess_run.call_args_list[-1]
    assert last_call[0][0] == ["open", "https://apple.com"]


def test_tmux_open_url_success_wsl(mock_subprocess_run):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "tmux":
            mock = MagicMock()
            mock.stdout = "https://microsoft.com"
            return mock
        if cmd[0] == "fzf":
            mock = MagicMock()
            mock.stdout = "enter\nhttps://microsoft.com\n"
            return mock
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run
    with patch("sys.platform", "linux"), patch("os.uname") as mock_uname:
        mock_uname.return_value = MagicMock(release="5.15.90.1-microsoft-standard-WSL2")
        result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 0
    assert mock_subprocess_run.call_count == 3
    last_call = mock_subprocess_run.call_args_list[-1]
    assert last_call[0][0] == ["wslview", "https://microsoft.com"]


def test_tmux_open_url_capture_fail(mock_subprocess_run):
    mock_subprocess_run.side_effect = [subprocess.CalledProcessError(1, "tmux"), MagicMock()]
    result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 1
    mock_subprocess_run.assert_called_with(["tmux", "display-message", "Failed to capture pane"], check=False)


def test_tmux_open_url_no_urls(mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(stdout="No links here")
    result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 0
    mock_subprocess_run.assert_called_with(["tmux", "display-message", "No URLs found."], check=False)


def test_tmux_open_url_fzf_fail(mock_subprocess_run):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "tmux":
            mock = MagicMock()
            mock.stdout = "https://example.com"
            return mock
        if cmd[0] == "fzf":
            raise OSError("fzf failed")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run
    result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 1
    assert "Failed to execute fzf" in result.stderr
