import math
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from re import Pattern
from typing import Final

from whenever import TimeDelta

from termstatus.agy.protocol import AgyPayload, Quota
from termstatus.agy.term_colors import (
    _STATE_COLORS,
    fullness_icon,
    get_icon,
    meter_color,
    state_icon,
)
from termstatus.git_status import VcsState
from termstatus.segments.constants import (
    BLUE,
    BOLD,
    CYAN,
    DARK_GREY,
    DIM,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    SKY_BLUE,
    YELLOW,
    use_icons,
)
from termstatus.terminal_text import normalized_text

_ANSI_ESCAPE: Final[Pattern[str]] = re.compile(r"(?:\x1b\[[0-9;]*m|\x1b]8;;.*?(?:\x1b\\|\x07))")


_GAP: Final[str] = "  "
_GAP_WIDTH: Final[int] = len(_GAP)


@dataclass(frozen=True, slots=True)
class _RowSpec:
    col0: str
    col1_items: tuple[str, ...] = ()
    col2_items: tuple[str, ...] = ()
    col1_overflow: bool = False


@dataclass(frozen=True, slots=True)
class _FittedRow:
    col0: str
    col1: str = ""
    col2: str = ""
    is_continuation: bool = False


def strip_ansi(value: str) -> str:
    return _ANSI_ESCAPE.sub("", value)


def display_width(value: str) -> int:
    return sum(
        0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
        for char in strip_ansi(value)
    )


def shorten_path(cwd: str) -> str:
    try:
        home = str(Path.home())
    except Exception:
        home = ""
    try:
        if home and cwd == home:
            return "~"
        if home and cwd.startswith(home + "/"):
            rel = cwd[len(home) + 1 :]
            parts = [p for p in rel.split("/") if p]
            if len(parts) > 3:
                return f".../{parts[-2]}/{parts[-1]}"
            return f"~/{rel}"
        parts = [p for p in cwd.split("/") if p]
        if len(parts) > 3:
            return f".../{parts[-2]}/{parts[-1]}"
        return cwd
    except Exception:
        return cwd


def _format_meter(remaining: int) -> str:
    return f"{remaining}%"


def _format_cost(cost: float) -> str:
    try:
        if not math.isfinite(cost):
            return "$0.00"
        if cost < 0.001:
            return "<$0.001" if cost > 0 else "$0.00"
        return f"${cost:.3f}" if cost < 0.0095 else f"${cost:.2f}"
    except TypeError, ValueError:
        return "$0.00"


def _model_name(model: str | None, effort: str | None) -> str | None:
    return (
        re.sub(rf"\s*\({re.escape(effort)}\)$", "", model, flags=re.IGNORECASE)
        if model is not None and effort is not None
        else model
    )


def _github_url(remote: str | None) -> str | None:
    if remote is None:
        return None
    match = re.fullmatch(
        r"(?:git@github\.com:|ssh://git@github\.com/|https?://github\.com/|git://github\.com/)([^/:\s]+/[^/\s]+?)(?:\.git)?/?",
        remote.strip(),
    )
    return f"https://github.com/{match.group(1)}" if match else None


