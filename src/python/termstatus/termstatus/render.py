import asyncio
import os
import shlex
import shutil
import sys
from collections.abc import Iterable, Sequence

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from termstatus.layout import SegmentGenerationResult
from termstatus.payload import StatusLineStdIn
from termstatus.segments.constants import CYAN, DIM, RESET, get_icon
from termstatus.segments.git import GitInfo

_RIGHT_COLUMN_THRESHOLD = 3


async def _run_cmd(cmd: list[str], *, timeout: float = 2.0) -> str | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        if proc.returncode == 0 and stdout:
            return stdout.decode().strip()
    except TimeoutError, OSError:
        pass
    return None


async def _run_shell_cmd(cmd: str, *, timeout: float = 2.0) -> str | None:
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        if proc.returncode == 0 and stdout:
            return stdout.decode().strip()
    except TimeoutError, OSError:
        pass
    return None


async def _get_parent_pid(pid: int) -> int | None:
    output = await _run_cmd(["ps", "-o", "ppid=", "-p", str(pid)])
    return _parse_positive_int(output) if output else None


async def _get_tty_for_pid(pid: int) -> str | None:
    output = await _run_cmd(["ps", "-o", "tty=", "-p", str(pid)])
    if output and output not in ("??", "?"):
        return output
    return None


async def _get_width_for_tty(tty: str) -> int | None:
    quoted_path = shlex.quote(f"/dev/{tty}")
    commands = [
        f"stty -f {quoted_path} size",
        f"stty -F {quoted_path} size",
        f"stty size < {quoted_path}",
    ]
    for cmd in commands:
        output = await _run_shell_cmd(cmd)
        if output:
            parts = output.split()
            if len(parts) >= 2:
                width = _parse_positive_int(parts[1])
                if width is not None:
                    return width
    return None


def _parse_positive_int(value: str) -> int | None:
    try:
        parsed = int(value)
        return parsed if parsed > 0 else None
    except ValueError:
        return None


async def probe_terminal_width() -> int | None:
    override = os.environ.get("TERMSTATUS_WIDTH")
    if override:
        parsed = _parse_positive_int(override)
        if parsed is not None:
            return parsed

    size = shutil.get_terminal_size(fallback=(0, 0))
    if size.columns > 0:
        return size.columns

    if sys.platform == "win32":
        return None

    # Claude Code spawns with piped stdio (no TTY).
    # Walk up ancestors to find the shell that owns the real PTY.
    pid = os.getpid()
    for _ in range(8):
        parent_pid = await _get_parent_pid(pid)
        if parent_pid is None:
            break
        pid = parent_pid
        tty = await _get_tty_for_pid(pid)
        if tty is None:
            continue
        width = await _get_width_for_tty(tty)
        if width is not None:
            return width

    return None


def _effective_width(probed: int | None) -> int:
    # Panel border + padding takes 4 chars (│ + space each side + │)
    return max(40, (probed or 80) - 4)


def _group_segments_by_line(
    segments: Sequence[SegmentGenerationResult],
) -> dict[int, Sequence[SegmentGenerationResult]]:
    by_line: dict[int, list[SegmentGenerationResult]] = {}
    for seg in segments:
        by_line.setdefault(seg.line, []).append(seg)
    return {k: sorted(v, key=lambda s: s.index) for k, v in sorted(by_line.items())}


def _split_left_right(
    segments: Sequence[SegmentGenerationResult],
) -> tuple[Sequence[SegmentGenerationResult], Sequence[SegmentGenerationResult]]:
    left = [s for s in segments if (s.column or 0) < _RIGHT_COLUMN_THRESHOLD]
    right = [s for s in segments if (s.column or 0) >= _RIGHT_COLUMN_THRESHOLD]
    return left, right


def render_lines(
    payload: StatusLineStdIn | None,
    git_info: GitInfo | None,
    segments: Iterable[SegmentGenerationResult],
    *,
    terminal_width: int | None = None,
) -> list[str]:
    """Renders the statusline as a list of strings using a flex layout."""
    sep = f" {DIM}{get_icon('dot')}{RESET} "

    segments_list = list(segments)
    if not segments_list:
        return []

    effective_width = _effective_width(terminal_width)

    lines_map = _group_segments_by_line(segments_list)

    table = Table(
        show_header=False,
        show_edge=False,
        box=None,
        padding=(0, 0),
        expand=True,
    )
    table.add_column("left", justify="left", ratio=1, overflow="ellipsis", no_wrap=True)
    table.add_column("right", justify="right", no_wrap=True)

    for line_segs in lines_map.values():
        left_segs, right_segs = _split_left_right(line_segs)

        left_text = sep.join(s.segment.text for s in left_segs) if left_segs else ""
        right_text = sep.join(s.segment.text for s in right_segs) if right_segs else ""

        table.add_row(
            Text.from_ansi(left_text) if left_text else Text(""),
            Text.from_ansi(right_text) if right_text else Text(""),
        )

    console = Console(
        width=effective_width,
        force_terminal=True,
        color_system="truecolor",
        highlight=False,
    )

    if payload is not None and payload.session_name:
        session_text = Text.from_ansi(f"{CYAN}#{payload.session_name}{RESET}", no_wrap=True)
        session_text.overflow = "ellipsis"
        renderable = Group(session_text, table)
    else:
        renderable = table

    with console.capture() as capture:
        console.print(Panel(renderable, border_style="dim", expand=True))

    return [line.rstrip() for line in capture.get().splitlines() if line.strip()]
