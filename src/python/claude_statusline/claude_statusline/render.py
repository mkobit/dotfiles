import shutil
from collections.abc import Iterable

from rich.console import Console
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
    # We leave a buffer of ~20 columns to account for Claude's own trailing UI.
    # Claude uses some space on the right, and maybe a few chars for borders.
    safe_width = max(20, term_size.columns - 20)

    # Find unique rows (lines)
    all_lines = sorted({seg.line for seg in segments_list})

    # Group segments by line then by index
    grid_data = {}
    for line in all_lines:
        grid_data[line] = {}

    for seg in segments_list:
        if seg.index not in grid_data[seg.line]:
            grid_data[seg.line][seg.index] = []
        grid_data[seg.line][seg.index].append(seg)

    output_lines = []

    # Build a separate table per line to avoid columns syncing widths across different lines
    for line in all_lines:
        table = Table.grid(padding=(0, 2))

        indices = sorted(grid_data[line].keys())
        for _ in indices:
            table.add_column(justify="left", no_wrap=True)

        row_cells = []
        for index in indices:
            segs = grid_data[line][index]
            # Multiple segments in the same cell get joined
            text_str = sep.join(s.segment.text for s in sorted(segs, key=lambda x: x.generator))

            if text_str:
                row_cells.append(Text.from_ansi(text_str))
            else:
                row_cells.append(Text.from_ansi(""))

        if row_cells:
            table.add_row(*row_cells)

            # Use a bounded console to allow rich to gracefully truncate or handle the line
            console = Console(width=safe_width, force_terminal=True, color_system="truecolor", highlight=False)
            with console.capture() as capture:
                console.print(table)

            captured_lines = capture.get().splitlines()
            output_lines.extend(captured_lines)

    # Strip any extra completely empty lines at the end that Rich might add,
    # but keep lines with content (even just spaces if they were formatted)
    return [line.rstrip() for line in output_lines if line.strip()]
