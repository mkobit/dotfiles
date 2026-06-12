from termstatus.layout import Segment, SegmentGenerationResult
from termstatus.payload import (
    ContextWindowInfo,
    StatusLineStdIn,
)
from termstatus.segments.constants import (
    BLUE,
    BOLD,
    BRIGHT_GREEN,
    BRIGHT_RED,
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


def format_context_usage(cw: ContextWindowInfo) -> list[SegmentGenerationResult]:
    """Formats context usage as a battery icon with remaining % and token counts."""
    used_pct = cw.used_percentage or 0.0
    remaining_pct = 100.0 - used_pct

    color = (
        BRIGHT_GREEN
        if remaining_pct >= 85
        else GREEN
        if remaining_pct >= 70
        else YELLOW
        if remaining_pct >= 55
        else ORANGE
        if remaining_pct >= 30
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

    results = []
    if pct_str:
        results.append(
            SegmentGenerationResult(
                line=2, index=0, column=0, generator="internal.claude", segment=Segment(text=pct_str)
            )
        )
    if token_str:
        results.append(
            SegmentGenerationResult(
                line=2,
                index=10,
                column=1,
                generator="internal.claude",
                segment=Segment(text=f"{DIM}{dot}{RESET} {token_str}"),
            )
        )
    return results


def format_model_info(payload: StatusLineStdIn) -> list[SegmentGenerationResult]:
    style = payload.output_style
    results = []
    model_str = f"{get_icon('robot')} {BLUE}{BOLD}{payload.model.display_name}{RESET}"
    results.append(
        SegmentGenerationResult(line=0, index=0, column=0, generator="internal.claude", segment=Segment(text=model_str))
    )

    agent_style_parts = []
    if payload.agent.name:
        agent_style_parts.append(f"{MAGENTA}@{payload.agent.name}{RESET}")
    if style and style.name:
        agent_style_parts.append(f"{DIM}[{style.name}]{RESET}")

    if agent_style_parts:
        results.append(
            SegmentGenerationResult(
                line=0,
                index=10,
                column=1,
                generator="internal.claude",
                segment=Segment(text=" ".join(agent_style_parts)),
            )
        )
    return results


def format_session_info(payload: StatusLineStdIn) -> list[SegmentGenerationResult]:
    results = []

    if payload.cost.total_duration_ms:
        elapsed_seconds = payload.cost.total_duration_ms // 1000
        hours, remainder = divmod(elapsed_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        timer = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
        results.append(
            SegmentGenerationResult(
                line=0,
                index=10,
                column=4,
                generator="internal.claude",
                segment=Segment(text=f"{YELLOW}{get_icon('timer')} {timer}{RESET}"),
            )
        )

    return results


def format_cost(payload: StatusLineStdIn) -> list[SegmentGenerationResult]:
    if not payload.cost.total_cost_usd:
        return []
    return [
        SegmentGenerationResult(
            line=2,
            index=20,
            column=4,
            generator="internal.claude",
            segment=Segment(text=f"{GREEN}{get_icon('cost')} ${payload.cost.total_cost_usd:.2f}{RESET}"),
        )
    ]


def format_lines_impact(payload: StatusLineStdIn) -> list[SegmentGenerationResult]:
    added = payload.cost.total_lines_added or 0
    removed = payload.cost.total_lines_removed or 0

    if added == 0 and removed == 0:
        return []

    parts = [
        f"{BRIGHT_GREEN}+{added}{RESET}" if added > 0 else None,
        f"{BRIGHT_RED}-{removed}{RESET}" if removed > 0 else None,
    ]

    return [
        SegmentGenerationResult(
            line=1,
            index=30,
            column=4,
            generator="internal.claude",
            segment=Segment(text=" ".join(filter(None, parts))),
        )
    ]
