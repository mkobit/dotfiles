from collections import defaultdict
from collections.abc import Iterable

from claude_statusline.models import GitInfo, SegmentGenerationResult, StatusLineStdIn
from claude_statusline.segments.constants import get_icon


def render_lines(
    payload: StatusLineStdIn,
    git_info: GitInfo | None,
    segments: Iterable[SegmentGenerationResult],
) -> list[str]:
    """Renders the statusline as a list of strings."""
    sep = f" {get_icon('dot')} "

    lines_map = defaultdict(list)
    for seg in segments:
        if seg.line <= 3:
            lines_map[seg.line].append(seg)

    result_lines = []
    for line_num in sorted(lines_map.keys()):
        line_segments = sorted(lines_map[line_num], key=lambda s: (s.index, s.generator))
        text = sep.join(s.segment.text for s in line_segments)
        if text:
            result_lines.append(text)

    return result_lines
