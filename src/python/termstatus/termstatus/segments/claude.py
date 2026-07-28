from termstatus.layout import Segment, SegmentGenerationResult
from termstatus.payload import (
    ContextWindowInfo,
    StatusLineStdIn,
)
from termstatus.segments.constants import (
    BLUE,
    BOLD,
    BRIGHT_GREEN,
    DIM,
    GREEN,
    MAGENTA,
    ORANGE,
    RED,
    RESET,
    YELLOW,
    get_icon,
)

_USAGE_LINE = 9
_CONTEXT_LINE = 10

_BAR_WIDTH = 12
_BAR_FILLED = "▰"
_BAR_EMPTY = "▱"


def _format_tokens_compact(tokens: int) -> str:
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.1f}M".replace(".0M", "M")
    if tokens >= 1000:
        return f"{tokens / 1000:.1f}k".replace(".0k", "k")
    return str(tokens)


def _context_color(remaining_pct: float) -> str:
    if remaining_pct >= 85:
        return BRIGHT_GREEN
    if remaining_pct >= 70:
        return GREEN
    if remaining_pct >= 55:
        return YELLOW
    if remaining_pct >= 30:
        return ORANGE
    return RED


def _make_bar(used_pct: float, color: str) -> str:
    filled_count = round((used_pct / 100.0) * _BAR_WIDTH)
    filled = _BAR_FILLED * filled_count
    empty = _BAR_EMPTY * (_BAR_WIDTH - filled_count)
    return f"{color}{filled}{DIM}{empty}{RESET}"


def format_context_usage(cw: ContextWindowInfo) -> list[SegmentGenerationResult]:
    """Formats context as a progress bar with percentage and token ratio."""
    used_pct = cw.used_percentage or 0.0
    remaining_pct = 100.0 - used_pct
    color = _context_color(remaining_pct)

    total_used = (cw.total_input_tokens or 0) + (cw.total_output_tokens or 0)
    window_size = cw.context_window_size or 0

    bar = _make_bar(used_pct, color)
    pct_text = f"{color}{int(remaining_pct)}%{RESET}"

    token_text = (
        f"{DIM}{_format_tokens_compact(total_used)}/{_format_tokens_compact(window_size)}{RESET}"
        if window_size > 0
        else ""
    )

    results = [
        SegmentGenerationResult(
            line=_CONTEXT_LINE, index=0, column=0, generator="internal.claude", segment=Segment(text=get_icon("tokens"))
        ),
        SegmentGenerationResult(
            line=_CONTEXT_LINE,
            index=30,
            column=1,
            generator="internal.claude",
            segment=Segment(text=f"{bar}  {pct_text}"),
        ),
    ]
    if token_text:
        results = [
            *results,
            SegmentGenerationResult(
                line=_CONTEXT_LINE, index=40, column=3, generator="internal.claude", segment=Segment(text=token_text)
            ),
        ]
    return results


def format_model_info(payload: StatusLineStdIn) -> list[SegmentGenerationResult]:
    style = payload.output_style
    results = [
        SegmentGenerationResult(
            line=0, index=0, column=0, generator="internal.claude", segment=Segment(text=get_icon("robot"))
        ),
        SegmentGenerationResult(
            line=0,
            index=0,
            column=1,
            generator="internal.claude",
            segment=Segment(text=f"{BLUE}{BOLD}{payload.model.display_name}{RESET}"),
        ),
    ]

    if payload.agent.name:
        results = [
            *results,
            SegmentGenerationResult(
                line=0,
                index=10,
                column=1,
                generator="internal.claude",
                segment=Segment(text=f"{MAGENTA}@{payload.agent.name}{RESET}"),
            ),
        ]
    if style and style.name:
        results = [
            *results,
            SegmentGenerationResult(
                line=0,
                index=0,
                column=2,
                generator="internal.claude",
                segment=Segment(text=f"{DIM}[{style.name}]{RESET}"),
            ),
        ]
    return results


def format_session_info(payload: StatusLineStdIn) -> list[SegmentGenerationResult]:
    if not payload.cost.total_duration_ms:
        return []

    elapsed_seconds = payload.cost.total_duration_ms // 1000
    hours, remainder = divmod(elapsed_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    timer = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
    return [
        SegmentGenerationResult(
            line=_USAGE_LINE,
            index=10,
            column=2,
            generator="internal.claude",
            segment=Segment(text=f"{DIM}{get_icon('timer')} {timer}{RESET}"),
        )
    ]


def format_cost(payload: StatusLineStdIn) -> list[SegmentGenerationResult]:
    if not payload.cost.total_cost_usd:
        return []
    return [
        SegmentGenerationResult(
            line=_USAGE_LINE, index=0, column=0, generator="internal.claude", segment=Segment(text=get_icon("cost"))
        ),
        SegmentGenerationResult(
            line=_USAGE_LINE,
            index=0,
            column=1,
            generator="internal.claude",
            segment=Segment(text=f"{GREEN}${payload.cost.total_cost_usd:.2f}{RESET}"),
        ),
    ]
