import asyncio
import io
import json
import sys
import time
from collections.abc import Iterable, Mapping, MutableMapping
from dataclasses import FrozenInstanceError
from typing import SupportsIndex, cast, override
from unittest.mock import AsyncMock, patch

import pytest
from whenever import TimeDelta

from termstatus.agy.cli import render_from_stdin
from termstatus.agy.git import (
    _GIT_STATUS_MAX_BYTES,
    _GIT_TIMEOUT,
    _read_git_stdout,
    parse_git_status,
    probe_git,
    resolve_vcs,
)
from termstatus.agy.protocol import Quota, VcsState, decode_payload
from termstatus.agy.statusline import display_width, git_branch, render_statusline, strip_ansi
from termstatus.agy.term_colors import _STATE_COLORS
from termstatus.main import main

FULL_PAYLOAD = {
    "agent_state": "working",
    "cwd": "/work/repo",
    "model": {"display_name": "GPT-5.6 (high)", "effort": "high"},
    "execution_mode": "autonomous",
    "plan": {"tier": "full"},
    "sandbox": {"enabled": True, "allow_network": False},
    "vim_mode": "insert",
    "context_window": {"remaining_percentage": 82},
    "quota": {
        "codex-5h": {"remaining_fraction": 0.50, "reset_in_seconds": 1800},
        "codex-weekly": {"remaining_percentage": 10, "reset_in_seconds": 7200},
    },
    "cost": {"estimated": 0.01},
    "vcs": {
        "branch": "feature/renderer",
        "dirty": True,
        "upstream": "origin/feature/renderer",
        "ahead": 2,
        "behind": 1,
    },
    "tasks": [{"id": "one"}, {"id": "two"}, {"id": "three"}],
    "pending_input_count": 2,
    "confirmation_pending": True,
    "artifacts": [{"id": "one"}],
    "terminal_width": 160,
}


class AsyncBytesReader:
    def __init__(self, value: bytes) -> None:
        self.value = value

    async def read(self, size: int) -> bytes:
        chunk, self.value = self.value[:size], self.value[size:]
        return chunk


def rendered(raw: Mapping[str, object], vcs: VcsState | None = None) -> list[str]:
    return strip_ansi(render_statusline(decode_payload(raw), vcs)).splitlines()


def test_wide_render_uses_four_conditional_rows() -> None:
    lines = rendered(FULL_PAYLOAD)

    assert len(lines) == 4
    assert all(
        expected in line
        for expected, line in zip(
            (
                "working",
                "GPT-5.6",
                "high",
                "autonomous",
                "plan:full",
                "sandbox:no-net",
                "vim:insert",
            ),
            [lines[0]] * 7,
            strict=True,
        )
    )
    assert "/work/repo" in lines[1]
    assert "82% ctx" in lines[1] and "codex-5h:50%" in lines[1] and "codex-weekly:10%" in lines[1]
    assert "$0.01" in lines[1]
    assert "feature/renderer*" in lines[2] and "origin/feature/renderer" in lines[2]
    assert "ahead:2" in lines[2] and "behind:1" in lines[2]
    assert "tasks:3" in lines[3] and "input:2" in lines[3]
    assert "confirm" in lines[3] and "artifacts:1" in lines[3]


def test_narrow_render_omits_lower_priority_slots_without_overflowing() -> None:
    lines = rendered({**FULL_PAYLOAD, "terminal_width": 40})

    assert "working" in lines[0]
    assert "plan:full" not in lines[0] and "vim:insert" not in lines[0]
    assert all(display_width(line) <= 40 for line in lines)


def test_payload_display_text_cannot_inject_terminal_controls_or_rows() -> None:
    output = render_statusline(
        decode_payload(
            {
                "agent_state": "working\x1b[31m",
                "cwd": "/work\nrepo",
                "model": {"display_name": "model\x1b]8;;bad\x1b\\"},
                "quota": {"quota\nname\x1b[31m": {"remaining_percentage": 50}},
                "terminal_width": 160,
            }
        ),
        VcsState("branch\nname\x1b[31m", True, True),
    )

    assert output.count("\n") == 2
    assert "\x1b[31m" not in output
    assert "\r" not in output


def test_disabled_sandbox_is_rendered() -> None:
    assert "sandbox:off" in "\n".join(rendered({"sandbox": {"enabled": False}, "terminal_width": 160}))


def test_detached_dirty_repository_still_shows_dirty_state() -> None:
    line = render_statusline(decode_payload({"terminal_width": 80}), VcsState(None, True, True))

    assert "dirty" in strip_ansi(line)


def test_quota_without_reset_is_rendered() -> None:
    assert "quota:50%" in "\n".join(rendered({"quota": {"quota": {"remaining_percentage": 50}}}))


