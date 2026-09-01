import asyncio
import re
from collections.abc import Sequence
from contextlib import suppress
from typing import Final, cast

from termstatus.agy.constants import (
    _GIT_CLEANUP_RESERVE,
    _GIT_CLEANUP_SCHEDULING_MARGIN,
    _GIT_STATUS_MAX_BYTES,
    _GIT_TIMEOUT,
)
from termstatus.agy.decode import normalized_text
from termstatus.agy.models.payload import AgyPayload
from termstatus.agy.models.vcs import VcsState

_GIT_STDOUT_READ_BYTES: Final[int] = 4_096


def _deadline_expired(deadline: float | None) -> bool:
    return deadline is not None and asyncio.get_running_loop().time() >= deadline


def parse_git_status(stdout: bytes, deadline: float | None = None) -> VcsState | None:
    if len(stdout) > _GIT_STATUS_MAX_BYTES:
        return None
    branch: str | None = None
    upstream: str | None = None
    ahead = behind = 0
    dirty = saw_header = False
    for line in stdout.decode(errors="replace").splitlines():
        if _deadline_expired(deadline):
            return None
        if line.startswith("# branch.head "):
            saw_header = True
            value = line.removeprefix("# branch.head ").strip()
            branch = None if value.startswith("(") else normalized_text(value)
        elif line.startswith("# branch.upstream "):
            upstream = normalized_text(line.removeprefix("# branch.upstream "))
        elif match := re.fullmatch(r"# branch\.ab \+(\d+) -(\d+)", line):
            ahead, behind = (int(value) for value in match.groups())
        elif not line.startswith("# "):
            dirty = True
    return (
        VcsState(branch, dirty, True, upstream, ahead, behind)
        if saw_header and not _deadline_expired(deadline)
        else None
    )


def _build_vcs(vcs: VcsState, origin_stdout: bytes | None, deadline: float) -> VcsState | None:
    if _deadline_expired(deadline):
        return None
    origin_url = normalized_text(origin_stdout.decode(errors="replace")) if origin_stdout is not None else None
    return (
        VcsState(vcs.branch, vcs.dirty, vcs.is_repo, vcs.upstream, vcs.ahead, vcs.behind, origin_url)
        if not _deadline_expired(deadline)
        else None
    )


def _completed_processes(
    launches: Sequence[asyncio.Task[asyncio.subprocess.Process]],
) -> list[asyncio.subprocess.Process]:
    processes: list[asyncio.subprocess.Process] = []
    for launch in launches:
        if not launch.done() or launch.cancelled():
            continue
        with suppress(Exception):
            processes.append(launch.result())
    return processes


async def _read_git_stdout(process: asyncio.subprocess.Process) -> bytes | None:
    if process.stdout is None:
        return None
    stdout = bytearray()
    while len(stdout) <= _GIT_STATUS_MAX_BYTES:
        chunk = await process.stdout.read(min(_GIT_STDOUT_READ_BYTES, _GIT_STATUS_MAX_BYTES + 1 - len(stdout)))
        if not chunk:
            return bytes(stdout)
        stdout.extend(chunk)
    if process.returncode is None:
        with suppress(ProcessLookupError):
            process.kill()
    while await process.stdout.read(_GIT_STDOUT_READ_BYTES):
        pass
    return None


async def _probe_git_status(process: asyncio.subprocess.Process, deadline: float) -> VcsState | None:
    stdout = await _read_git_stdout(process)
    if stdout is not None and process.returncode is None:
        await process.wait()
    return parse_git_status(stdout, deadline) if stdout is not None and process.returncode == 0 else None


async def _probe_git_origin(process: asyncio.subprocess.Process) -> bytes | None:
    stdout = await _read_git_stdout(process)
    if stdout is not None and process.returncode is None:
        await process.wait()
    return stdout if process.returncode == 0 else None


async def _cancel_git_work(
    launches: Sequence[asyncio.Task[asyncio.subprocess.Process]],
    communications: Sequence[asyncio.Task[object]],
    processes: Sequence[asyncio.subprocess.Process],
    deadline: float,
) -> None:
    pending = [task for task in (*launches, *communications) if not task.done()]
    for task in pending:
        task.cancel()
    for process in processes:
        if process.returncode is None:
            with suppress(ProcessLookupError):
                process.kill()
    waiters = [process.wait() for process in processes if process.returncode is None]
    if pending or waiters:
        with suppress(TimeoutError):
            async with asyncio.timeout_at(deadline - _GIT_CLEANUP_SCHEDULING_MARGIN.total("seconds")):
                await asyncio.gather(*pending, *waiters, return_exceptions=True)


async def probe_git(cwd: str) -> VcsState | None:
    deadline = asyncio.get_running_loop().time() + _GIT_TIMEOUT.total("seconds")
    processes: list[asyncio.subprocess.Process] = []
    communications: list[asyncio.Task[object]] = []
    vcs: VcsState | None = None
    launches = [
        asyncio.create_task(
            asyncio.create_subprocess_exec(
                "git",
                "-C",
                cwd,
                "status",
                "--porcelain=v2",
                "--branch",
                "-uno",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
        ),
        asyncio.create_task(
            asyncio.create_subprocess_exec(
                "git",
                "-C",
                cwd,
                "remote",
                "get-url",
                "origin",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
        ),
    ]
    try:
        async with asyncio.timeout_at(deadline):
            async with asyncio.timeout_at(deadline - _GIT_CLEANUP_RESERVE.total("seconds")):
                results = await asyncio.gather(*launches, return_exceptions=True)
                processes = [result for result in results if not isinstance(result, BaseException)]
                if len(processes) == len(launches):
                    communications = [
                        asyncio.create_task(_probe_git_status(processes[0], deadline)),
                        asyncio.create_task(_probe_git_origin(processes[1])),
                    ]
                    results = await asyncio.gather(*communications, return_exceptions=True)
                    if not isinstance(results[0], BaseException):
                        vcs = cast(VcsState | None, results[0])
                        origin_stdout = (
                            cast(bytes, results[1])
                            if not isinstance(results[1], BaseException) and results[1] is not None
                            else None
                        )
                        if vcs and (enriched_vcs := _build_vcs(vcs, origin_stdout, deadline)):
                            return enriched_vcs
    except TimeoutError:
        pass
    finally:
        processes = _completed_processes(launches)
        if communications and communications[0].done() and not communications[0].cancelled():
            with suppress(Exception):
                vcs = cast(VcsState | None, communications[0].result()) or vcs
        await _cancel_git_work(launches, communications, processes, deadline)
    return vcs


def fallback_vcs(payload: AgyPayload) -> VcsState | None:
    return VcsState(payload.vcs.branch, payload.vcs.dirty, payload.vcs.is_repo) if payload.vcs else None


async def resolve_vcs(payload: AgyPayload) -> VcsState | None:
    return await probe_git(payload.cwd) or fallback_vcs(payload) if payload.cwd else payload.vcs
