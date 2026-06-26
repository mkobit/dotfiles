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
    raw = (probed or 80) - 4
    return max(20, min(raw, 90))


def _group_segments_by_line(
    segments: Sequence[SegmentGenerationResult],
) -> dict[int, Sequence[SegmentGenerationResult]]:
    by_line: dict[int, list[SegmentGenerationResult]] = {}
    for seg in segments:
        by_line.setdefault(seg.line, []).append(seg)
    return {k: sorted(v, key=lambda s: s.index) for k, v in sorted(by_line.items())}


_RIGHT_COLUMN_THRESHOLD = 3
_GIT_GENERATORS = frozenset({"internal.git", "internal.chezmoi"})


def _is_git_section(line_segs: Sequence[SegmentGenerationResult]) -> bool:
    return all(s.generator in _GIT_GENERATORS for s in line_segs) and any((s.column or 0) == 1 for s in line_segs)


def _build_git_subtable(
    lines: Sequence[Sequence[SegmentGenerationResult]],
) -> Table:
    table = Table(
        show_header=False,
        show_edge=False,
        box=None,
        padding=(0, 1),
        expand=True,
    )
    table.add_column("label", justify="left", no_wrap=True, min_width=7)
    table.add_column("branch", justify="left", no_wrap=True, ratio=1)
    table.add_column("status", justify="left", no_wrap=True)
    table.add_column("right", justify="right", no_wrap=True)

    for line_segs in lines:
        col0 = [s for s in line_segs if (s.column or 0) == 0]
        col1 = [s for s in line_segs if (s.column or 0) == 1]
        col2 = [s for s in line_segs if (s.column or 0) == 2]
        col_right = [s for s in line_segs if (s.column or 0) >= _RIGHT_COLUMN_THRESHOLD]

        label_text = " ".join(s.segment.text for s in col0) if col0 else ""
        branch_text = " ".join(s.segment.text for s in col1) if col1 else ""
        status_text = " ".join(s.segment.text for s in col2) if col2 else ""
        right_text = " ".join(s.segment.text for s in col_right) if col_right else ""

        table.add_row(
            Text.from_ansi(label_text, no_wrap=True) if label_text else Text(""),
            Text.from_ansi(branch_text, no_wrap=True) if branch_text else Text(""),
            Text.from_ansi(status_text, no_wrap=True) if status_text else Text(""),
            Text.from_ansi(right_text, no_wrap=True) if right_text else Text(""),
        )

    return table


def _build_standard_row(
    line_segs: Sequence[SegmentGenerationResult],
    left_sep: str,
) -> tuple[Text, Text]:
    left = [s for s in line_segs if (s.column or 0) < _RIGHT_COLUMN_THRESHOLD]
    right = [s for s in line_segs if (s.column or 0) >= _RIGHT_COLUMN_THRESHOLD]
    left_text = left_sep.join(s.segment.text for s in left) if left else ""
    right_text = "  ".join(s.segment.text for s in right) if right else ""
    return (
        Text.from_ansi(left_text, no_wrap=True) if left_text else Text(""),
        Text.from_ansi(right_text, no_wrap=True) if right_text else Text(""),
    )


def render_lines(
    payload: StatusLineStdIn | None,
    git_info: GitInfo | None,
    segments: Iterable[SegmentGenerationResult],
    *,
    terminal_width: int | None = None,
) -> list[str]:
    """Renders segments as a panel with subtables for aligned git sections."""
    left_sep = f" {DIM}{get_icon('dot')}{RESET} "

    segments_list = list(segments)
    if not segments_list:
        return []

    effective_width = _effective_width(terminal_width)
    lines_map = _group_segments_by_line(segments_list)

    outer = Table(
        show_header=False,
        show_edge=False,
        box=None,
        padding=(0, 1),
        expand=True,
    )
    outer.add_column("left", justify="left", ratio=1, overflow="ellipsis", no_wrap=True)
    outer.add_column("right", justify="right", no_wrap=True)

    git_line_buffer: list[Sequence[SegmentGenerationResult]] = []

    def flush_git_buffer() -> None:
        if not git_line_buffer:
            return
        subtable = _build_git_subtable(git_line_buffer)
        outer.add_row(subtable, Text(""))
        git_line_buffer.clear()

    for line_segs in lines_map.values():
        if _is_git_section(line_segs):
            git_line_buffer.append(line_segs)
        else:
            flush_git_buffer()
            left_cell, right_cell = _build_standard_row(line_segs, left_sep)
            outer.add_row(left_cell, right_cell)

    flush_git_buffer()

    console = Console(
        width=effective_width,
        force_terminal=True,
        color_system="truecolor",
        highlight=False,
    )

    if payload is not None and payload.session_name:
        session_text = Text.from_ansi(f"{CYAN}#{payload.session_name}{RESET}", no_wrap=True)
        session_text.overflow = "ellipsis"
        renderable = Group(session_text, outer)
    else:
        renderable = outer

    with console.capture() as capture:
        console.print(Panel(renderable, border_style="dim", expand=True))

    return [line.rstrip() for line in capture.get().splitlines() if line.strip()]
