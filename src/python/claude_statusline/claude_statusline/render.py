from collections.abc import Iterable

from rich.console import Console
from rich.table import Table
from rich.text import Text

from claude_statusline.models import GitInfo, SegmentGenerationResult, StatusLineStdIn
from claude_statusline.segments.constants import get_icon


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

    # Find unique columns (indices) and rows (lines)
    all_indices = sorted({seg.index for seg in segments_list})
    all_lines = sorted({seg.line for seg in segments_list})

    # Group segments by line then by index
    # We might have multiple segments with the same line and index, though
    # ideally we wouldn't. We'll join them with sep if they exist.
    grid_data = {}
    for line in all_lines:
        grid_data[line] = {}
        for index in all_indices:
            grid_data[line][index] = []

    for seg in segments_list:
        grid_data[seg.line][seg.index].append(seg)

    # Build the rich table
    table = Table(show_header=False, box=None, pad_edge=False, padding=(0, 2))

    # Add columns for each unique index
    for _ in all_indices:
        table.add_column()

    for line in all_lines:
        row_cells = []
        for index in all_indices:
            segs = grid_data[line][index]
            # Multiple segments in the same cell get joined
            text_str = sep.join(s.segment.text for s in sorted(segs, key=lambda x: x.generator))

            if text_str:
                row_cells.append(Text.from_ansi(text_str))
            else:
                row_cells.append(Text.from_ansi(""))

        table.add_row(*row_cells)

    # Use a wide console to prevent line wrapping during string extraction
    console = Console(width=2000, force_terminal=True, color_system="truecolor", highlight=False)
    with console.capture() as capture:
        console.print(table)

    output_lines = capture.get().splitlines()

    # Strip any extra completely empty lines at the end that Rich might add,
    # but keep lines with content (even just spaces if they were formatted)
    return [line.rstrip() for line in output_lines if line.strip()]
