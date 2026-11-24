import math
import re
import unicodedata
from collections.abc import Sequence
from pathlib import Path
from re import Pattern
from typing import Final

from rich.console import Console, Group, RenderableType
from rich.table import Table
from rich.text import Text
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

_ANSI_ESCAPE: Final[Pattern[str]] = re.compile(r"(?:\x1b\[[0-9;]*m|\x1b]8;[^;]*;.*?(?:\x1b\\|\x07))")

_GAP_WIDTH: Final[int] = 2


def strip_ansi(value: str) -> str:
    return _ANSI_ESCAPE.sub("", value)


def display_width(value: str) -> int:
    return sum(
        0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
        for char in strip_ansi(value)
    )


def _fish_abbrev(segment: str) -> str:
    if segment.startswith(".") and len(segment) > 2:
        return segment[:2]
    return segment[:1]


def _join_path(prefix: str, parts: Sequence[str]) -> str:
    if prefix == "~":
        return f"~/{'/'.join(parts)}" if parts else "~"
    if prefix == "/":
        return f"/{'/'.join(parts)}" if parts else "/"
    return "/".join(parts)


def _shorten_parts(prefix: str, parts: Sequence[str], max_width: int | None) -> str:
    full = _join_path(prefix, parts)
    if max_width is None:
        return _join_path(prefix, ["…", parts[-2], parts[-1]]) if len(parts) > 3 else full

    if display_width(full) <= max_width:
        return full

    # Fish-style progressive shortening of leading segments while keeping trailing segments readable.
    for shorten_count in range(1, len(parts)):
        candidate = _join_path(prefix, [*(_fish_abbrev(p) for p in parts[:shorten_count]), *parts[shorten_count:]])
        if display_width(candidate) <= max_width:
            return candidate

    if len(parts) >= 3:
        two_leaf = _join_path(prefix, ["…", parts[-2], parts[-1]])
        return two_leaf if display_width(two_leaf) <= max_width else _join_path(prefix, ["…", parts[-1]])

    return _join_path(prefix, [_fish_abbrev(parts[0]), parts[1]]) if len(parts) == 2 else full


def shorten_path(cwd: str, max_width: int | None = None) -> str:
    try:
        home = str(Path.home())
    except Exception:
        home = ""
    try:
        if home and cwd == home:
            return "~"
        if home and cwd.startswith(home + "/"):
            prefix = "~"
            parts = [p for p in cwd[len(home) + 1 :].split("/") if p]
        elif cwd.startswith("/"):
            prefix = "/"
            parts = [p for p in cwd.split("/") if p]
        else:
            return cwd

        return _shorten_parts(prefix, parts, max_width) if parts else prefix
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
    icon_prefix = f"{vim_icon} " if vim_icon else ""
    return f"{color}{icon_prefix}{char}{RESET}"


def _format_directory(cwd: str, *, max_width: int | None = None) -> str:
    icon = get_icon("dir")
    icon_prefix = f"{icon} " if icon else ""
    path_budget = max(1, max_width - display_width(icon_prefix)) if max_width is not None else None
    short_path = shorten_path(cwd, max_width=path_budget)
    link = f"\033]8;;file://{cwd}\033\\{short_path}\033]8;;\033\\"
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


def _row_width(cells: Sequence[str], *, gap: int = _GAP_WIDTH) -> int:
    return sum(display_width(cell) for cell in cells) + gap * max(0, len(cells) - 1)


def _fit_row(cells: Sequence[str], max_width: int, *, gap: int = _GAP_WIDTH) -> list[str]:
    fitted = list(cells)
    while len(fitted) > 1 and _row_width(fitted, gap=gap) > max_width:
        fitted.pop()
    return fitted


def _grid_band(rows: Sequence[Sequence[str]], *, gap: int = _GAP_WIDTH) -> Table:
    col_count = max(len(row) for row in rows)
    grid = Table.grid(padding=(0, gap))
    for _ in range(col_count):
        grid.add_column(justify="left", no_wrap=True, overflow="ellipsis")
    for row in rows:
        padded = (*row, *("" for _ in range(col_count - len(row))))
        grid.add_row(
            *(Text.from_ansi(cell, no_wrap=True, overflow="ellipsis") if cell else Text("") for cell in padded)
        )
    return grid


