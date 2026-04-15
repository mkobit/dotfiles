from claude_statusline.models import (
    ContextWindowInfo,
    Segment,
    SegmentGenerationResult,
    StatusLineStdIn,
)
from claude_statusline.segments.constants import (
    BG_DIM,
    BG_RESET,
    BLUE,
    BOLD,
    BRIGHT_GREEN,
    BRIGHT_RED,
    CYAN,
    DIM,
    GREEN,
    MAGENTA,
    ORANGE,
    RED,
    RESET,
    YELLOW,
    get_icon,
)


def format_tokens(tokens: int, max_tokens: int = 0) -> str:
    if max_tokens >= 1_000_000 or max_tokens >= 100_000:
        width = 4
    elif max_tokens >= 10_000:
        width = 3
    else:
        width = 5

    val = str(tokens) if tokens < 1000 else f"{tokens / 1000:.1f}k".replace(".0k", "k")
    return f"{val:>{width}}"


def format_context_usage(cw: ContextWindowInfo) -> SegmentGenerationResult | None:
    """Formats the context usage with a block-based progress bar and token stats."""
    used_pct = cw.used_percentage or 0.0

    color = GREEN
    if used_pct >= 90:
        color = RED
    elif used_pct >= 75:
        color = ORANGE
    elif used_pct >= 50:
        color = YELLOW

    width = 8
    blocks = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]

    total_eighths = int((used_pct / 100.0) * width * 8)
    full_blocks = total_eighths // 8
    remainder = total_eighths % 8

    visual_bar = "".join(
        f"{color}{BG_DIM}{blocks[8]}{BG_RESET}{RESET}"
        if i < full_blocks
        else f"{color}{BG_DIM}{blocks[remainder]}{BG_RESET}{RESET}"
        if i == full_blocks and remainder > 0
        else f"{color}{BG_DIM}{blocks[0]}{BG_RESET}{RESET}"
        for i in range(width)
    )

    total_used = (cw.total_input_tokens or 0) + (cw.total_output_tokens or 0)
    window_size = cw.context_window_size or 0

    token_str = None
    if window_size > 0:
        used_str = format_tokens(total_used, window_size)
        window_str = format_tokens(window_size, window_size).strip()
        token_str = f"{DIM}{used_str}/{window_str}{RESET}"

    parts = [
        f"{DIM}ctx:{RESET}",
        visual_bar,
        token_str,
        f"{color}{int(used_pct):>3}%{RESET}",
    ]

    return SegmentGenerationResult(
        line=2,
        index=10,
        generator="internal.claude",
        segment=Segment(text=" ".join(filter(None, parts))),
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

    if payload.output_style and payload.output_style.name:
        # e.g., default, concise, quiet
        parts.append(f"{DIM}[{payload.output_style.name}]{RESET}")

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


def format_lines_impact(payload: StatusLineStdIn) -> SegmentGenerationResult | None:
    added = payload.cost.total_lines_added or 0
    removed = payload.cost.total_lines_removed or 0

    if added == 0 and removed == 0:
        return None

    parts = [
        f"{BRIGHT_GREEN}+{added}{RESET}" if added > 0 else None,
        f"{BRIGHT_RED}-{removed}{RESET}" if removed > 0 else None,
    ]

    return SegmentGenerationResult(
        line=2,
        index=30,
        generator="internal.claude",
        segment=Segment(text=" ".join(filter(None, parts))),
    )
