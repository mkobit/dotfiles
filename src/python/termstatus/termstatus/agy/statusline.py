import math
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from re import Pattern
from typing import Final

from termstatus.agy.protocol import AgyPayload, VcsState, normalized_text
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
    return re.sub(rf"\s*\({re.escape(effort)}\)$", "", model, flags=re.IGNORECASE) if model and effort else model


def _github_url(remote: str | None) -> str | None:
    if not remote:
        return None
    match = re.fullmatch(
        r"(?:git@github\.com:|ssh://git@github\.com/|https?://github\.com/|git://github\.com/)([^/:\s]+/[^/\s]+?)(?:\.git)?/?",
        remote.strip(),
    )
    return f"https://github.com/{match.group(1)}" if match else None


def git_branch(vcs: VcsState) -> str | None:
    if not (branch := normalized_text(vcs.branch)):
        return None
    url = _github_url(vcs.origin_url)
    branch_link = f"\033]8;;{url}\033\\{branch}\033]8;;\033\\" if url else branch
    branch_icon = get_icon("branch")
    icon_prefix = f"{branch_icon} " if branch_icon else ""

    if upstream := normalized_text(vcs.upstream):
        remote_link = f"\033]8;;{url}\033\\{upstream}\033]8;;\033\\" if url else upstream
        pair_text = f"{DIM}<{RESET}{MAGENTA}{branch_link}{RESET} {DIM}→{RESET} {CYAN}{remote_link}{RESET}{DIM}>{RESET}"
    else:
        pair_text = f"{MAGENTA}{branch_link}{RESET}"

    status_items: list[str] = []
    if vcs.rebase:
        status_items.append(f"{YELLOW}rebase{RESET}")
    if vcs.dirty:
        status_items.append(f"{YELLOW}!{RESET}")
    if vcs.untracked:
        status_items.append(f"{YELLOW}?{RESET}")
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
    if not effort:
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
    model_text = f"{BOLD}{model}{RESET}" if model else None
    brain = "🧠 " if use_icons() else ""
    graph = (
        f"{_thinking_cellular_graph(payload.effort)} "
        if use_icons() and _thinking_cellular_graph(payload.effort)
        else ""
    )
    think_text = f"{brain}{graph}{DIM}think:{RESET}{payload.effort}" if payload.effort else None
    mode_text = f"{DIM}{payload.execution_mode}{RESET}" if payload.execution_mode else None
    plan_text = f"{DIM}plan:{RESET}{payload.plan_tier}" if payload.plan_tier else None

    sandbox_text = None
    if payload.sandbox and payload.sandbox.enabled:
        net_mode = "net" if payload.sandbox.allow_network else "no-net"
        sandbox_text = f"{DIM}sandbox:{RESET}{net_mode}"

    vim_text = f"{DIM}vim:{payload.vim_mode}{RESET}" if payload.vim_mode else None

    values = (
        (1, 30, model_text),
        (2, 45, think_text),
        (3, 65, mode_text),
        (4, 85, plan_text),
        (5, 105, sandbox_text),
        (6, 125, vim_text),
    )
    slots.extend(_Slot(0, index, minimum_width, text) for index, minimum_width, text in values if text)
    return slots


def _format_directory(cwd: str) -> str:
    short_path = shorten_path(cwd)
    link = f"\033]8;;file://{cwd}\033\\{short_path}\033]8;;\033\\"
    icon = get_icon("dir")
    icon_prefix = f"{icon} " if icon else ""
    return f"{SKY_BLUE}{icon_prefix}{link}{RESET}"


def _format_quota_label(name: str) -> str | None:
    low = name.lower()
    if low.startswith(("3p-", "3p_", "3p:")):
        return None
    if low.endswith("-5h") or low == "5h":
        return "5h"
    if low.endswith(("-weekly", "-7d")) or low in {"weekly", "7d"}:
        return "7d"
    if "-" in name:
        return name.split("-", 1)[1]
    return name


def _resource_slots(payload: AgyPayload) -> list[_Slot]:
    slots = [_Slot(1, 0, 10, _format_directory(payload.cwd))] if payload.cwd else []
    if payload.remaining_context is not None:
        color = meter_color(payload.remaining_context)
        icon = fullness_icon(payload.remaining_context)
        slots.append(_Slot(1, 1, 20, f"{color}{icon} {_format_meter(payload.remaining_context)} ctx{RESET}"))

    quota_parts: list[str] = []
    for name, quota in payload.quotas.items():
        label = _format_quota_label(name)
        if not label:
            continue
        color = meter_color(quota.remaining)
        icon = fullness_icon(quota.remaining)
        meter = _format_meter(quota.remaining)
        icon_text = f" {icon}" if use_icons() else ""
        quota_parts.append(f"{DIM}[{RESET}{color}{label}{icon_text} {meter}{RESET}{DIM}]{RESET}")

    if quota_parts:
        slots.append(_Slot(1, 2, 45, " ".join(quota_parts)))

    if payload.cost is not None:
        slots.append(_Slot(1, 3, 90, f"{DIM}{_format_cost(payload.cost)}{RESET}"))
    return slots


def _vcs_slots(vcs: VcsState | None) -> list[_Slot]:
    if not vcs:
        return []
    if branch := git_branch(vcs):
        return [_Slot(2, 0, 10, branch)]
    if vcs.dirty:
        dirty_icon = get_icon("dirty") or "!"
        return [_Slot(2, 0, 10, f"{YELLOW}{dirty_icon} dirty{RESET}")]
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
    return [_Slot(3, index, minimum_width, text) for index, minimum_width, text in values if text]


def render_statusline(payload: AgyPayload, vcs: VcsState | None) -> str:
    slots = (
        _identity_slots(payload) + _resource_slots(payload) + _vcs_slots(vcs or payload.vcs) + _activity_slots(payload)
    )
    return "\n".join(
        row
        for line in range(4)
        if (row := _fit_slots([slot for slot in slots if slot.line == line], payload.terminal_width))
    )
