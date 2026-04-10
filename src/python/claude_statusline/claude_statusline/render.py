from pathlib import Path

from claude_statusline.models import GitInfo, StatusLineStdIn
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


def render_lines(payload: StatusLineStdIn, git_info: GitInfo | None) -> list[str]:
    """Renders the statusline as a list of strings, up to 3 lines."""

    cwd_str = payload.workspace.current_dir
    if not cwd_str and payload.cwd:
        cwd_str = payload.cwd
    cwd = Path(cwd_str).resolve() if cwd_str else Path.cwd()

    model_seg = format_model_info(payload)
    session_seg = format_session_info(payload)
    dir_seg = format_directory(cwd)
    obsidian_seg = format_obsidian_vault(cwd)
    git_seg = format_git_full(git_info)
    context_seg = format_context_usage(payload.context_window)
    cost_seg = format_cost(payload)

    line1_segs = filter(None, [model_seg, session_seg])
    line1 = DIVIDER_BAR.join(s.text for s in line1_segs) or None

    line2_segs = filter(None, [dir_seg, obsidian_seg])
    line2 = DIVIDER_BAR.join(s.text for s in line2_segs) or None

    line3_segs = filter(None, [git_seg, context_seg, cost_seg])
    line3 = DIVIDER_BAR.join(s.text for s in line3_segs) or None

    return [line for line in [line1, line2, line3] if line]
