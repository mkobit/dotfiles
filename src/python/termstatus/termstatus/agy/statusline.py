import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from re import Pattern
from typing import Final

from termstatus.agy.protocol import AgyPayload, VcsState, normalized_text
from termstatus.agy.term_colors import _STATE_COLORS

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


def _format_meter(remaining: int) -> str:
    return f"{remaining}%"


def _format_cost(cost: float) -> str:
    if cost < 0.001:
        return "<$0.001" if cost > 0 else "$0.00"
    return f"${cost:.3f}" if cost < 0.0095 else f"${cost:.2f}"


def _model_name(model: str | None, effort: str | None) -> str | None:
    return re.sub(rf"\s*\({re.escape(effort)}\)$", "", model) if model and effort else model


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
    branch += "*" if vcs.dirty else ""
    return f"\033]8;;{url}\033\\{branch}\033]8;;\033\\" if (url := _github_url(vcs.origin_url)) else branch


def _fit_slots(slots: Sequence[_Slot], width: int) -> str | None:
    chosen: list[str] = []
    for slot in sorted(slots, key=lambda item: item.index):
        if width >= slot.minimum_width and display_width(" ".join((*chosen, slot.text))) <= width:
            chosen.append(slot.text)
    return " ".join(chosen) or None


def _identity_slots(payload: AgyPayload) -> list[_Slot]:
    state = f"{_STATE_COLORS.get(payload.state, '\033[37m')}[{payload.state}]\033[0m"
    slots = [_Slot(0, 0, 1, state)]
    values = (
        (1, 30, _model_name(payload.model, payload.effort)),
        (2, 45, payload.effort),
        (3, 65, payload.execution_mode),
        (4, 85, f"plan:{payload.plan_tier}" if payload.plan_tier else None),
        (
            5,
            105,
            f"sandbox:{'net' if payload.sandbox.allow_network else 'no-net'}"
            if payload.sandbox and payload.sandbox.enabled
            else "sandbox:off"
            if payload.sandbox
            else None,
        ),
        (6, 125, f"vim:{payload.vim_mode}" if payload.vim_mode else None),
    )
    slots.extend(_Slot(0, index, minimum_width, text) for index, minimum_width, text in values if text)
    return slots


def _resource_slots(payload: AgyPayload) -> list[_Slot]:
    slots = [_Slot(1, 0, 10, payload.cwd)] if payload.cwd else []
    if payload.remaining_context is not None:
        slots.append(_Slot(1, 1, 20, f"{_format_meter(payload.remaining_context)} ctx"))
    slots.extend(
        _Slot(1, index, 45, f"{name}:{_format_meter(quota.remaining)}")
        for index, (name, quota) in enumerate(payload.quotas.items(), start=2)
    )
    if payload.cost is not None:
        slots.append(_Slot(1, len(payload.quotas) + 2, 90, _format_cost(payload.cost)))
    return slots


def _vcs_slots(vcs: VcsState | None) -> list[_Slot]:
    if not vcs:
        return []
    slots = (
        [_Slot(2, 0, 10, branch)] if (branch := git_branch(vcs)) else [_Slot(2, 0, 10, "dirty")] if vcs.dirty else []
    )
    slots.extend(
        _Slot(2, index, minimum_width, text)
        for index, minimum_width, text in (
            (1, 55, normalized_text(vcs.upstream)),
            (2, 75, f"ahead:{vcs.ahead}" if vcs.ahead else None),
            (3, 90, f"behind:{vcs.behind}" if vcs.behind else None),
        )
        if text
    )
    return slots


def _activity_slots(payload: AgyPayload) -> list[_Slot]:
    values = (
        (0, 10, f"tasks:{payload.task_count}" if payload.task_count is not None else None),
        (1, 30, f"input:{payload.pending_input_count}" if payload.pending_input_count is not None else None),
        (2, 50, "confirm" if payload.confirmation_pending else None),
        (3, 65, f"artifacts:{payload.artifact_count}" if payload.artifact_count is not None else None),
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
