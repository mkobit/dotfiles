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


@pytest.mark.parametrize(
    ("platform", "uname_release", "url", "expected_opener"),
    [
        ("linux", "5.15.0-generic", "https://example.com", "xdg-open"),
        ("darwin", None, "https://apple.com", "open"),
        ("linux", "5.15.90.1-microsoft-standard-WSL2", "https://microsoft.com", "wslview"),
    ],
)
def test_tmux_open_url_success(mock_subprocess_run, platform, uname_release, url, expected_opener):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "tmux":
            mock = MagicMock()
            mock.stdout = f"Some text with {url} inside"
            return mock
        if cmd[0] == "fzf":
            mock = MagicMock()
            mock.stdout = f"enter\n{url}\n"
            return mock
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run
    with patch("sys.platform", platform):
        if uname_release is not None:
            with patch("os.uname") as mock_uname:
                mock_uname.return_value = MagicMock(release=uname_release)
                result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])
        else:
            result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 0
    # capture-pane, fzf, opener
    assert mock_subprocess_run.call_count == 3
    last_call = mock_subprocess_run.call_args_list[-1]
    assert last_call[0][0] == [expected_opener, url]


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


def test_tmux_open_url_ctrl_c_copies_to_clipboard(mock_subprocess_run):
    url = "https://example.com/item"

    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "tmux":
            mock = MagicMock()
            mock.stdout = f"Log with {url}"
            return mock
        if cmd[0] == "fzf":
            mock = MagicMock()
            mock.stdout = f"ctrl-c\n{url}\n"
            return mock
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run
    with patch("sys.platform", "linux"), patch("os.uname") as mock_uname:
        mock_uname.return_value = MagicMock(release="5.15.0-generic")
        result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 0
    assert mock_subprocess_run.call_count == 3
    last_call = mock_subprocess_run.call_args_list[-1]
    assert last_call[0][0] == ["xclip", "-selection", "clipboard"]
    assert last_call[1]["input"] == url


@pytest.mark.parametrize("fzf_stdout", ["", "only_one_line\n"])
def test_tmux_open_url_fzf_abort_or_empty(mock_subprocess_run, fzf_stdout):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "tmux":
            mock = MagicMock()
            mock.stdout = "https://example.com"
            return mock
        if cmd[0] == "fzf":
            mock = MagicMock()
            mock.stdout = fzf_stdout
            return mock
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run
    result = runner.invoke(app, ["tmux", "open-url", "--pane-id", "%1"])

    assert result.exit_code == 0
    # Only capture-pane and fzf are invoked
    assert mock_subprocess_run.call_count == 2
