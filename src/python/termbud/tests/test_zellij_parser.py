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


def test_zellij_open_url_success_linux(mock_subprocess_run):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Here is a url: https://example.com")
            return MagicMock()
        if cmd[0] == "fzf":
            mock = MagicMock()
            mock.stdout = "enter\nhttps://example.com\n"
            return mock
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    with patch("sys.platform", "linux"), patch("os.uname") as mock_uname:
        mock_uname.return_value = MagicMock(release="5.15.0-generic")
        result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 0
    # One for dump-screen, one for fzf, one for xdg-open
    assert mock_subprocess_run.call_count == 3
    # Check that xdg-open was called with the URL
    last_call = mock_subprocess_run.call_args_list[-1]
    assert last_call[0][0] == ["xdg-open", "https://example.com"]


def test_zellij_open_url_success_darwin(mock_subprocess_run):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("https://apple.com")
            return MagicMock()
        if cmd[0] == "fzf":
            mock = MagicMock()
            mock.stdout = "enter\nhttps://apple.com\n"
            return mock
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    with patch("sys.platform", "darwin"):
        result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 0
    assert mock_subprocess_run.call_count == 3
    last_call = mock_subprocess_run.call_args_list[-1]
    assert last_call[0][0] == ["open", "https://apple.com"]


def test_zellij_open_url_success_wsl(mock_subprocess_run):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("https://microsoft.com")
            return MagicMock()
        if cmd[0] == "fzf":
            mock = MagicMock()
            mock.stdout = "enter\nhttps://microsoft.com\n"
            return mock
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    with patch("sys.platform", "linux"), patch("os.uname") as mock_uname:
        mock_uname.return_value = MagicMock(release="5.15.90.1-microsoft-standard-WSL2")
        result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 0
    assert mock_subprocess_run.call_count == 3
    last_call = mock_subprocess_run.call_args_list[-1]
    assert last_call[0][0] == ["wslview", "https://microsoft.com"]


def test_zellij_open_url_no_urls(mock_subprocess_run):
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
    # Only zellij call
    assert mock_subprocess_run.call_count == 1


def test_zellij_open_url_dump_fail(mock_subprocess_run):
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "zellij")
    result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 1
    assert "Failed to capture Zellij pane" in result.stderr


def test_zellij_open_url_not_found(mock_subprocess_run):
    mock_subprocess_run.side_effect = FileNotFoundError("zellij")
    result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 1
    assert "Zellij command not found. Are you running inside Zellij?" in result.stderr


def test_zellij_open_url_fzf_fail(mock_subprocess_run):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("https://example.com")
            return MagicMock()
        if cmd[0] == "fzf":
            raise OSError("fzf failed")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 1
    assert "Failed to execute fzf" in result.stderr


def test_zellij_open_url_copy(mock_subprocess_run):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("https://example.com")
            return MagicMock()
        if cmd[0] == "fzf":
            mock = MagicMock()
            mock.stdout = "ctrl-c\nhttps://example.com\n"
            return mock
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    with patch("sys.platform", "linux"), patch("os.uname") as mock_uname:
        mock_uname.return_value = MagicMock(release="5.15.0-generic")
        result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 0
    assert mock_subprocess_run.call_count == 3
    last_call = mock_subprocess_run.call_args_list[-1]
    # xclip -selection clipboard
    assert last_call[0][0] == ["xclip", "-selection", "clipboard"]
    assert last_call[1]["input"] == "https://example.com"


def test_zellij_open_url_injection_prevention(mock_subprocess_run):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("https://example.com/$(id)")
            return MagicMock()
        if cmd[0] == "fzf":
            mock = MagicMock()
            mock.stdout = "enter\nhttps://example.com/$(id)\n"
            return mock
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    with patch("sys.platform", "linux"), patch("os.uname") as mock_uname:
        mock_uname.return_value = MagicMock(release="5.15.0-generic")
        result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 0
    last_call = mock_subprocess_run.call_args_list[-1]
    # It should be a single argument, not split by shell
    assert last_call[0][0] == ["xdg-open", "https://example.com/$(id)"]
    assert last_call[1].get("shell", False) is False
