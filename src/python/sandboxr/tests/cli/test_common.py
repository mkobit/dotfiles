"""Unit tests for the guard helpers in cli/_common.py."""

from unittest.mock import patch

import pytest
import typer

from sandboxr.cli._common import _apply_timeout


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
