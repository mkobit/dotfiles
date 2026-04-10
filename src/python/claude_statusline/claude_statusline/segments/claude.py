from claude_statusline.models import ContextWindowInfo, StatusLineStdIn
from claude_statusline.segments.constants import (
    BLOCK_EMPTY,
    BLOCK_FILLED,
    BLUE,
    BOLD,
    CYAN,
    DIM,
    GREEN,
    ICON_COST,
    ICON_ROBOT,
    ICON_TIMER,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    Segment,
)


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
