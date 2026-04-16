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


def test_zellij_open_url_success(mock_subprocess_run, mock_os_execvpe):
    def side_effect_run(cmd, *args, **kwargs):
        if cmd[0] == "zellij" and cmd[1] == "action" and cmd[2] == "dump-screen":
            # Write some content to the temp file
            file_path = cmd[3]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Here is a url: https://example.com")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect_run

    result = runner.invoke(app, ["zellij", "open-url"])

    assert result.exit_code == 0
    mock_subprocess_run.assert_called_once()
    mock_os_execvpe.assert_called_once()


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
