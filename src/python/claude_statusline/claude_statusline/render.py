from collections import defaultdict
from pathlib import Path

from claude_statusline.models import GitInfo, SegmentGenerationResult, StatusLineStdIn
from claude_statusline.segments import (
    DIVIDER_BAR,
    format_context_usage,
    format_cost,
    format_directory,
    format_git_full,
    format_model_info,
    format_obsidian_vault,
    format_session_info,
)


def render_lines(
    payload: StatusLineStdIn,
    git_info: GitInfo | None,
    extra_segments: list[SegmentGenerationResult] | None = None,
) -> list[str]:
    """Renders the statusline as a list of strings."""

    if extra_segments is None:
        extra_segments = []

    cwd_str = payload.workspace.current_dir
    if not cwd_str and payload.cwd:
        cwd_str = payload.cwd
    cwd = Path(cwd_str).resolve() if cwd_str else Path.cwd()

    segments = tuple(
        extra_segments
        + list(
            filter(
                None,
                [
                    format_model_info(payload),
                    format_session_info(payload),
                    format_directory(cwd),
                    format_obsidian_vault(cwd),
                    format_git_full(git_info),
                    format_context_usage(payload.context_window),
                    format_cost(payload),
                ],
            )
        )
    )

    lines_map = defaultdict(list)
    for seg in segments:
        lines_map[seg.line].append(seg)

    result_lines = []
    # Claude supports up to 3 lines. We render available lines sorted.
    for line_num in sorted(lines_map.keys()):
        line_segments = sorted(
            lines_map[line_num], key=lambda s: (s.index, s.generator)
        )
        text = DIVIDER_BAR.join(s.segment.text for s in line_segments)
        if text:
            result_lines.append(text)

    return result_lines
