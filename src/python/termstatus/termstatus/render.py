import asyncio
import os
import shutil
import sys
from collections.abc import Iterable, Sequence

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from termstatus.layout import SegmentGenerationResult
from termstatus.payload import StatusLineStdIn
from termstatus.segments.constants import CYAN, RESET
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


def _parse_positive_int(value: str) -> int | None:
    try:
        parsed = int(value)
        return parsed if parsed > 0 else None
    except ValueError:
        return None


async def probe_terminal_width(payload_width: int | None = None) -> int | None:
    if payload_width is not None and payload_width > 0:
        return payload_width

    override = os.environ.get("TERMSTATUS_WIDTH")
    if override:
        parsed = _parse_positive_int(override)
        if parsed is not None:
            return parsed

    env_columns = os.environ.get("COLUMNS")
    if env_columns:
        parsed = _parse_positive_int(env_columns)
        if parsed is not None:
            return parsed

    for stream in (sys.stdout, sys.stderr, sys.stdin):
        if stream and hasattr(stream, "isatty") and stream.isatty():
            try:
                size = os.get_terminal_size(stream.fileno())
                if size.columns > 0:
                    return size.columns
            except OSError, ValueError:
                pass

    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns if size.columns > 0 else 80


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


_LEAD_COLUMN = 0
_BODY_COLUMN = 1
_BADGE_COLUMN = 2


def _build_row_cells(line_segs: Sequence[SegmentGenerationResult]) -> tuple[Text, Text, Text]:
    lead = [s for s in line_segs if (s.column or 0) == _LEAD_COLUMN]
    body = [s for s in line_segs if (s.column or 0) == _BODY_COLUMN]
    trailing = [s for s in line_segs if (s.column or 0) >= _BADGE_COLUMN]
    lead_text = " ".join(s.segment.text for s in lead)
    body_text = "   ".join(s.segment.text for s in body)
    trailing_text = "  ".join(s.segment.text for s in trailing)
    # Everything from badge onward (bracket tags, trailing git icons, a token
    # ratio, ...) shares ONE cell rather than each getting its own aligned
    # column. A column that only one or two rows ever populate has nothing to
    # align against, so Rich pushes it out to an isolated, disconnected
    # position — confirmed twice now (trailing git icons, then the token
    # ratio). One shared "whatever comes after body" cell avoids that by
    # construction: it always sits immediately after ITS OWN row's body.
    return (
        Text.from_ansi(lead_text, no_wrap=True) if lead_text else Text(""),
        Text.from_ansi(body_text, no_wrap=True) if body_text else Text(""),
        Text.from_ansi(trailing_text, no_wrap=True) if trailing_text else Text(""),
    )


def render_lines(
    payload: StatusLineStdIn | None,
    git_info: GitInfo | None,
    segments: Iterable[SegmentGenerationResult],
    *,
    terminal_width: int | None = None,
) -> list[str]:
    """Renders segments as one shared table: lead/body columns size to the
    widest content across every row, so every row's cells start at the same
    position. Everything trailing (badges, status icons, secondary values)
    shares one cell per row instead of each being its own aligned column, so
    it always sits right next to that row's own content.
    """
    segments_list = list(segments)
    if not segments_list:
        return []

    effective_width = _effective_width(terminal_width)
    lines_map = _group_segments_by_line(segments_list)
    rows = [_build_row_cells(line_segs) for line_segs in lines_map.values()]

    table = Table(show_header=False, show_edge=False, box=None, padding=(0, 1))
    table.add_column("lead", justify="left", no_wrap=True)
    table.add_column("body", justify="left", no_wrap=True, max_width=effective_width, overflow="ellipsis")
    table.add_column("trailing", justify="left", no_wrap=True)
    for lead, body, trailing in rows:
        table.add_row(lead, body, trailing)

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
        console.print(Panel(renderable, border_style="dim", expand=False))

    return [line.rstrip() for line in capture.get().splitlines() if line.strip()]
