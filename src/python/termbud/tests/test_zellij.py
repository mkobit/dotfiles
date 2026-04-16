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
def mock_subprocess_popen():
    with patch("subprocess.Popen") as mock:
        yield mock


@pytest.fixture
def mock_os_execvp():
    with patch("os.execvp") as mock:
        yield mock


def test_zellij_open_url_success(
    mock_subprocess_run, mock_subprocess_popen, mock_os_execvp
):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            # Write some content to the temp file
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Here is a url: https://example.com")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    mock_popen_obj = MagicMock()
    mock_popen_obj.communicate.return_value = ("https://example.com", "")
    mock_subprocess_popen.return_value = mock_popen_obj

    result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 0
    mock_subprocess_run.assert_called_once()
    mock_subprocess_popen.assert_called_once()
    assert mock_os_execvp.call_count == 1

    args = mock_os_execvp.call_args[0]
    assert args[1] == [args[0], "https://example.com"]


def test_zellij_open_url_no_urls(
    mock_subprocess_run, mock_subprocess_popen, mock_os_execvp
):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("No urls here.")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 0
    assert "No URLs found." in result.stderr
    mock_subprocess_popen.assert_not_called()
    mock_os_execvp.assert_not_called()


def test_zellij_open_url_fzf_cancelled(
    mock_subprocess_run, mock_subprocess_popen, mock_os_execvp
):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("https://example.com")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    mock_popen_obj = MagicMock()
    mock_popen_obj.communicate.return_value = ("", "")
    mock_subprocess_popen.return_value = mock_popen_obj

    result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 0
    mock_subprocess_popen.assert_called_once()
    mock_os_execvp.assert_not_called()
