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

    # Decide the actual working directory
    cwd_str = payload.workspace.current_dir
    if not cwd_str and payload.cwd:
        cwd_str = payload.cwd
    cwd = Path(cwd_str).resolve() if cwd_str else Path.cwd()

    # Create segments
    model_seg = format_model_info(payload)
    session_seg = format_session_info(payload)
    dir_seg = format_directory(cwd)
    git_seg = format_git_full(git_info)
    context_seg = format_context_usage(payload.context_window)
    cost_seg = format_cost(payload)

    lines = []

    # Line 1: Claude Info
    line1_segs = [s for s in [model_seg] if s]
    if line1_segs:
        lines.append(DIVIDER_BAR.join(s.text for s in line1_segs))

    # Line 2: Working Dir & Session Info
    line2_segs = [s for s in [dir_seg, session_seg] if s]
    if line2_segs:
        lines.append(DIVIDER_DOT.join(s.text for s in line2_segs))

    # Line 3: Git & Costs
    line3_segs = [s for s in [git_seg, context_seg, cost_seg] if s]
    if line3_segs:
        lines.append(DIVIDER_BAR.join(s.text for s in line3_segs))

    return lines
