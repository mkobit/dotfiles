import math
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from re import Pattern
from typing import Final

from whenever import TimeDelta

from termstatus.agy.protocol import AgyPayload, Quota, VcsState, normalized_text
from termstatus.agy.term_colors import (
    _STATE_COLORS,
    BLUE,
    BOLD,
    CYAN,
    DARK_GREY,
    DIM,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    SEPARATOR,
    SKY_BLUE,
    YELLOW,
    fullness_icon,
    get_icon,
    meter_color,
    state_icon,
    use_icons,
)

_ANSI_ESCAPE: Final[Pattern[str]] = re.compile(r"(?:\x1b\[[0-9;]*m|\x1b]8;;.*?(?:\x1b\\|\x07))")


@dataclass(frozen=True, slots=True)
class _Slot:
    line: int
    index: int
    minimum_width: int
    text: str


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
    if vcs.dirty:
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


def _fit_slots(slots: Sequence[_Slot], width: int) -> str | None:
    chosen: list[str] = []
    for slot in sorted(slots, key=lambda item: item.index):
        candidate = (*chosen, slot.text)
        if width >= slot.minimum_width and display_width(SEPARATOR.join(candidate)) <= width:
            chosen.append(slot.text)
    return SEPARATOR.join(chosen) or None


_THINK_LEVELS: Final[dict[str, int]] = {
    "off": 0,
    "none": 0,
    "low": 1,
    "medium": 2,
    "med": 2,
    "high": 3,
    "max": 3,
}

_CELL_BARS: Final[tuple[str, ...]] = ("▂", "▅", "█")


def _thinking_cellular_graph(effort: str | None) -> str:
    if effort is None:
        return ""
    low = effort.lower().strip()
    if low in _THINK_LEVELS:
        lvl = _THINK_LEVELS[low]
    elif low.isdigit():
        lvl = max(0, min(3, int(low)))
    else:
        return ""
    bars = [f"{CYAN}{_CELL_BARS[i]}{RESET}" if i < lvl else f"{DARK_GREY}{_CELL_BARS[i]}{RESET}" for i in range(3)]
    return "".join(bars)


def _identity_slots(payload: AgyPayload) -> list[_Slot]:
    icon = state_icon(payload.state)
    icon_prefix = f"{icon} " if icon else ""
    color = _STATE_COLORS.get(payload.state, "\033[37m")
    state = f"{color}[{icon_prefix}{payload.state}]{RESET}"
    slots = [_Slot(0, 0, 1, state)]
    model = _model_name(payload.model, payload.effort)
    model_text = f"{BOLD}{model}{RESET}" if model is not None else None
    brain = "🧠 " if use_icons() else ""
    graph = (
        f"{_thinking_cellular_graph(payload.effort)} "
        if use_icons() and _thinking_cellular_graph(payload.effort)
        else ""
    )
    think_text = f"{brain}{graph}{DIM}think:{RESET}{payload.effort}" if payload.effort is not None else None
    mode_text = f"{DIM}{payload.execution_mode}{RESET}" if payload.execution_mode is not None else None
    plan_text = f"{DIM}plan:{RESET}{payload.plan_tier}" if payload.plan_tier is not None else None

    sandbox_text = None
    if payload.sandbox and payload.sandbox.enabled:
        net_mode = "net" if payload.sandbox.allow_network else "no-net"
        sandbox_text = f"{DIM}sandbox:{RESET}{net_mode}"

    vim_text = f"{DIM}vim:{payload.vim_mode}{RESET}" if payload.vim_mode is not None else None

    values = (
        (1, 30, model_text),
        (2, 45, think_text),
        (3, 65, mode_text),
        (4, 85, plan_text),
        (5, 105, sandbox_text),
        (6, 125, vim_text),
    )
    slots.extend(_Slot(0, index, minimum_width, text) for index, minimum_width, text in values if text is not None)
    return slots


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


def _resource_slots(payload: AgyPayload) -> list[_Slot]:
    slots = [_Slot(1, 0, 10, _format_directory(payload.cwd))] if payload.cwd is not None else []
    if payload.remaining_context is not None:
        color = meter_color(payload.remaining_context)
        icon = fullness_icon(payload.remaining_context)
        slots.append(_Slot(1, 1, 20, f"{color}{icon} {_format_meter(payload.remaining_context)} ctx{RESET}"))

    five_hour_quotas: list[tuple[str, str]] = []
    for name in payload.quotas:
        if _quota_interval(name) != "5h":
            continue
        base_label = _format_quota_label(name)
        if base_label is None:
            continue
        five_hour_quotas.append((name, base_label))

    if five_hour_quotas:
        five_hour_parts: list[str] = []
        is_multiple = len(five_hour_quotas) > 1
        for name, base_label in five_hour_quotas:
            quota = payload.quotas[name]
            is_ambiguous = is_multiple and base_label == "5h"
            five_hour_parts.append(_format_quota_badge(name, quota, base_label, is_ambiguous=is_ambiguous))
        slots.append(_Slot(1, 2, 40, " ".join(five_hour_parts)))

    if payload.cost is not None:
        slots.append(_Slot(1, 3, 90, f"{DIM}{_format_cost(payload.cost)}{RESET}"))
    return slots


def _quota_slots(payload: AgyPayload) -> list[_Slot]:
    valid_quotas: list[tuple[str, str, str | None]] = []
    for name in payload.quotas:
        if _quota_interval(name) == "5h":
            continue
        base_label = _format_quota_label(name)
        if base_label is None:
            continue
        interval = _quota_interval(name)
        valid_quotas.append((name, base_label, interval))

    interval_counts: dict[str, int] = {}
    for _, _, interval in valid_quotas:
        if interval is not None:
            interval_counts[interval] = interval_counts.get(interval, 0) + 1

    quota_parts: list[str] = []
    for name, base_label, interval in valid_quotas:
        quota = payload.quotas[name]
        is_ambiguous = bool(interval and interval_counts.get(interval, 0) > 1 and base_label == interval)
        quota_parts.append(_format_quota_badge(name, quota, base_label, is_ambiguous=is_ambiguous))

    if quota_parts:
        return [_Slot(2, 0, 10, " ".join(quota_parts))]
    return []


def _vcs_slots(vcs: VcsState | None) -> list[_Slot]:
    if not vcs or not vcs.is_repo:
        return []
    if (branch := git_branch(vcs)) is not None:
        return [_Slot(3, 0, 10, branch)]
    return []


def _activity_slots(payload: AgyPayload) -> list[_Slot]:
    values = (
        (0, 10, f"{CYAN}tasks:{payload.task_count}{RESET}" if payload.task_count is not None else None),
        (
            1,
            30,
            f"{YELLOW}input:{payload.pending_input_count}{RESET}" if payload.pending_input_count is not None else None,
        ),
        (2, 50, f"{BOLD}{RED}confirm{RESET}" if payload.confirmation_pending else None),
        (3, 65, f"{BLUE}artifacts:{payload.artifact_count}{RESET}" if payload.artifact_count is not None else None),
    )
    return [_Slot(4, index, minimum_width, text) for index, minimum_width, text in values if text is not None]


def render_statusline(payload: AgyPayload, vcs: VcsState | None) -> str:
    slots = (
        _identity_slots(payload)
        + _resource_slots(payload)
        + _quota_slots(payload)
        + _vcs_slots(vcs or payload.vcs)
        + _activity_slots(payload)
    )
    return "\n".join(
        row
        for line in range(5)
        if (row := _fit_slots([slot for slot in slots if slot.line == line], payload.terminal_width)) is not None
    )