def _harness_band(payload: AgyPayload, max_width: int) -> Table:
    icon = state_icon(payload.state)
    icon_prefix = f"{icon} " if icon else ""
    color = _STATE_COLORS.get(payload.state, "\033[37m")
    state = f"{color}[{icon_prefix}{payload.state}]{RESET}"
    vim_badge = _format_vim_mode(payload.vim_mode)
    lead = f"{state} {vim_badge}" if vim_badge is not None else state

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

    cells = [item for item in (lead, model_text, think_text, mode_text, sandbox_text) if item is not None]
    return _grid_band([_fit_row(cells, max_width)])


def _directory_band(payload: AgyPayload, max_width: int) -> Text | None:
    if payload.cwd is None:
        return None
    return Text.from_ansi(_format_directory(payload.cwd, max_width=max_width), no_wrap=True, overflow="ellipsis")


def _vcs_band(payload: AgyPayload, vcs: VcsState | None) -> Text | None:
    effective_vcs = vcs or payload.vcs
    vcs_text = git_branch(effective_vcs) if effective_vcs and effective_vcs.is_repo else None
    if vcs_text is None:
        return None
    return Text.from_ansi(vcs_text, no_wrap=True, overflow="ellipsis")


def _usage_band(payload: AgyPayload, max_width: int) -> Table | None:
    ctx_text = None
    if payload.remaining_context is not None:
        color = meter_color(payload.remaining_context)
        icon = fullness_icon(payload.remaining_context)
        ctx_text = f"{color}{icon} {_format_meter(payload.remaining_context)} ctx{RESET}"

    quota_badges = _ordered_quota_badges(payload)
    cost_text = f"{DIM}{_format_cost(payload.cost)}{RESET}" if payload.cost is not None else None
    plan_text = f"{DIM}{payload.plan_tier}{RESET}" if payload.plan_tier is not None else None

    items = [
        *([ctx_text] if ctx_text is not None else []),
        *quota_badges,
        *([cost_text] if cost_text is not None else []),
        *([plan_text] if plan_text is not None else []),
    ]
    if not items:
        return None

    # Drop plan_tier first, then cost, if the single row exceeds terminal width.
    for droppable in (plan_text, cost_text):
        if _row_width(items) <= max_width:
            break
        if droppable is not None and len(items) > 1:
            items.pop()

    rows: list[list[str]]
    if _row_width(items) <= max_width:
        rows = [items]
    elif ctx_text is not None and quota_badges:
        if display_width(ctx_text) + _GAP_WIDTH + max(display_width(badge) for badge in quota_badges) <= max_width:
            rows = [[ctx_text, quota_badges[0]], *(["", badge] for badge in quota_badges[1:])]
        else:
            rows = [[ctx_text], *([badge] for badge in quota_badges)]
    elif len(quota_badges) > 1:
        rows = [[badge] for badge in quota_badges]
    else:
        rows = [_fit_row(items, max_width)]
    return _grid_band(rows)


def _activity_band(payload: AgyPayload, max_width: int) -> Table | None:
    items = [
        text
        for text in (
            f"{BOLD}{RED}confirm{RESET}" if payload.confirmation_pending else None,
            f"{CYAN}tasks:{payload.task_count}{RESET}" if payload.task_count is not None else None,
            f"{YELLOW}input:{payload.pending_input_count}{RESET}" if payload.pending_input_count is not None else None,
        )
        if text is not None
    ]
    if not items:
        return None
    return _grid_band([_fit_row(items, max_width)])


def render_statusline(payload: AgyPayload, vcs: VcsState | None) -> str:
    effective_width = max(1, payload.terminal_width)
    bands: list[RenderableType] = [
        band
        for band in (
            _harness_band(payload, effective_width),
            _directory_band(payload, effective_width),
            _vcs_band(payload, vcs),
            _usage_band(payload, effective_width),
            _activity_band(payload, effective_width),
        )
        if band is not None
    ]
    if not bands:
        return ""

    console = Console(
        width=effective_width,
        force_terminal=True,
        color_system="truecolor",
        highlight=False,
        legacy_windows=False,
        _environ={},
    )
    with console.capture() as capture:
        console.print(Group(*bands))

    return "\n".join(line.rstrip() for line in capture.get().splitlines() if line.strip())
