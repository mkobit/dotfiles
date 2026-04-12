from claude_statusline.models import (
    ContextWindowInfo,
    Segment,
    SegmentGenerationResult,
    StatusLineStdIn,
)
from claude_statusline.segments.constants import (
    BLUE,
    BOLD,
    CYAN,
    DIM,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    get_icon,
)


def format_context_usage(cw: ContextWindowInfo) -> SegmentGenerationResult | None:
    """Formats the context usage with a block-based progress bar and token stats."""
    used_pct = cw.used_percentage or 0.0

    color = GREEN
    if used_pct >= 90:
        color = RED
    elif used_pct >= 50:
        color = YELLOW

    width = 10
    blocks = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

    total_eighths = int((used_pct / 100.0) * width * 8)
    full_blocks = total_eighths // 8
    remainder = total_eighths % 8

    visual_bar = "".join(
        blocks[8]
        if i < full_blocks
        else blocks[remainder]
        if i == full_blocks
        else blocks[0]
        for i in range(width)
    )

    return SegmentGenerationResult(
        line=2,
        index=10,
        generator="internal.claude",
        segment=Segment(
            text=f"{DIM}ctx:{RESET} {color}{visual_bar}{RESET} {int(used_pct)}%"
        ),
    )


def format_model_info(payload: StatusLineStdIn) -> SegmentGenerationResult | None:
    parts = [
        f"{get_icon('robot')} {BLUE}{BOLD}{payload.model.display_name}{RESET}",
        f"{MAGENTA}@{payload.agent.name}{RESET}" if payload.agent.name else None,
    ]
    return SegmentGenerationResult(
        line=0,
        index=0,
        generator="internal.claude",
        segment=Segment(text=" ".join(filter(None, parts))),
    )


def format_session_info(payload: StatusLineStdIn) -> SegmentGenerationResult | None:
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

        parts.append(f"{YELLOW}{get_icon('timer')} {timer}{RESET}")

    if not parts:
        return None
    return SegmentGenerationResult(
        line=0,
        index=10,
        generator="internal.claude",
        segment=Segment(text=" ".join(parts)),
    )


def format_cost(payload: StatusLineStdIn) -> SegmentGenerationResult | None:
    if not payload.cost.total_cost_usd:
        return None
    return SegmentGenerationResult(
        line=2,
        index=20,
        generator="internal.claude",
        segment=Segment(
            text=f"{GREEN}{get_icon('cost')} ${payload.cost.total_cost_usd:.2f}{RESET}"
        ),
    )
