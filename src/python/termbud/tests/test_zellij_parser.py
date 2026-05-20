import subprocess
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from termbud.main import app

runner = CliRunner()

ZELLIJ_ENV = {"ZELLIJ": "0", "ZELLIJ_PANE_ID": "5", "ZELLIJ_SESSION_NAME": "test"}
WORKER_ENV = {**ZELLIJ_ENV, "ZELLIJ_PANE_ID": "6"}
CMD = ["zellij", "history-search"]
WORKER_CMD = [*CMD, "--source-pane-id", "5"]


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


# --- launcher mode ---

def test_launcher_spawns_floating_pane(mock_subprocess_run):
    runner.invoke(app, CMD, env=ZELLIJ_ENV)
    calls = _calls_for(mock_subprocess_run, "new-pane", "--floating", "--source-pane-id", "5")
    assert calls


def test_launcher_passes_patterns_file(mock_subprocess_run):
    runner.invoke(app, [*CMD, "--patterns-file", "/tmp/p.toml"], env=ZELLIJ_ENV)
    calls = _calls_for(mock_subprocess_run, "new-pane", "--patterns-file", "/tmp/p.toml")
    assert calls


def test_launcher_requires_zellij_env():
    with patch.dict("os.environ", {}, clear=True):
        result = runner.invoke(app, CMD)
    assert result.exit_code == 1


# --- worker mode ---

def _worker_side_effect(scrollback: str, yank: str):
    def _run(cmd, *args, **kwargs):
        if "dump-screen" in cmd:
            return _dump_result(scrollback)
        if cmd[0] == "fzf":
            return _fzf_result(yank)
        return MagicMock()
    return _run


def test_worker_dumps_source_pane(mock_subprocess_run):
    mock_subprocess_run.side_effect = _worker_side_effect("https://example.com", "")
    runner.invoke(app, WORKER_CMD, env=WORKER_ENV)
    assert _calls_for(mock_subprocess_run, "dump-screen", "-p", "5")


def test_worker_writes_selection_back(mock_subprocess_run):
    mock_subprocess_run.side_effect = _worker_side_effect("https://example.com", "https://example.com")
    result = runner.invoke(app, WORKER_CMD, env=WORKER_ENV)
    assert result.exit_code == 0
    assert _calls_for(mock_subprocess_run, "write-chars", "https://example.com")


def test_worker_no_patterns_exits_silently(mock_subprocess_run):
    mock_subprocess_run.side_effect = _worker_side_effect("nothing matchable here", "")
    result = runner.invoke(app, WORKER_CMD, env=WORKER_ENV)
    assert result.exit_code == 0
    assert not _calls_for(mock_subprocess_run, "write-chars")


def test_worker_fzf_no_selection_no_write(mock_subprocess_run):
    def side_effect(cmd, *args, **kwargs):
        if "dump-screen" in cmd:
            return _dump_result("https://example.com")
        if cmd[0] == "fzf":
            return _dump_result("")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect
    result = runner.invoke(app, WORKER_CMD, env=WORKER_ENV)
    assert result.exit_code == 0
    assert not _calls_for(mock_subprocess_run, "write-chars")


def test_worker_no_content_exits_silently(mock_subprocess_run):
    mock_subprocess_run.side_effect = _worker_side_effect("", "")
    result = runner.invoke(app, WORKER_CMD, env=WORKER_ENV)
    assert result.exit_code == 0
    assert not _calls_for(mock_subprocess_run, "write-chars")
