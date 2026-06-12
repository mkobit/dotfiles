import shutil
from collections.abc import Iterable

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from termstatus.layout import SegmentGenerationResult
from termstatus.payload import StatusLineStdIn
from termstatus.segments.constants import CYAN, RESET, get_icon
from termstatus.segments.git import GitInfo


def render_lines(
    payload: StatusLineStdIn | None,
    git_info: GitInfo | None,
    segments: Iterable[SegmentGenerationResult],
) -> list[str]:
    """Renders the statusline as a list of strings."""
    sep = f" {get_icon('dot')} "

    # Extract segments to a list for multiple passes
    segments_list = list(segments)
    if not segments_list:
        return []

    term_size = shutil.get_terminal_size((80, 24))
    # We leave a small buffer of ~4 columns for panel borders and padding.
    safe_width = max(20, term_size.columns - 4)

    # Find unique rows (lines)
    all_lines = sorted({seg.line for seg in segments_list})

    # Reference: https://github.com/Owloops/claude-powerline
    # TUI Mode layout engine uses a 5-column grid by default.
    table = Table(show_header=False, show_edge=False, box=None, padding=(0, 1), expand=True)
    table.add_column("col0", justify="left", no_wrap=True)
    table.add_column("col1", justify="left", ratio=1, overflow="ellipsis", no_wrap=True)
    table.add_column("col2", justify="right", no_wrap=True)
    table.add_column("col3", justify="right", no_wrap=True)
    table.add_column("col4", justify="right", no_wrap=True)

    for line in all_lines:
        line_segs = [s for s in segments_list if s.line == line]

        # Group segments by column
        col_segs: dict[int, list[SegmentGenerationResult]] = {i: [] for i in range(5)}

        for s in line_segs:
            if s.column is not None:
                col = max(0, min(4, s.column))
                col_segs[col].append(s)
            # Fallback mapping based on index
            elif s.index < 10:
                col_segs[0].append(s)
            else:
                col_segs[4].append(s)

        col_texts = []
        for i in range(5):
            segs = sorted(col_segs[i], key=lambda x: x.index)
            text = sep.join(s.segment.text for s in segs)
            col_texts.append(Text.from_ansi(text) if text else Text(""))

        table.add_row(*col_texts)

    console = Console(width=safe_width, force_terminal=True, color_system="truecolor", highlight=False)

    # Put session name at the top stretch row if available
    if payload is not None and payload.session_name:
        session_text = Text.from_ansi(f"{CYAN}#{payload.session_name}{RESET}", no_wrap=True)
        session_text.overflow = "ellipsis"
        renderable = Group(session_text, table)
    else:
        renderable = table

    with console.capture() as capture:
        console.print(Panel(renderable, border_style="dim", expand=True))

    captured_lines = capture.get().splitlines()

    # Strip any extra completely empty lines at the end that Rich might add,
    # but keep lines with content (even just spaces if they were formatted)
    return [line.rstrip() for line in captured_lines if line.strip()]