def git_branch(vcs: VcsState) -> str | None:
    if not vcs.is_repo:
        return None
    url = _github_url(vcs.origin_url)
    if (branch := normalized_text(vcs.branch)) is not None:
        branch_link = f"\033]8;;{url}\033\\{branch}\033]8;;\033\\" if url is not None else branch
        branch_icon = get_icon("branch")
        icon_prefix = f"{branch_icon} " if branch_icon else ""

        if (upstream := normalized_text(vcs.upstream)) is not None:
            remote_link = f"\033]8;;{url}\033\\{upstream}\033]8;;\033\\" if url is not None else upstream
            pair_text = (
                f"{DIM}<{RESET}{MAGENTA}{branch_link}{RESET} {DIM}→{RESET} {CYAN}{remote_link}{RESET}{DIM}>{RESET}"
            )
        else:
            pair_text = f"{MAGENTA}{branch_link}{RESET}"
    else:
        detached_icon = get_icon("detached")
        icon_prefix = f"{detached_icon} " if detached_icon else ""
        if (commit := normalized_text(vcs.commit)) is not None:
            short_hash = commit[:7]
            commit_url = f"{url}/commit/{commit}" if url is not None else None
            linked_hash = (
                f"\033]8;;{commit_url}\033\\{short_hash}\033]8;;\033\\" if commit_url is not None else short_hash
            )
            pair_text = f"{YELLOW}(detached@{linked_hash}){RESET}"
        else:
            pair_text = f"{YELLOW}(detached){RESET}"

    status_items: list[str] = []
    if vcs.rebase:
        status_items.append(f"{YELLOW}REBASE{RESET}")
    if vcs.dirty or vcs.staged:
        status_items.append(f"{YELLOW}!{RESET}")
    if vcs.untracked:
        status_items.append(f"{CYAN}?{RESET}")
    if vcs.ahead:
        status_items.append(f"{CYAN}↑{vcs.ahead}{RESET}")
    if vcs.behind:
        status_items.append(f"{RED}↓{vcs.behind}{RESET}")
    if not status_items:
        clean_icon = get_icon("clean") or "✓"
        status_items.append(f"{GREEN}{clean_icon}{RESET}")

    bracketed = f" {DIM}[{RESET}{' '.join(status_items)}{DIM}]{RESET}"
    return f"{icon_prefix}{pair_text}{bracketed}"


_THINK_LEVELS: Final[dict[str, int]] = {
    "off": 0,
    "none": 0,
    "low": 1,
    "medium": 2,
    "med": 2,
    "high": 3,
    "xhigh": 4,
    "max": 5,
}

_CELL_BARS: Final[tuple[str, ...]] = ("▁", "▂", "▄", "▆", "█")


def _thinking_cellular_graph(effort: str | None) -> str:
    if effort is None:
        return ""
    low = effort.lower().strip()
    if low in _THINK_LEVELS:
        lvl = _THINK_LEVELS[low]
    elif low.isdigit():
        lvl = max(0, min(len(_CELL_BARS), int(low)))
    else:
        return ""
    bars = [f"{CYAN}{bar}{RESET}" if idx < lvl else f"{DARK_GREY}{bar}{RESET}" for idx, bar in enumerate(_CELL_BARS)]
    return "".join(bars)


_VIM_MODES: Final[dict[str, tuple[str, str]]] = {
    "insert": ("I", GREEN),
    "i": ("I", GREEN),
    "normal": ("N", CYAN),
    "n": ("N", CYAN),
    "visual": ("V", MAGENTA),
    "v": ("V", MAGENTA),
    "v-line": ("V", MAGENTA),
    "v-block": ("V", MAGENTA),
    "replace": ("R", RED),
    "r": ("R", RED),
    "command": ("C", YELLOW),
    "c": ("C", YELLOW),
}


def _format_vim_mode(vim_mode: str | None) -> str | None:
    if vim_mode is None:
        return None
    key = vim_mode.strip().lower()
    if not key:
        return None
    char, color = _VIM_MODES.get(key, (key[0].upper(), DIM))
    vim_icon = get_icon("vim")
    return f"{color}{vim_icon}{char}{RESET}"


def _agent_row(payload: AgyPayload) -> _RowSpec:
    icon = state_icon(payload.state)
    icon_prefix = f"{icon} " if icon else ""
    color = _STATE_COLORS.get(payload.state, "\033[37m")
    state = f"{color}[{icon_prefix}{payload.state}]{RESET}"
    vim_badge = _format_vim_mode(payload.vim_mode)
    col0 = f"{state} {vim_badge}" if vim_badge is not None else state

    model = _model_name(payload.model, payload.effort)
    model_text = f"{BOLD}{model}{RESET}" if model is not None else None
    brain = "🧠 " if use_icons() else ""
    cellular = _thinking_cellular_graph(payload.effort)
    graph = f"{cellular} " if use_icons() and cellular else ""
    think_text = f"{brain}{graph}{payload.effort}" if payload.effort is not None else None

    mode_text = f"{DIM}{payload.execution_mode}{RESET}" if payload.execution_mode is not None else None

    sandbox_text = None
    if payload.sandbox and payload.sandbox.enabled:
        net_mode = "net" if payload.sandbox.allow_network else "no-net"
        sandbox_text = f"{DIM}sandbox:{RESET}{net_mode}"

    col1 = tuple(item for item in (model_text, think_text) if item is not None)
    col2 = tuple(item for item in (mode_text, sandbox_text) if item is not None)
    return _RowSpec(col0=col0, col1_items=col1, col2_items=col2)


