import io
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from termstatus.agy import (
    Quota,
    VcsState,
    decode_payload,
    display_width,
    format_meter,
    limiting_timer,
    render_from_stdin,
    render_statusline,
    strip_ansi,
)

FULL_PAYLOAD = {
    "agent_state": "working",
    "cwd": "/work/repo",
    "model": {"display_name": "Gemini 3 (high)", "effort": "high"},
    "context_window": {"used_percentage": 18},
    "cost": {"estimated": 0.01},
    "terminal_width": 120,
    "quota": {
        "gemini-5h": {"remaining_fraction": 0.50, "reset_in_seconds": 1800},
        "gemini-weekly": {"remaining_fraction": 0.10, "reset_in_seconds": 7200},
        "3p-5h": {"remaining_fraction": 0.75, "reset_in_seconds": 1800},
        "3p-weekly": {"remaining_fraction": 0.50, "reset_in_seconds": 7200},
    },
    "sandbox": {"enabled": True, "allow_network": False},
}


def test_decode_payload_prefers_remaining_context() -> None:
    assert decode_payload({"context_window": {"remaining_percentage": 62, "used_percentage": 99}}).remaining_context == 62


def test_decode_payload_derives_remaining_context() -> None:
    assert decode_payload({"context_window": {"used_percentage": 17.6}}).remaining_context == 82


def test_wide_render_shows_the_canonical_statusline_information() -> None:
    line = strip_ansi(render_statusline(decode_payload(FULL_PAYLOAD), VcsState("main", True, True)))
    assert "82% ctx" in line and "$0.01" in line
    assert "g:" in line and "3p:" in line
    assert "repo" in line and "main*" in line
    assert "Gemini" in line and "high" in line and "sandbox" in line


@pytest.mark.parametrize(("remaining", "glyph"), [(0, "○"), (25, "◔"), (50, "◑"), (75, "◕"), (100, "●")])
def test_format_meter_uses_reference_thresholds(remaining: int, glyph: str) -> None:
    assert glyph in format_meter(remaining)


def test_limiting_timer_prioritizes_a_critical_weekly_quota() -> None:
    assert limiting_timer(Quota(50, 1800), Quota(10, 7_200)) == "wk:2h"


def test_display_width_ignores_ansi_sequences() -> None:
    assert display_width("\033[32m●\033[0m") == 1


def test_gemini_timer_requires_ninety_width_when_cost_is_present() -> None:
    payload = decode_payload({**FULL_PAYLOAD, "terminal_width": 80})
    assert "5h" not in strip_ansi(render_statusline(payload, None))


def test_three_p_timer_requires_one_ten_width() -> None:
    payload = decode_payload({**FULL_PAYLOAD, "terminal_width": 110})
    assert "3p:" in strip_ansi(render_statusline(payload, None))
    assert "3p:◕75% wk:2h" in strip_ansi(render_statusline(payload, None))


def test_narrow_render_does_not_duplicate_vcs_branch() -> None:
    payload = decode_payload({"terminal_width": 60, "cwd": "/work/repo"})
    assert strip_ansi(render_statusline(payload, VcsState("main", True, True))).count("main*") == 0
    assert strip_ansi(render_statusline(payload, VcsState("main", False, True))).count("main") == 1


def test_malformed_json_and_missing_fields_render_default(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    render_from_stdin()
    assert "[idle]" in capsys.readouterr().out


def test_debug_write_failure_preserves_render(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    with patch("termstatus.agy.os.environ.get", return_value="bad\x00path"):
        monkeypatch.setattr(sys, "stdin", io.StringIO('{"agent_state":"working"}'))
        render_from_stdin()
    assert "working" in capsys.readouterr().out


def test_state_render_uses_state_colour() -> None:
    line = render_statusline(decode_payload({"agent_state": "working"}), None)
    assert "\033[34m" in line


def test_entrypoint_does_not_import_typer_for_agy_render() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import sys; import termstatus.entrypoint; print('typer' in sys.modules)"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == "False\n"


def test_console_script_renders_from_a_fresh_process() -> None:
    command = [str(Path(sys.executable).with_name("statusline")), "antigravity", "render"]
    payload = '{"agent_state":"working"}'
    durations = []
    for _ in range(5):
        started = time.perf_counter()
        result = subprocess.run(command, input=payload, capture_output=True, check=False, text=True, timeout=1)
        durations.append(time.perf_counter() - started)
        assert result.returncode == 0
        assert "working" in result.stdout
    assert max(durations) < 0.75
