from claude_statusline.models import GitInfo
from claude_statusline.segments.constants import (
    CYAN,
    GREEN,
    ICON_BRANCH,
    ICON_CLEAN,
    ICON_DIRTY,
    ICON_REMOTE,
    ICON_STAGED,
    ICON_UNTRACKED,
    ICON_WORKTREE,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    Segment,
)


def format_git_full(info: GitInfo | None) -> Segment | None:
    if not info:
        return None

    branch_icon = ICON_WORKTREE if info.is_worktree else ICON_BRANCH
    parts = [f"{MAGENTA}{branch_icon} {info.branch}{RESET}"]

    status_parts = []
    if info.dirty:
        status_parts.append(f"{RED}{ICON_DIRTY}{RESET}")
    if info.staged:
        status_parts.append(f"{YELLOW}{ICON_STAGED}{RESET}")
    if info.untracked:
        status_parts.append(f"{CYAN}{ICON_UNTRACKED}{RESET}")

    if not status_parts:
        status_parts.append(f"{GREEN}{ICON_CLEAN}{RESET}")

    parts.append("".join(status_parts))

    if info.ahead > 0:
        parts.append(f"{GREEN}↑{info.ahead}{RESET}")
    if info.behind > 0:
        parts.append(f"{RED}↓{info.behind}{RESET}")

    if info.remote:
        parts.append(f"\033]8;;{info.remote}\033\\{ICON_REMOTE}\033]8;;\033\\")

    return Segment(" ".join(parts))