def _format_directory(cwd: str) -> str:
    short_path = shorten_path(cwd)
    link = f"\033]8;;file://{cwd}\033\\{short_path}\033]8;;\033\\"
    icon = get_icon("dir")
    icon_prefix = f"{icon} " if icon else ""
    return f"{SKY_BLUE}{icon_prefix}{link}{RESET}"


def _format_quota_label(name: str, *, disambiguate: bool = False) -> str | None:
    low = name.lower()
    if low.startswith(("3p-", "3p_", "3p:")):
        return None
    remaining = name
    matched_prefix = ""
    for prefix in ("gemini-", "codex-"):
        if remaining.lower().startswith(prefix):
            matched_prefix = prefix
            remaining = remaining[len(prefix) :]
            break
    rem_low = remaining.lower()
    if rem_low == "5h":
        return f"{matched_prefix}{remaining}" if disambiguate and matched_prefix else remaining
    if rem_low in {"weekly", "7d"}:
        base = "7d"
        return f"{matched_prefix}{base}" if disambiguate and matched_prefix else base
    if rem_low.endswith(("-weekly", "-7d")):
        stem = remaining[: -len("-weekly")] if rem_low.endswith("-weekly") else remaining[: -len("-7d")]
        return f"{stem}-7d"
    if not rem_low.endswith("-5h") and "-" in remaining:
        return remaining.split("-", 1)[1]
    return remaining


def _quota_interval(name: str) -> str | None:
    low = name.lower()
    if low == "5h" or low.endswith(("-5h", "_5h", ":5h")):
        return "5h"
    if low in {"weekly", "7d"} or low.endswith(("-weekly", "-7d", "_weekly", "_7d")):
        return "7d"
    return None


def _format_quota_reset_duration(reset_in: TimeDelta | None) -> str | None:
    if reset_in is None or reset_in.total("seconds") <= 0:
        return None
    total_seconds = int(reset_in.total("seconds"))
    days = total_seconds // 86400
    remainder = total_seconds % 86400
    hours = remainder // 3600
    minutes = (remainder % 3600) // 60
    if total_seconds > 0 and days == 0 and hours == 0 and minutes == 0:
        minutes = 1
    parts: list[str] = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or (days > 0 and minutes > 0):
        parts.append(f"{hours}h")
    if minutes > 0 or not parts:
        parts.append(f"{minutes}m")
    duration = " ".join(parts)
    icon = "⏳ " if use_icons() else ""
    formatted = f"{icon}{duration}"
    if total_seconds <= 1800:
        return f"{CYAN}{formatted}{RESET}"
    return f"{DIM}{formatted}{RESET}"


def _format_quota_badge(name: str, quota: Quota, base_label: str, *, is_ambiguous: bool) -> str:
    label = _format_quota_label(name, disambiguate=is_ambiguous)
    color = meter_color(quota.remaining)
    icon = fullness_icon(quota.remaining)
    meter = _format_meter(quota.remaining)
    icon_text = f" {icon}" if use_icons() else ""
    reset_str = _format_quota_reset_duration(quota.reset_in)
    reset_text = f" {reset_str}" if reset_str is not None else ""
    return f"{DIM}[{RESET}{color}{label}{icon_text} {meter}{RESET}{reset_text}{DIM}]{RESET}"


