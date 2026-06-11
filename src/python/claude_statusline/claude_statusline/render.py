import shutil
from collections.abc import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from claude_statusline.layout import SegmentGenerationResult
from claude_statusline.payload import StatusLineStdIn
from claude_statusline.segments.constants import get_icon
from claude_statusline.segments.git import GitInfo


def render_lines(
    payload: StatusLineStdIn,
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

    table = Table(show_header=False, show_edge=False, box=None, padding=(0, 1), expand=True)
    table.add_column("left", justify="left", ratio=1, no_wrap=True)
    table.add_column("right", justify="right", no_wrap=True)

    for line in all_lines:
        line_segs = [s for s in segments_list if s.line == line]

        # Split into left (index < 10) and right (index >= 10)
        left_segs = [s for s in line_segs if s.index < 10]
        right_segs = [s for s in line_segs if s.index >= 10]

        left_text = sep.join(s.segment.text for s in sorted(left_segs, key=lambda x: x.index))
        right_text = sep.join(s.segment.text for s in sorted(right_segs, key=lambda x: x.index))

        table.add_row(
            Text.from_ansi(left_text) if left_text else Text(""), Text.from_ansi(right_text) if right_text else Text("")
        )

    console = Console(width=safe_width, force_terminal=True, color_system="truecolor", highlight=False)
    with console.capture() as capture:
        console.print(Panel(table, border_style="dim", expand=True))

    captured_lines = capture.get().splitlines()

    # Strip any extra completely empty lines at the end that Rich might add,
    # but keep lines with content (even just spaces if they were formatted)
    return [line.rstrip() for line in captured_lines if line.strip()]
