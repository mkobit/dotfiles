from claude_statusline.models import GitInfo, Segment, SegmentGenerationResult
from claude_statusline.segments.constants import (
    CYAN,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    get_icon,
)


def format_git_full(info: GitInfo | None) -> SegmentGenerationResult | None:
    if not info:
        return None

    branch_icon = get_icon("worktree") if info.is_worktree else get_icon("branch")
    parts = [f"{MAGENTA}{branch_icon} {info.branch}{RESET}"]

    status_parts = []
    if info.dirty:
        status_parts.append(f"{RED}{get_icon('dirty')}{RESET}")
    if info.staged:
        status_parts.append(f"{YELLOW}{get_icon('staged')}{RESET}")
    if info.untracked:
        status_parts.append(f"{CYAN}{get_icon('untracked')}{RESET}")

    if not status_parts:
        status_parts.append(f"{GREEN}{get_icon('clean')}{RESET}")

    parts.append("".join(status_parts))

    if info.ahead > 0:
        parts.append(f"{GREEN}↑{info.ahead}{RESET}")
    if info.behind > 0:
        parts.append(f"{RED}↓{info.behind}{RESET}")

    if info.remote:
        parts.append(f"\033]8;;{info.remote}\033\\{get_icon('remote')}\033]8;;\033\\")

    return SegmentGenerationResult(
        line=3, index=0, segment=Segment(text=" ".join(parts))
    )