def _ordered_quota_badges(payload: AgyPayload) -> list[str]:
    five_hour: list[tuple[str, str, str | None]] = []
    other: list[tuple[str, str, str | None]] = []
    for name in payload.quotas:
        base_label = _format_quota_label(name)
        if base_label is None:
            continue
        interval = _quota_interval(name)
        entry = (name, base_label, interval)
        if interval == "5h":
            five_hour.append(entry)
        else:
            other.append(entry)

    ordered = five_hour + other
    interval_counts: dict[str, int] = {}
    for _, _, interval in ordered:
        if interval is not None:
            interval_counts[interval] = interval_counts.get(interval, 0) + 1

    badges: list[str] = []
    for name, base_label, interval in ordered:
        quota = payload.quotas[name]
        is_ambiguous = bool(interval and interval_counts.get(interval, 0) > 1 and base_label == interval)
        badges.append(_format_quota_badge(name, quota, base_label, is_ambiguous=is_ambiguous))
    return badges


def _workspace_row(payload: AgyPayload, vcs: VcsState | None) -> _RowSpec | None:
    dir_text = _format_directory(payload.cwd) if payload.cwd is not None else None
    effective_vcs = vcs or payload.vcs
    vcs_text = git_branch(effective_vcs) if effective_vcs and effective_vcs.is_repo else None
    if dir_text is not None and vcs_text is not None:
        return _RowSpec(col0=dir_text, col1_items=(vcs_text,))
    if dir_text is not None:
        return _RowSpec(col0=dir_text)
    if vcs_text is not None:
        return _RowSpec(col0=vcs_text)
    return None


def _usage_row(payload: AgyPayload) -> _RowSpec | None:
    ctx_text = None
    if payload.remaining_context is not None:
        color = meter_color(payload.remaining_context)
        icon = fullness_icon(payload.remaining_context)
        ctx_text = f"{color}{icon} {_format_meter(payload.remaining_context)} ctx{RESET}"

    quota_badges = _ordered_quota_badges(payload)
    cost_text = f"{DIM}{_format_cost(payload.cost)}{RESET}" if payload.cost is not None else None
    plan_text = f"{DIM}{payload.plan_tier}{RESET}" if payload.plan_tier is not None else None
    col2_items = tuple(item for item in (cost_text, plan_text) if item is not None)

    if ctx_text is not None:
        return _RowSpec(
            col0=ctx_text,
            col1_items=tuple(quota_badges),
            col2_items=col2_items,
            col1_overflow=True,
        )
    if quota_badges:
        return _RowSpec(
            col0=quota_badges[0],
            col1_items=tuple(quota_badges[1:]),
            col2_items=col2_items,
            col1_overflow=True,
        )
    if col2_items:
        return _RowSpec(col0=col2_items[0], col1_items=col2_items[1:])
    return None


def _activity_row(payload: AgyPayload) -> _RowSpec | None:
    items = [
        text
        for text in (
            f"{BOLD}{RED}confirm{RESET}" if payload.confirmation_pending else None,
            f"{CYAN}tasks:{payload.task_count}{RESET}" if payload.task_count is not None else None,
            f"{YELLOW}input:{payload.pending_input_count}{RESET}" if payload.pending_input_count is not None else None,
            f"{BLUE}artifacts:{payload.artifact_count}{RESET}" if payload.artifact_count is not None else None,
        )
        if text is not None
    ]
    if not items:
        return None
    return _RowSpec(col0=items[0], col1_items=tuple(items[1:]))


def _fit_items(items: Sequence[str], max_width: int) -> tuple[list[str], list[str]]:
    fitted: list[str] = []
    used = 0
    for idx, item in enumerate(items):
        item_width = display_width(item)
        needed = item_width if not fitted else used + _GAP_WIDTH + item_width
        if needed <= max_width:
            fitted.append(item)
            used = needed
        else:
            return fitted, list(items[idx:])
    return fitted, []


