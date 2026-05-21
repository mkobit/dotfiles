from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from termbud.main import app

runner = CliRunner()

ZELLIJ_ENV = {"ZELLIJ": "0", "ZELLIJ_PANE_ID": "6", "ZELLIJ_SESSION_NAME": "test"}
CMD_PANE = ["zellij", "history-search", "--source-pane-id", "5"]


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


# --- --source-pane-id path (dump-screen + write-chars) ---


def test_dumps_source_pane(mock_subprocess_run):
    mock_subprocess_run.side_effect = _side_effect("https://example.com", "")
    runner.invoke(app, CMD_PANE, env=ZELLIJ_ENV)
    assert _calls_for(mock_subprocess_run, "dump-screen", "-p", "5")


def test_writes_selection_back_to_source(mock_subprocess_run):
    mock_subprocess_run.side_effect = _side_effect("https://example.com", "https://example.com")
    result = runner.invoke(app, CMD_PANE, env=ZELLIJ_ENV)
    assert result.exit_code == 0
    assert _calls_for(mock_subprocess_run, "write-chars", "--pane-id", "5", "https://example.com")


def test_no_patterns_exits_silently(mock_subprocess_run):
    mock_subprocess_run.side_effect = _side_effect("nothing matchable here", "")
    result = runner.invoke(app, CMD_PANE, env=ZELLIJ_ENV)
    assert result.exit_code == 0
    assert not _calls_for(mock_subprocess_run, "write-chars")


def test_fzf_no_selection_no_write(mock_subprocess_run):
    def side_effect(cmd, *args, **kwargs):
        if "dump-screen" in cmd:
            return _dump_result("https://example.com")
        if cmd[0] == "fzf":
            return _dump_result("")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect
    result = runner.invoke(app, CMD_PANE, env=ZELLIJ_ENV)
    assert result.exit_code == 0
    assert not _calls_for(mock_subprocess_run, "write-chars")


def test_no_content_exits_silently(mock_subprocess_run):
    mock_subprocess_run.side_effect = _side_effect("", "")
    result = runner.invoke(app, CMD_PANE, env=ZELLIJ_ENV)
    assert result.exit_code == 0
    assert not _calls_for(mock_subprocess_run, "write-chars")


def test_requires_zellij_env():
    with patch.dict("os.environ", {}, clear=True):
        result = runner.invoke(app, CMD_PANE)
    assert result.exit_code == 1


# --- --from-file path (DumpScreen-based, no write-back) ---


def test_from_file_reads_scrollback(mock_subprocess_run, tmp_path):
    scrollback_file = tmp_path / "scrollback.txt"
    scrollback_file.write_text("https://example.com")
    mock_subprocess_run.side_effect = _side_effect("", "")
    runner.invoke(
        app,
        ["zellij", "history-search", "--from-file", str(scrollback_file)],
        env=ZELLIJ_ENV,
    )
    assert not _calls_for(mock_subprocess_run, "dump-screen")


def test_from_file_no_write_back_without_pane_id(mock_subprocess_run, tmp_path):
    scrollback_file = tmp_path / "scrollback.txt"
    scrollback_file.write_text("https://example.com")

    def side_effect(cmd, *args, **kwargs):
        if cmd[0] == "fzf":
            return _fzf_result("https://example.com")
        return MagicMock()

    mock_subprocess_run.side_effect = side_effect
    result = runner.invoke(
        app,
        ["zellij", "history-search", "--from-file", str(scrollback_file)],
        env=ZELLIJ_ENV,
    )
    assert result.exit_code == 0
    assert not _calls_for(mock_subprocess_run, "write-chars")


def test_from_file_no_content_exits_silently(mock_subprocess_run, tmp_path):
    scrollback_file = tmp_path / "scrollback.txt"
    scrollback_file.write_text("")
    mock_subprocess_run.side_effect = _side_effect("", "")
    result = runner.invoke(
        app,
        ["zellij", "history-search", "--from-file", str(scrollback_file)],
        env=ZELLIJ_ENV,
    )
    assert result.exit_code == 0
    assert not _calls_for(mock_subprocess_run, "write-chars")


def test_requires_from_file_or_pane_id(mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock()
    result = runner.invoke(app, ["zellij", "history-search"], env=ZELLIJ_ENV)
    assert result.exit_code == 1


def test_fzf_invoked_when_matches_found(mock_subprocess_run, tmp_path):
    scrollback_file = tmp_path / "scrollback.txt"
    scrollback_file.write_text("https://example.com")
    mock_subprocess_run.return_value = MagicMock(stdout="")
    runner.invoke(
        app,
        ["zellij", "history-search", "--from-file", str(scrollback_file)],
        env=ZELLIJ_ENV,
    )
    assert _calls_for(mock_subprocess_run, "fzf")
