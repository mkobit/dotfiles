from claude_statusline.models import (
    ContextWindowInfo,
    Segment,
    SegmentGenerationResult,
    StatusLineStdIn,
)
from claude_statusline.segments.constants import (
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
    get_battery_icon,
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
    """Formats context usage as a battery icon with remaining % and token counts."""
    used_pct = cw.used_percentage or 0.0
    remaining_pct = 100.0 - used_pct

    color = (
        BRIGHT_GREEN if remaining_pct >= 85
        else GREEN if remaining_pct >= 70
        else YELLOW if remaining_pct >= 55
        else ORANGE if remaining_pct >= 30
        else RED
    )

    battery = get_battery_icon(remaining_pct)
    pct_str = f"{color}{battery} {int(remaining_pct)}%{RESET}"

    total_used = (cw.total_input_tokens or 0) + (cw.total_output_tokens or 0)
    window_size = cw.context_window_size or 0
    token_str = (
        f"{BLUE}{format_tokens(total_used, window_size).strip()}"
        f"/{format_tokens(window_size, window_size).strip()}{RESET}"
        if window_size > 0
        else None
    )

    dot = get_icon("dot")
    parts = [pct_str, f"{DIM}{dot}{RESET} {token_str}" if token_str else None]

    return SegmentGenerationResult(
        line=2,
        index=0,
        generator="internal.claude",
        segment=Segment(text=" ".join(filter(None, parts))),
    )


def format_model_info(payload: StatusLineStdIn) -> SegmentGenerationResult | None:
    style = payload.output_style
    parts = [
        f"{get_icon('robot')} {BLUE}{BOLD}{payload.model.display_name}{RESET}",
        f"{MAGENTA}@{payload.agent.name}{RESET}" if payload.agent.name else None,
        f"{DIM}[{style.name}]{RESET}" if style and style.name else None,
    ]
    return SegmentGenerationResult(
        line=0,
        index=0,
        generator="internal.claude",
        segment=Segment(text=" ".join(filter(None, parts))),
    )


def format_session_info(payload: StatusLineStdIn) -> SegmentGenerationResult | None:
    parts = [
        f"{CYAN}#{payload.session_name}{RESET}" if payload.session_name else None,
    ]

    if payload.cost.total_duration_ms:
        elapsed_seconds = payload.cost.total_duration_ms // 1000
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            timer = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            timer = f"{minutes:02d}:{seconds:02d}"

        parts.append(f"{YELLOW}{get_icon('timer')} {timer}{RESET}")

    filtered = [p for p in parts if p]
    if not filtered:
        return None
    return SegmentGenerationResult(
        line=0,
        index=10,
        generator="internal.claude",
        segment=Segment(text=" ".join(filtered)),
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
        line=1,
        index=30,
        generator="internal.claude",
        segment=Segment(text=" ".join(filter(None, parts))),
    )
