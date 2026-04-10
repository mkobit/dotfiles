from dataclasses import dataclass
from pathlib import Path

from claude_statusline.models import ContextWindowInfo, GitInfo, StatusLineStdIn

# --- Terminal Colors & Styling ---
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

USE_ICONS = True
ICON_DIR = "\uf115" if USE_ICONS else "📁"
ICON_BRANCH = "\ue0a0" if USE_ICONS else ""
ICON_REMOTE = "\uf0c1" if USE_ICONS else "🔗"
ICON_DIRTY = "\uf06a" if USE_ICONS else "!"
ICON_CLEAN = "\uf00c" if USE_ICONS else "✓"
ICON_STAGED = "\uf067" if USE_ICONS else "+"
ICON_UNTRACKED = "\uf128" if USE_ICONS else "?"
ICON_TIMER = "\uf017" if USE_ICONS else "⏱"
ICON_COST = "💳" if USE_ICONS else "💳"
ICON_TOKENS = "\uf4a5" if USE_ICONS else "⚡"
ICON_ROBOT = "\uf544" if USE_ICONS else "🤖"
ICON_WORKTREE = "\uf1bb" if USE_ICONS else "🌳"

BLOCK_FILLED = "\u2588"  # █
BLOCK_EMPTY = "\u2591"  # ░
DIVIDER_DOT = " • "
DIVIDER_BAR = " │ "


@dataclass
class Segment:
    text: str


def format_context_usage(cw: ContextWindowInfo) -> Segment | None:
    """Formats the context usage with a block-based progress bar and token stats."""
    used_pct = cw.used_percentage or 0.0

    color = GREEN
    if used_pct >= 90:
        color = RED
    elif used_pct >= 50:
        color = YELLOW

    width = 10
    filled = min(int(width * (used_pct / 100)), width)
    visual_bar = (BLOCK_FILLED * filled) + (BLOCK_EMPTY * (width - filled))

    return Segment(f"{DIM}ctx:{RESET} {color}{visual_bar}{RESET} {int(used_pct)}%")


def format_model_info(payload: StatusLineStdIn) -> Segment | None:
    parts = [
        f"{ICON_ROBOT} {BLUE}{BOLD}{payload.model.display_name}{RESET}",
        f"{MAGENTA}@{payload.agent.name}{RESET}" if payload.agent.name else None,
    ]
    return Segment(" ".join(filter(None, parts)))


def format_session_info(payload: StatusLineStdIn) -> Segment | None:
    parts = []
    if payload.session_name:
        parts.append(f"{CYAN}#{payload.session_name}{RESET}")
    elif payload.session_id:
        parts.append(f"{DIM}#{payload.session_id[:8]}{RESET}")

    if payload.cost.total_duration_ms:
        elapsed_seconds = payload.cost.total_duration_ms // 1000
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            timer = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            timer = f"{minutes:02d}:{seconds:02d}"

        parts.append(f"{YELLOW}{ICON_TIMER} {timer}{RESET}")

    if not parts:
        return None
    return Segment(" ".join(parts))


def format_cost(payload: StatusLineStdIn) -> Segment | None:
    if not payload.cost.total_cost_usd:
        return None
    return Segment(f"{GREEN}{ICON_COST}{payload.cost.total_cost_usd:.2f}{RESET}")


def shorten_path(path: Path) -> str:
    """Shortens the path for display (e.g. ~/projects/foo -> .../projects/foo)."""
    try:
        rel_path = path.relative_to(Path.home())
        parts = list(rel_path.parts)
        if len(parts) > 3:
            return f".../{parts[-2]}/{parts[-1]}"
        if str(rel_path) == ".":
            return "~"
        return f"~/{rel_path}"
    except ValueError:
        parts = list(path.parts)
        if len(parts) > 3:
            return f".../{parts[-2]}/{parts[-1]}"
        return str(path)


def format_directory(cwd: Path) -> Segment | None:
    display_path = shorten_path(cwd)
    cwd_link = f"\033]8;;file://{cwd}\033\\{display_path}\033]8;;\033\\"
    return Segment(f"{BLUE}{ICON_DIR} {cwd_link}{RESET}")


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
