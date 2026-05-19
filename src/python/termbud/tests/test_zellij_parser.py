import subprocess
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from termbud.main import app

runner = CliRunner()

ZELLIJ_ENV = {"ZELLIJ": "0", "ZELLIJ_PANE_ID": "5", "ZELLIJ_SESSION_NAME": "test"}
OPEN_ARGS = ["zellij", "open"]


@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock:
        yield mock


def _calls_for(mock, *tokens) -> list:
    return [c for c in mock.call_args_list if all(t in c.args[0] for t in tokens)]


def _dump_result(text: str) -> MagicMock:
    m = MagicMock()
    m.stdout = text
    return m


def _fzf_result(yank: str) -> MagicMock:
    m = MagicMock()
    m.stdout = f"display\turl\t{yank}\n"
    return m


def _side_effect(scrollback: str, yank: str):
    def _run(cmd, *args, **kwargs):
        if "dump-screen" in cmd:
            return _dump_result(scrollback)
        if cmd[0] == "fzf":
            return _fzf_result(yank)
        return MagicMock()
    return _run


def test_open_uses_pane_id_flag(mock_subprocess_run):
    mock_subprocess_run.side_effect = _side_effect("https://example.com", "https://example.com")
    runner.invoke(app, OPEN_ARGS, env=ZELLIJ_ENV)
    assert _calls_for(mock_subprocess_run, "dump-screen", "-p")


def test_open_writes_selection_back(mock_subprocess_run):
    mock_subprocess_run.side_effect = _side_effect("https://example.com", "https://example.com")
    result = runner.invoke(app, OPEN_ARGS, env=ZELLIJ_ENV)
    assert result.exit_code == 0
    assert _calls_for(mock_subprocess_run, "write-chars", "https://example.com")


def test_open_no_patterns_exits_silently(mock_subprocess_run):
    mock_subprocess_run.side_effect = _side_effect("nothing matchable here", "")
    result = runner.invoke(app, OPEN_ARGS, env=ZELLIJ_ENV)
    assert result.exit_code == 0
    assert not _calls_for(mock_subprocess_run, "write-chars")


def test_open_fzf_no_selection_no_write(mock_subprocess_run):
    def side_effect(cmd, *args, **kwargs):
        if "dump-screen" in cmd:
            return _dump_result("https://example.com")
        if cmd[0] == "fzf":
            return _dump_result("")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect
    result = runner.invoke(app, OPEN_ARGS, env=ZELLIJ_ENV)
    assert result.exit_code == 0
    assert not _calls_for(mock_subprocess_run, "write-chars")


def test_open_requires_zellij_env():
    with patch.dict("os.environ", {}, clear=True):
        result = runner.invoke(app, OPEN_ARGS)
    assert result.exit_code == 1


def test_open_no_content_exits_silently(mock_subprocess_run):
    mock_subprocess_run.side_effect = _side_effect("", "")
    result = runner.invoke(app, OPEN_ARGS, env=ZELLIJ_ENV)
    assert result.exit_code == 0
    assert not _calls_for(mock_subprocess_run, "write-chars")