def _fit_row_spec(spec: _RowSpec, width: int) -> list[_FittedRow]:
    col0_w = display_width(spec.col0)
    remaining_after_col0 = width - col0_w - _GAP_WIDTH

    col1_fitted: list[str] = []
    col1_leftover: list[str] = list(spec.col1_items)
    if spec.col1_items and remaining_after_col0 > 0:
        col1_fitted, col1_leftover = _fit_items(spec.col1_items, remaining_after_col0)

    col1_str = _GAP.join(col1_fitted)
    col1_w = display_width(col1_str)

    col2_fitted: list[str] = []
    if spec.col2_items and not col1_leftover:
        remaining_after_col1 = width - col0_w - _GAP_WIDTH - col1_w - _GAP_WIDTH if col1_str else remaining_after_col0
        if remaining_after_col1 > 0:
            col2_fitted, _ = _fit_items(spec.col2_items, remaining_after_col1)

    col2_str = _GAP.join(col2_fitted)
    if not col1_str and col2_str:
        col1_str, col2_str = col2_str, ""

    rows = [_FittedRow(col0=spec.col0, col1=col1_str, col2=col2_str)]

    if spec.col1_overflow and col1_leftover:
        overflow_fitted, _ = _fit_items(col1_leftover, width)
        if overflow_fitted:
            rows.append(_FittedRow(col0="", col1=_GAP.join(overflow_fitted), is_continuation=True))

    return rows


def _render_table(specs: Sequence[_RowSpec], width: int) -> str:
    fitted_rows = [row for spec in specs for row in _fit_row_spec(spec, width)]

    col0_cap = max(16, width // 3)
    col0_candidates = [
        display_width(row.col0)
        for row in fitted_rows
        if not row.is_continuation and (row.col1 or row.col2) and display_width(row.col0) <= col0_cap
    ]
    col0_width = max(col0_candidates, default=0)

    col0_ends: list[int] = []
    for row in fitted_rows:
        if row.is_continuation:
            col1_w = display_width(row.col1)
            if col0_width > 0 and col0_width + _GAP_WIDTH + col1_w <= width:
                col0_ends.append(col0_width)
            else:
                col0_ends.append(-_GAP_WIDTH)
        elif not row.col1 and not row.col2:
            col0_ends.append(display_width(row.col0))
        else:
            raw_col0_w = display_width(row.col0)
            rest_w = _GAP_WIDTH + display_width(row.col1) + (_GAP_WIDTH + display_width(row.col2) if row.col2 else 0)
            if raw_col0_w <= col0_width and col0_width + rest_w <= width:
                col0_ends.append(col0_width)
            else:
                col0_ends.append(raw_col0_w)

    target_col2_start = max(
        (
            col0_ends[idx] + _GAP_WIDTH + display_width(row.col1) + _GAP_WIDTH
            for idx, row in enumerate(fitted_rows)
            if row.col2
        ),
        default=0,
    )

    lines: list[str] = []
    for idx, row in enumerate(fitted_rows):
        if row.is_continuation:
            indent = col0_ends[idx] + _GAP_WIDTH
            lines.append(f"{' ' * indent}{row.col1}" if indent > 0 else row.col1)
            continue
        if not row.col1:
            lines.append(row.col0)
            continue

        pad0 = " " * (col0_ends[idx] - display_width(row.col0) + _GAP_WIDTH)
        if not row.col2:
            lines.append(f"{row.col0}{pad0}{row.col1}")
            continue

        natural_col2_start = col0_ends[idx] + _GAP_WIDTH + display_width(row.col1) + _GAP_WIDTH
        col2_w = display_width(row.col2)
        if target_col2_start >= natural_col2_start and target_col2_start + col2_w <= width:
            pad1 = " " * (target_col2_start - natural_col2_start + _GAP_WIDTH)
        else:
            pad1 = _GAP
        lines.append(f"{row.col0}{pad0}{row.col1}{pad1}{row.col2}")

    return "\n".join(lines)


def render_statusline(payload: AgyPayload, vcs: VcsState | None) -> str:
    specs = [
        row
        for row in (
            _agent_row(payload),
            _workspace_row(payload, vcs),
            _usage_row(payload),
            _activity_row(payload),
        )
        if row is not None
    ]
    return _render_table(specs, payload.terminal_width)
