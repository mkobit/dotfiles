"""Unit tests for the guard helpers in cli/_common.py."""

from unittest.mock import patch

import pytest
import typer

from sandboxr.cli._common import _apply_timeout, _log_invocation


def test_apply_timeout_none_returns_args_unchanged() -> None:
    assert _apply_timeout(["bwrap", "--foo"], None) == ["bwrap", "--foo"]


def test_apply_timeout_prefixes_with_foreground_flag() -> None:
    with patch("shutil.which", return_value="/usr/bin/timeout"):
        result = _apply_timeout(["bwrap", "--foo"], 300)
    assert result == ["/usr/bin/timeout", "--foreground", "300", "bwrap", "--foo"]


def test_apply_timeout_raises_when_binary_missing() -> None:
    with (
        patch("shutil.which", return_value=None),
        pytest.raises(typer.Exit),
    ):
        _apply_timeout(["bwrap", "--foo"], 300)


def test_log_invocation_writes_to_state_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    _log_invocation(["bwrap", "--ro-bind", "/"], action="test_run")
    log_file = tmp_path / "sandboxr" / "invocations.log"
    assert log_file.exists()
    content = log_file.read_text()
    assert "action=test_run" in content
    assert "command=bwrap --ro-bind /" in content
