import asyncio
from collections.abc import Iterable
from typing import SupportsIndex, cast, override
from unittest.mock import patch

import pytest
from whenever import TimeDelta

from termstatus.git_status import (
    _GIT_STATUS_MAX_BYTES,
    _GIT_TIMEOUT,
    VcsState,
    _probe_git_status,
    _read_git_stdout,
    parse_git_status,
    probe_git,
)


class AsyncBytesReader:
    def __init__(self, value: bytes) -> None:
        self.value = value

    async def read(self, size: int) -> bytes:
        chunk, self.value = self.value[:size], self.value[size:]
        return chunk


def test_parse_porcelain_v2_with_untracked_files() -> None:
    vcs = parse_git_status(b"# branch.oid abc123\n# branch.head feature/demo\n? untracked_file.py\n")

    assert vcs == VcsState("feature/demo", False, True, untracked=True, commit="abc123")


@pytest.mark.asyncio
async def test_parse_git_status_stops_when_deadline_expires_while_scanning() -> None:
    class DelayedClock:
        def __init__(self, deadline: float) -> None:
            self.times = iter((deadline - 0.001, deadline + 0.001))

        def time(self) -> float:
            return next(self.times)

    deadline = asyncio.get_running_loop().time() + _GIT_TIMEOUT.total("seconds")
    with patch("termstatus.git_status.asyncio.get_running_loop", return_value=DelayedClock(deadline)):
        assert parse_git_status(b"# branch.oid abc123\n# branch.head enriched\n", deadline) is None


@pytest.mark.asyncio
async def test_git_probe_parses_truncated_status_output_after_kill() -> None:
    class KilledProcess:
        def __init__(self, stdout: bytes) -> None:
            self.returncode: int | None = None
            self.stdout = AsyncBytesReader(stdout)

        def kill(self) -> None:
            self.returncode = -9

    headers = b"# branch.oid abc\n# branch.head enriched\n"
    stdout = headers + b"? untracked/file.txt\n" * 5_000
    assert len(stdout) > _GIT_STATUS_MAX_BYTES

    state = await _probe_git_status(cast(asyncio.subprocess.Process, KilledProcess(stdout)), 1e18)

    assert state == VcsState("enriched", False, True, commit="abc", untracked=True)


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
    timeout_deadlines: list[float] = []
    timeout_at = asyncio.timeout_at

    def track_timeout_at(deadline: float) -> asyncio.Timeout:
        timeout_deadlines.append(deadline)
        return timeout_at(deadline)

    with (
        patch("termstatus.git_status.asyncio.create_subprocess_exec", side_effect=delayed_start) as create_process,
        patch("termstatus.git_status.asyncio.timeout_at", side_effect=track_timeout_at),
    ):
        started_loop = loop.time()
        assert await probe_git("/work/repo") is None

    assert create_process.await_count == 2
    assert [call.args for call in create_process.await_args_list] == [
        ("git", "-C", "/work/repo", "status", "--porcelain=v2", "--branch", "--show-stash", "-unormal"),
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
        with patch("termstatus.git_status.asyncio.get_running_loop", return_value=DelayedClock(deadline)):
            return parse_git_status(stdout, deadline)

    with (
        patch("termstatus.git_status.asyncio.create_subprocess_exec", side_effect=start),
        patch("termstatus.git_status.parse_git_status", side_effect=delayed_parse),
    ):
        assert await probe_git("/work/repo") is None


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

    loop = asyncio.get_running_loop()
    timeout_deadlines: list[float] = []
    timeout_at = asyncio.timeout_at

    def track_timeout_at(deadline: float) -> asyncio.Timeout:
        timeout_deadlines.append(deadline)
        return timeout_at(deadline)

    with (
        patch("termstatus.git_status.asyncio.create_subprocess_exec", side_effect=start) as create_process,
        patch("termstatus.git_status.asyncio.timeout_at", side_effect=track_timeout_at),
    ):
        started_loop = loop.time()
        assert await probe_git("/work/repo") is None

    assert create_process.await_count == 2
    assert timeout_deadlines
    assert abs(max(timeout_deadlines) - started_loop - _GIT_TIMEOUT.total("seconds")) < 0.01
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

    with patch("termstatus.git_status.asyncio.create_subprocess_exec", side_effect=start):
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

    with patch("termstatus.git_status.asyncio.create_subprocess_exec", side_effect=start):
        assert await probe_git("/work/repo") == VcsState("enriched", False, True, commit="abc123")


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

    with patch("termstatus.git_status.bytearray", TrackingBytearray, create=True):
        result = await _read_git_stdout(cast(asyncio.subprocess.Process, process))

    assert result == (b"", True)

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

    loop = asyncio.get_running_loop()
    timeout_deadlines: list[float] = []
    timeout_at = asyncio.timeout_at

    def track_timeout_at(deadline: float) -> asyncio.Timeout:
        timeout_deadlines.append(deadline)
        return timeout_at(deadline)

    with (
        patch("termstatus.git_status.asyncio.create_subprocess_exec", side_effect=start),
        patch("termstatus.git_status.asyncio.timeout_at", side_effect=track_timeout_at),
    ):
        started_loop = loop.time()
        assert await probe_git("/work/repo") == VcsState("enriched", False, True, commit="abc123")

    assert timeout_deadlines
    assert abs(max(timeout_deadlines) - started_loop - _GIT_TIMEOUT.total("seconds")) < 0.01
    assert origin.killed and origin.waited and origin.read_cancelled


def test_parse_splits_staged_and_dirty_entries() -> None:
    header = b"# branch.oid abc\n# branch.head main\n"
    staged = parse_git_status(header + b"1 M. N... 100644 100644 100644 a b file.py\n")
    dirty = parse_git_status(header + b"2 .R N... 100644 100644 100644 a b R100 new.py\told.py\n")
    unmerged = parse_git_status(header + b"u UU N... 100644 100644 100644 100644 a b c file.py\n")

    assert staged is not None and (staged.staged, staged.dirty) == (True, False)
    assert dirty is not None and (dirty.staged, dirty.dirty) == (False, True)
    assert unmerged is not None and (unmerged.staged, unmerged.dirty) == (True, True)


def test_parse_reads_stash_count() -> None:
    header = b"# branch.oid abc\n# branch.head main\n"

    assert parse_git_status(header + b"# stash 3\n") == VcsState("main", False, True, commit="abc", stash_count=3)
    assert parse_git_status(header) == VcsState("main", False, True, commit="abc")
