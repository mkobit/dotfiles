from typing import Any

from termstatus.payload import RateLimitWindow, StatusLineStdIn


def test_statusline_stdin_from_dict_non_dict_fallback() -> None:
    non_dict: Any = "invalid_input"
    payload = StatusLineStdIn.from_dict(non_dict)
    assert isinstance(payload, StatusLineStdIn)
    assert payload.cwd is None
    assert payload.rate_limits is not None


def test_statusline_stdin_from_dict_parses_rate_limits() -> None:
    raw = {
        "rate_limits": {
            "five_hour": {"used_percentage": 25.5, "resets_at": 1700000000},
            "seven_day": {"used_percentage": 60.0, "resets_at": 1700600000},
        }
    }
    payload = StatusLineStdIn.from_dict(raw)
    assert payload.rate_limits is not None
    assert payload.rate_limits.five_hour == RateLimitWindow(used_percentage=25.5, resets_at=1700000000)
    assert payload.rate_limits.seven_day == RateLimitWindow(used_percentage=60.0, resets_at=1700600000)