def test_decoded_quotas_are_immutable_and_use_time_delta_resets() -> None:
    quota = decode_payload({"quota": {"five-hour": {"remaining_percentage": 50, "reset_in_seconds": 1800}}}).quotas[
        "five-hour"
    ]

    assert quota == Quota(remaining=50, reset_in=TimeDelta(minutes=30))
    with pytest.raises(TypeError):
        cast(MutableMapping[str, Quota], decode_payload({}).quotas)["new"] = quota
    with pytest.raises(FrozenInstanceError):
        field = "remaining"
        setattr(quota, field, 0)


def test_state_colors_are_runtime_immutable() -> None:
    with pytest.raises(TypeError):
        cast(MutableMapping[str, str], _STATE_COLORS)["idle"] = "changed"


def test_missing_optional_fields_omit_empty_rows_and_sensitive_fields() -> None:
    lines = rendered(
        {
            "agent_state": "idle",
            "email": "person@example.com",
            "transcript_path": "/private/transcript",
            "product": "antigravity",
            "version": "9.9.9",
        }
    )

    assert lines == ["[idle]"]
    assert "person@example.com" not in "\n".join(lines)


def test_reasoning_precedence_is_model_effort_then_reasoning_then_top_level() -> None:
    assert decode_payload({"model": {"effort": "high", "reasoning_effort": "medium"}, "effort": "low"}).effort == "high"
    assert decode_payload({"model": {"reasoning_effort": "medium"}, "effort": "low"}).effort == "medium"
    assert decode_payload({"effort": "low"}).effort == "low"


def test_activity_task_count_never_invents_a_total() -> None:
    line = "\n".join(rendered({"tasks": 3, "terminal_width": 80}))

    assert "tasks:3" in line
    assert "/" not in line


def test_malformed_json_renders_without_throwing(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))

    render_from_stdin()

    assert strip_ansi(capsys.readouterr().out) == "[idle]\n"


def test_main_dispatches_antigravity_render_without_subprocess(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "argv", ["statusline", "antigravity", "render"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))

    with patch("termstatus.agy.git.asyncio.create_subprocess_exec") as create_process:
        main()

    assert strip_ansi(capsys.readouterr().out) == "[idle]\n"
    create_process.assert_not_called()


def test_huge_valid_json_numbers_render_without_throwing(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    huge = 10**1000
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "terminal_width": huge,
                    "context_window": {"remaining_percentage": huge},
                    "quota": {"quota": {"remaining_percentage": huge}},
                }
            )
        ),
    )

    render_from_stdin()

    assert "[idle]" in strip_ansi(capsys.readouterr().out)


def test_resolution_error_uses_payload_branch_and_dirty_fallback_only(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO('{"cwd":"/work/repo","vcs":{"branch":"payload","dirty":true,"upstream":"stale","ahead":2}}'),
    )
    with patch("termstatus.agy.cli.resolve_vcs", new=AsyncMock(side_effect=RuntimeError)):
        render_from_stdin()

    output = strip_ansi(capsys.readouterr().out)
    assert "payload*" in output
    assert "stale" not in output and "ahead:2" not in output


def test_parse_porcelain_v2_and_renders_github_origin_as_osc8_link() -> None:
    vcs = parse_git_status(
        b"# branch.oid abc123\n# branch.head feature/demo\n# branch.upstream origin/feature/demo\n# branch.ab +2 -1\n1 .M N... 100644 100644 100644 abc abc file.py\n"
    )

    assert vcs == VcsState("feature/demo", True, True, "origin/feature/demo", 2, 1)
    line = render_statusline(
        decode_payload({"terminal_width": 160}),
        VcsState("feature/demo", False, True, "origin/feature/demo", 2, 1, "git@github.com:stripe/example.git"),
    )
    assert "\033]8;;https://github.com/stripe/example\033\\feature/demo\033]8;;\033\\" in line


@pytest.mark.asyncio
async def test_parse_git_status_stops_when_deadline_expires_while_scanning() -> None:
    class DelayedClock:
        def __init__(self, deadline: float) -> None:
            self.times = iter((deadline - 0.001, deadline + 0.001))

        def time(self) -> float:
            return next(self.times)

    deadline = asyncio.get_running_loop().time() + _GIT_TIMEOUT.total("seconds")
    started = time.perf_counter()
    with patch("termstatus.agy.git.asyncio.get_running_loop", return_value=DelayedClock(deadline)):
        assert parse_git_status(b"# branch.oid abc123\n# branch.head enriched\n", deadline) is None

    assert time.perf_counter() - started < _GIT_TIMEOUT.total("seconds")


def test_parse_git_status_rejects_oversized_stdout() -> None:
    stdout = b"# branch.head enriched\n" * 3_000

    assert parse_git_status(stdout) is None


