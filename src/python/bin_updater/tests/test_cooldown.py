from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest

from bin_updater.cooldown import is_release_mature, parse_cooldown_to_seconds


def test_parse_cooldown_defaults() -> None:
    assert parse_cooldown_to_seconds(None) == 7 * 86400
    assert parse_cooldown_to_seconds(None, default_days=14) == 14 * 86400
    assert parse_cooldown_to_seconds("") == 7 * 86400


def test_parse_cooldown_valid_formats() -> None:
    assert parse_cooldown_to_seconds(21) == 21 * 86400
    assert parse_cooldown_to_seconds("21d") == 21 * 86400
    assert parse_cooldown_to_seconds("14D") == 14 * 86400
    assert parse_cooldown_to_seconds("5") == 5 * 86400


def test_parse_cooldown_invalid_formats() -> None:
    with pytest.raises(ValueError, match="Invalid cooldown format"):
        parse_cooldown_to_seconds("invalid")
    with pytest.raises(TypeError, match="Unsupported cooldown type"):
        parse_cooldown_to_seconds(cast(Any, ["7d"]))


def test_is_release_mature_cleared() -> None:
    now = datetime(2026, 11, 10, 12, 0, 0, tzinfo=UTC)
    eleven_days_ago = now - timedelta(days=11)
    published_iso = eleven_days_ago.isoformat()
    cooldown_seconds = 7 * 86400
    assert is_release_mature(published_iso, cooldown_seconds, now=now) is True


def test_is_release_mature_within_cooldown() -> None:
    now = datetime(2026, 11, 10, 12, 0, 0, tzinfo=UTC)
    three_days_ago = now - timedelta(days=3)
    published_iso = three_days_ago.isoformat()
    cooldown_seconds = 7 * 86400
    assert is_release_mature(published_iso, cooldown_seconds, now=now) is False


def test_is_release_mature_iso_trailing_z() -> None:
    now = datetime(2026, 11, 10, 12, 0, 0, tzinfo=UTC)
    published_iso = "2026-10-01T00:00:00Z"
    assert is_release_mature(published_iso, 7 * 86400, now=now) is True
