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


def test_zellij_open_url_success_linux(mock_subprocess_run, mock_os_execvpe):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Here is a url: https://example.com")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    with patch("sys.platform", "linux"), patch("os.uname") as mock_uname:
        mock_uname.return_value = MagicMock(release="5.15.0-generic")
        result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 0
    mock_subprocess_run.assert_called_once()
    mock_os_execvpe.assert_called_once()
    args = mock_os_execvpe.call_args[0][1]
    assert any("xdg-open" in str(arg) for arg in args)


def test_zellij_open_url_success_darwin(mock_subprocess_run, mock_os_execvpe):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("https://apple.com")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    with patch("sys.platform", "darwin"):
        result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 0
    mock_os_execvpe.assert_called_once()
    args = mock_os_execvpe.call_args[0][1]
    assert any("open " in str(arg) or arg == "open" for arg in args)


def test_zellij_open_url_success_wsl(mock_subprocess_run, mock_os_execvpe):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("https://microsoft.com")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    with patch("sys.platform", "linux"), patch("os.uname") as mock_uname:
        mock_uname.return_value = MagicMock(release="5.15.90.1-microsoft-standard-WSL2")
        result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 0
    mock_os_execvpe.assert_called_once()
    args = mock_os_execvpe.call_args[0][1]
    assert any("wslview" in str(arg) for arg in args)


def test_zellij_open_url_no_urls(mock_subprocess_run, mock_os_execvpe):
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
    mock_os_execvpe.assert_not_called()


def test_zellij_open_url_dump_fail(mock_subprocess_run, mock_os_execvpe):
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "zellij")
    result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 1
    assert "Failed to capture Zellij pane" in result.stderr
    mock_os_execvpe.assert_not_called()


def test_zellij_open_url_not_found(mock_subprocess_run, mock_os_execvpe):
    mock_subprocess_run.side_effect = FileNotFoundError("zellij")
    result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 1
    assert "Zellij command not found. Are you running inside Zellij?" in result.stderr
    mock_os_execvpe.assert_not_called()


def test_zellij_open_url_fzf_fail(mock_subprocess_run, mock_os_execvpe):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("https://example.com")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run
    mock_os_execvpe.side_effect = OSError("fzf failed")

    result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 1
    assert "Failed to execute fzf" in result.stderr
