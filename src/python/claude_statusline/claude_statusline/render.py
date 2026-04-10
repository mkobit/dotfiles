from pathlib import Path

from claude_statusline.models import GitInfo, StatusLineStdIn
from claude_statusline.segments import (
    DIVIDER_BAR,
    DIVIDER_DOT,
    format_context_usage,
    format_cost,
    format_directory,
    format_git_full,
    format_model_info,
    format_session_info,
)


def render_lines(payload: StatusLineStdIn, git_info: GitInfo | None) -> list[str]:
    """Renders the statusline as a list of strings, up to 3 lines."""

    cwd_str = payload.workspace.current_dir
    if not cwd_str and payload.cwd:
        cwd_str = payload.cwd
    cwd = Path(cwd_str).resolve() if cwd_str else Path.cwd()

    model_seg = format_model_info(payload)
    session_seg = format_session_info(payload)
    dir_seg = format_directory(cwd)
    git_seg = format_git_full(git_info)
    context_seg = format_context_usage(payload.context_window)
    cost_seg = format_cost(payload)

    line1 = DIVIDER_BAR.join(s.text for s in filter(None, [model_seg])) or None

    line2_segs = filter(None, [dir_seg, session_seg])
    line2 = DIVIDER_DOT.join(s.text for s in line2_segs) or None

    line3_segs = filter(None, [git_seg, context_seg, cost_seg])
    line3 = DIVIDER_BAR.join(s.text for s in line3_segs) or None

    return [line for line in [line1, line2, line3] if line]
