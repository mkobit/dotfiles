import io
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from termstatus.agy import (
    Quota,
    VcsState,
    decode_payload,
    display_width,
    format_meter,
    limiting_timer,
    parse_git_status,
    probe_git,
    render_from_stdin,
    render_statusline,
    resolve_vcs,
    strip_ansi,
    write_vcs_cache,
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
    line = strip_ansi(render_statusline(payload, None))
    assert "g:" in line and "wk:2h" not in line


def test_gemini_timer_is_shown_at_width_eighty_without_cost() -> None:
    raw = {key: value for key, value in FULL_PAYLOAD.items() if key != "cost"}
    payload = decode_payload({**raw, "terminal_width": 80})
    assert "wk:2h" in strip_ansi(render_statusline(payload, None))


def test_three_p_timer_requires_one_ten_width() -> None:
    for width in (100, 109):
        line = strip_ansi(render_statusline(decode_payload({**FULL_PAYLOAD, "terminal_width": width}), None))
        assert "3p:◕75%" in line
        assert "3p:◕75% wk:2h" not in line
    line = strip_ansi(render_statusline(decode_payload({**FULL_PAYLOAD, "terminal_width": 110}), None))
    assert "3p:◕75% wk:2h" in line


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


@pytest.mark.asyncio
async def test_resolve_vcs_uses_fresh_cache_without_launching_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    write_vcs_cache("/work/repo", VcsState("main", True, True), now=time.time())
    with patch("termstatus.agy.asyncio.create_subprocess_exec") as create_process:
        assert await resolve_vcs(decode_payload({"cwd": "/work/repo"})) == VcsState("main", True, True)
        create_process.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_vcs_kills_git_after_75_ms() -> None:
    process = AsyncMock()
    process.communicate.side_effect = TimeoutError
    with patch("termstatus.agy.asyncio.create_subprocess_exec", return_value=process):
        assert await resolve_vcs(decode_payload({"cwd": "/work/repo"})) is None
    process.kill.assert_called_once()


def test_parse_git_status_marks_dirty_when_porcelain_has_changes() -> None:
    assert parse_git_status(b"## feature/demo...origin/feature/demo\n M file.py\n") == VcsState("feature/demo", True, True)


@pytest.mark.asyncio
async def test_payload_branch_bypasses_cache_and_git() -> None:
    payload = decode_payload({"cwd": "/work/repo", "vcs": {"branch": "payload", "dirty": False}})
    with patch("termstatus.agy.probe_git") as probe:
        assert await resolve_vcs(payload) == VcsState("payload", False, True)
        probe.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_vcs_ignores_expired_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    write_vcs_cache("/work/repo", VcsState("stale", False, True), now=time.time() - 3)
    with patch("termstatus.agy.probe_git", new=AsyncMock(return_value=VcsState("fresh", False, True))) as probe:
        assert await resolve_vcs(decode_payload({"cwd": "/work/repo"})) == VcsState("fresh", False, True)
        probe.assert_awaited_once_with("/work/repo")


@pytest.mark.asyncio
async def test_resolve_vcs_ignores_malformed_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    cache_file = tmp_path / "cache.json"
    cache_file.write_text("not json")
    with patch("termstatus.agy.cache_path", return_value=cache_file), patch(
        "termstatus.agy.probe_git", new=AsyncMock(return_value=VcsState("fresh", False, True))
    ) as probe:
        assert await resolve_vcs(decode_payload({"cwd": "/work/repo"})) == VcsState("fresh", False, True)
        probe.assert_awaited_once_with("/work/repo")


@pytest.mark.asyncio
async def test_resolve_vcs_caches_non_repository_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    payload = decode_payload({"cwd": "/work/not-a-repo"})
    with patch("termstatus.agy.probe_git", new=AsyncMock(return_value=VcsState(None, False, False))) as probe:
        assert await resolve_vcs(payload) == VcsState(None, False, False)
        assert await resolve_vcs(payload) == VcsState(None, False, False)
        probe.assert_awaited_once_with("/work/not-a-repo")


@pytest.mark.asyncio
async def test_probe_git_returns_non_repository_state_for_nonzero_exit() -> None:
    process = AsyncMock()
    process.communicate.return_value = (b"", b"")
    process.returncode = 128
    with patch("termstatus.agy.asyncio.create_subprocess_exec", return_value=process):
        assert await probe_git("/work/not-a-repo") == VcsState(None, False, False)