def test_osc8_git_branch_uses_only_visible_width_when_fitting_slots() -> None:
    vcs = VcsState("界界", False, True, origin_url="git@github.com:stripe/example.git")

    assert display_width(git_branch(vcs) or "") == 4
    assert "界界" in render_statusline(decode_payload({"terminal_width": 10}), vcs)


@pytest.mark.asyncio
async def test_git_probe_launches_exactly_two_commands_and_falls_back_after_shared_deadline() -> None:
    class FinishedProcess:
        def __init__(self, stdout: bytes) -> None:
            self.returncode = 0
            self.stdout = AsyncBytesReader(stdout)

    processes = [
        FinishedProcess(b"# branch.oid abc123\n# branch.head enriched\n"),
        FinishedProcess(b"git@github.com:stripe/example.git\n"),
    ]

    async def delayed_start(*_args: object, **_kwargs: object) -> FinishedProcess:
        await asyncio.sleep(_GIT_TIMEOUT.total("seconds") + 0.005)
        return processes.pop(0)

    loop = asyncio.get_running_loop()
    started = time.perf_counter()
    timeout_deadlines: list[float] = []
    timeout_at = asyncio.timeout_at

    def track_timeout_at(deadline: float) -> asyncio.Timeout:
        timeout_deadlines.append(deadline)
        return timeout_at(deadline)

    with (
        patch("termstatus.agy.git.asyncio.create_subprocess_exec", side_effect=delayed_start) as create_process,
        patch("termstatus.agy.git.asyncio.timeout_at", side_effect=track_timeout_at),
    ):
        payload = decode_payload(
            {
                "cwd": "/work/repo",
                "vcs": {"branch": "payload", "dirty": True, "upstream": "stale", "ahead": 2, "behind": 1},
            }
        )
        started_loop = loop.time()
        assert await resolve_vcs(payload) == VcsState("payload", True, True)

    assert time.perf_counter() - started < _GIT_TIMEOUT.total("seconds")
    assert create_process.await_count == 2
    assert [call.args for call in create_process.await_args_list] == [
        ("git", "-C", "/work/repo", "status", "--porcelain=v2", "--branch", "-uno"),
        ("git", "-C", "/work/repo", "remote", "get-url", "origin"),
    ]
    assert timeout_deadlines
    assert TimeDelta(milliseconds=125) == _GIT_TIMEOUT
    assert abs(max(timeout_deadlines) - started_loop - _GIT_TIMEOUT.total("seconds")) < 0.01


@pytest.mark.asyncio
async def test_git_probe_falls_back_when_porcelain_parsing_crosses_shared_deadline() -> None:
    class FinishedProcess:
        def __init__(self, stdout: bytes) -> None:
            self.returncode = 0
            self.stdout = AsyncBytesReader(stdout)

    processes = [
        FinishedProcess(b"# branch.oid abc123\n# branch.head enriched\n"),
        FinishedProcess(b"git@github.com:stripe/example.git\n"),
    ]

    async def start(*_args: object, **_kwargs: object) -> FinishedProcess:
        return processes.pop(0)

    class DelayedClock:
        def __init__(self, deadline: float) -> None:
            self.times = iter((deadline - 0.001, deadline + 0.001))

        def time(self) -> float:
            return next(self.times)

    def delayed_parse(stdout: bytes, deadline: float) -> VcsState | None:
        with patch("termstatus.agy.git.asyncio.get_running_loop", return_value=DelayedClock(deadline)):
            return parse_git_status(stdout, deadline)

    payload = decode_payload({"cwd": "/work/repo", "vcs": {"branch": "payload", "dirty": True}})
    started = time.perf_counter()
    with (
        patch("termstatus.agy.git.asyncio.create_subprocess_exec", side_effect=start),
        patch("termstatus.agy.git.parse_git_status", side_effect=delayed_parse),
    ):
        assert await resolve_vcs(payload) == VcsState("payload", True, True)

    assert time.perf_counter() - started < _GIT_TIMEOUT.total("seconds")


@pytest.mark.asyncio
async def test_git_probe_cancels_stdout_reads_and_reaps_processes_within_deadline() -> None:
    class SlowProcess:
        def __init__(self) -> None:
            self.returncode: int | None = None
            self.killed = False
            self.stdout_read_cancelled = False
            self.wait_started = False
            self.stdout = self

        async def read(self, _size: int) -> bytes:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.stdout_read_cancelled = True
                raise
            return b""

        def kill(self) -> None:
            self.killed = True

        async def wait(self) -> int:
            self.wait_started = True
            await asyncio.Event().wait()
            return 0

    processes = [SlowProcess(), SlowProcess()]
    launches = processes.copy()

    async def start(*_args: object, **_kwargs: object) -> SlowProcess:
        return launches.pop(0)

    started = time.perf_counter()
    with patch("termstatus.agy.git.asyncio.create_subprocess_exec", side_effect=start) as create_process:
        assert await probe_git("/work/repo") is None

    assert time.perf_counter() - started < _GIT_TIMEOUT.total("seconds")
    assert create_process.await_count == 2
    assert all(process.killed and process.stdout_read_cancelled and process.wait_started for process in processes)


