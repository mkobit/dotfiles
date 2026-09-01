import json
import os
import re
import sys
import unicodedata
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

ANSI_SGR = re.compile(r"\x1b\[[0-9;]*m")
STATE_COLORS = {"idle": "\033[2m", "thinking": "\033[36m", "working": "\033[34m", "tool_use": "\033[35m", "initializing": "\033[33m"}


@dataclass(frozen=True)
class VcsState:
    branch: str | None
    dirty: bool
    is_repo: bool


@dataclass(frozen=True)
class Quota:
    remaining: int
    reset_in_seconds: int


@dataclass(frozen=True)
class SandboxState:
    enabled: bool
    allow_network: bool


@dataclass(frozen=True)
class AgyPayload:
    state: str
    remaining_context: int
    cwd: str | None
    model: str | None
    effort: str | None
    cost: float | None
    terminal_width: int
    quotas: dict[str, Quota]
    vcs: VcsState | None
    sandbox: SandboxState | None


def mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def normalized_text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def percent(value: object) -> int | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return round(value)
    return None


def integer(value: object) -> int | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    return None


def cost_value(value: object) -> float | None:
    value = mapping(value).get("estimated", mapping(value).get("total_cost_usd", value))
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def decode_quotas(raw: Mapping[str, object]) -> dict[str, Quota]:
    quotas = {}
    for name, value in raw.items():
        item = mapping(value)
        remaining = percent(item.get("remaining_percentage"))
        if remaining is None and isinstance(item.get("remaining_fraction"), (int, float)):
            remaining = round(float(item["remaining_fraction"]) * 100)
        reset = integer(item.get("reset_in_seconds"))
        if remaining is not None and reset is not None:
            quotas[name] = Quota(max(0, min(100, remaining)), max(0, reset))
    return quotas


def decode_vcs(raw: Mapping[str, object]) -> VcsState | None:
    branch = normalized_text(raw.get("branch"))
    if not raw and not branch:
        return None
    return VcsState(branch, bool(raw.get("dirty")), bool(raw.get("is_repo", branch)))


def decode_sandbox(raw: Mapping[str, object]) -> SandboxState | None:
    if not raw:
        return None
    return SandboxState(bool(raw.get("enabled")), bool(raw.get("allow_network")))


def decode_payload(raw: Mapping[str, object]) -> AgyPayload:
    context = mapping(raw.get("context_window"))
    remaining = percent(context.get("remaining_percentage"))
    if remaining is None:
        remaining = 100 - (percent(context.get("used_percentage")) or 0)
    model = mapping(raw.get("model"))
    effort = normalized_text(model.get("effort")) or normalized_text(model.get("reasoning_effort")) or normalized_text(raw.get("effort"))
    return AgyPayload(
        state=normalized_text(raw.get("agent_state")) or "idle",
        remaining_context=max(0, min(100, remaining)),
        cwd=normalized_text(raw.get("cwd")),
        model=normalized_text(model.get("display_name")),
        effort=effort,
        cost=cost_value(raw.get("cost")),
        terminal_width=max(1, integer(raw.get("terminal_width")) or 80),
        quotas=decode_quotas(mapping(raw.get("quota"))),
        vcs=decode_vcs(mapping(raw.get("vcs"))),
        sandbox=decode_sandbox(mapping(raw.get("sandbox"))),
    )


def strip_ansi(value: str) -> str:
    return ANSI_SGR.sub("", value)


def display_width(value: str) -> int:
    plain = strip_ansi(value)
    return sum(0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1 for char in plain)


def format_meter(remaining: int) -> str:
    glyph = "●" if remaining >= 85 else "◕" if remaining >= 65 else "◑" if remaining >= 40 else "◔" if remaining >= 15 else "○"
    color = "\033[32m" if remaining > 40 else "\033[33m" if remaining >= 20 else "\033[31m"
    return f"{color}{glyph}{remaining}%\033[0m"


def duration(seconds: int) -> str:
    if seconds >= 3600:
        return f"{seconds // 3600}h"
    return f"{max(1, seconds // 60)}m"


def limiting_timer(gemini: Quota | None, weekly: Quota | None) -> str | None:
    if not gemini and not weekly:
        return None
    if gemini and weekly and gemini.remaining >= 85 and weekly.remaining >= 85:
        return None
    if weekly and weekly.remaining <= 20:
        return f"wk:{duration(weekly.reset_in_seconds)}"
    chosen = min((quota for quota in (gemini, weekly) if quota), key=lambda q: q.remaining)
    label = "5h" if chosen is gemini else "wk"
    return f"{label}:{duration(chosen.reset_in_seconds)}"


def _cost(cost: float | None) -> str:
    if cost is None:
        return ""
    if cost < 0.001:
        text = "<$0.001" if cost > 0 else "$0.00"
    elif cost < 0.0095:
        text = f"${cost:.3f}"
    else:
        text = f"${cost:.2f}"
    return f"\033[2m{text}\033[0m"


def render_statusline(payload: AgyPayload, vcs: VcsState | None) -> str:
    vcs = vcs or payload.vcs
    model = payload.model
    if model and payload.effort:
        model = re.sub(rf"\s*\({re.escape(payload.effort)}\)$", "", model)
    state = f"{STATE_COLORS.get(payload.state, '\033[37m')}[{payload.state}]\033[0m"
    left = [state, f"{format_meter(payload.remaining_context)} ctx", payload.cwd and Path(payload.cwd).name]
    if payload.terminal_width >= 75 and vcs and vcs.branch:
        left.append(vcs.branch + ("*" if vcs.dirty else ""))
    if payload.cost is not None:
        left.append(_cost(payload.cost))
    left = [str(value) for value in left if value]
    if payload.terminal_width >= 80:
        gemini = payload.quotas.get("gemini-5h")
        weekly = payload.quotas.get("gemini-weekly")
        if gemini and weekly:
            timer = limiting_timer(gemini, weekly)
            timer_text = f" {timer}" if timer and (payload.terminal_width >= 90 or payload.cost is None) else ""
            left.append(f"g:{format_meter(gemini.remaining)}" + timer_text)
        if payload.terminal_width >= 100:
            third = payload.quotas.get("3p-5h")
            third_weekly = payload.quotas.get("3p-weekly")
            if third and third_weekly:
                third_timer = limiting_timer(third, third_weekly)
                timer_text = f" {third_timer}" if third_timer and payload.terminal_width >= 110 else ""
                left.append(f"3p:{format_meter(third.remaining)}" + timer_text)
    if payload.terminal_width >= 110:
        if model:
            left.append(model)
        if payload.sandbox and payload.sandbox.enabled:
            left.append("sandbox")
        if payload.effort:
            left.append(payload.effort)
    right = model if payload.terminal_width < 75 and model else (vcs.branch if vcs and vcs.branch else "")
    text = " ".join(left)
    padding = payload.terminal_width - display_width(text) - display_width(right)
    return f"{text}{' ' * padding}{right}" if padding > 1 else " ".join(part for part in (text, right) if part)


def render_from_stdin() -> None:
    raw_text = sys.stdin.read()
    try:
        raw = json.loads(raw_text) if raw_text.strip() else {}
        raw = raw if isinstance(raw, dict) else {}
    except Exception:
        raw = {}
    debug = os.environ.get("AGY_STATUSLINE_DEBUG")
    if debug:
        destination = "/tmp/agy-statusline-debug.json" if debug.lower() in {"1", "true"} else debug  # noqa: S108
        with suppress(Exception):
            Path(destination).write_text(raw_text)
    print(render_statusline(decode_payload(raw), None))