@pytest.mark.asyncio
async def test_git_probe_reaps_a_process_when_the_other_launch_times_out() -> None:
    class StartedProcess:
        def __init__(self) -> None:
            self.returncode: int | None = None
            self.killed = False
            self.waited = False

        def kill(self) -> None:
            self.killed = True

        async def wait(self) -> int:
            self.waited = True
            self.returncode = -9
            return self.returncode

    process = StartedProcess()

    async def start(*args: object, **_kwargs: object) -> StartedProcess:
        if args[-3:] == ("remote", "get-url", "origin"):
            await asyncio.Event().wait()
        return process

    with patch("termstatus.agy.git.asyncio.create_subprocess_exec", side_effect=start):
        assert await probe_git("/work/repo") is None

    assert process.killed and process.waited


@pytest.mark.asyncio
async def test_git_probe_keeps_status_when_origin_lookup_fails() -> None:
    class FinishedProcess:
        def __init__(self, stdout: bytes, returncode: int) -> None:
            self.returncode = returncode
            self.stdout = AsyncBytesReader(stdout)

    processes = [
        FinishedProcess(b"# branch.oid abc123\n# branch.head enriched\n", 0),
        FinishedProcess(b"", 1),
    ]

    async def start(*_args: object, **_kwargs: object) -> FinishedProcess:
        return processes.pop(0)

    with patch("termstatus.agy.git.asyncio.create_subprocess_exec", side_effect=start):
        assert await probe_git("/work/repo") == VcsState("enriched", False, True)


@pytest.mark.asyncio
async def test_git_stdout_rejects_content_beyond_the_retained_buffer_limit() -> None:
    class BoundedStdout:
        def __init__(self, value: bytes) -> None:
            self.value = value
            self.read_sizes: list[int] = []

        async def read(self, size: int) -> bytes:
            self.read_sizes.append(size)
            chunk, self.value = self.value[:size], self.value[size:]
            return chunk

    class FinishedProcess:
        def __init__(self, stdout: bytes) -> None:
            self.returncode = 0
            self.stdout = BoundedStdout(stdout)

    process = FinishedProcess(b"x" * (_GIT_STATUS_MAX_BYTES + 1))
    retained_sizes: list[int] = []

    class TrackingBytearray(bytearray):
        @override
        def extend(self, value: Iterable[SupportsIndex], /) -> None:
            super().extend(value)
            retained_sizes.append(len(self))

    with patch("termstatus.agy.git.bytearray", TrackingBytearray, create=True):
        assert await _read_git_stdout(cast(asyncio.subprocess.Process, process)) is None

    assert max(retained_sizes) == _GIT_STATUS_MAX_BYTES
    assert max(process.stdout.read_sizes) <= _GIT_STATUS_MAX_BYTES


@pytest.mark.asyncio
async def test_git_probe_returns_status_when_origin_stdout_blocks() -> None:
    class StatusProcess:
        def __init__(self) -> None:
            self.returncode = 0
            self.stdout = AsyncBytesReader(b"# branch.oid abc123\n# branch.head enriched\n")

    class BlockedOriginProcess:
        def __init__(self) -> None:
            self.returncode: int | None = None
            self.killed = False
            self.waited = False
            self.read_cancelled = False
            self.stdout = self

        async def read(self, _size: int) -> bytes:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.read_cancelled = True
                raise
            return b""

        def kill(self) -> None:
            self.killed = True

        async def wait(self) -> int:
            self.waited = True
            self.returncode = -9
            return self.returncode

    origin = BlockedOriginProcess()
    processes = [StatusProcess(), origin]

    async def start(*_args: object, **_kwargs: object) -> StatusProcess | BlockedOriginProcess:
        return processes.pop(0)

    started = time.perf_counter()
    with patch("termstatus.agy.git.asyncio.create_subprocess_exec", side_effect=start):
        assert await probe_git("/work/repo") == VcsState("enriched", False, True)

    assert time.perf_counter() - started < _GIT_TIMEOUT.total("seconds")
    assert origin.killed and origin.waited and origin.read_cancelled


@pytest.mark.asyncio
async def test_git_probe_is_not_started_without_a_cwd() -> None:
    with patch("termstatus.agy.git.asyncio.create_subprocess_exec") as create_process:
        assert await resolve_vcs(decode_payload({"vcs": {"branch": "payload", "dirty": True}})) == VcsState(
            "payload", True, True
        )

    create_process.assert_not_called()
