import math
import unicodedata
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import TypeGuard

from whenever import TimeDelta

from termstatus.agy.models.payload import AgyPayload
from termstatus.agy.models.quota import Quota
from termstatus.agy.models.sandbox import SandboxState
from termstatus.agy.models.vcs import VcsState


def mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        return MappingProxyType({})
    return MappingProxyType({key: item for key, item in value.items() if isinstance(key, str)})


def normalized_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = "".join(char for char in value if not unicodedata.category(char).startswith("C")).strip()
    return text or None


def finite_number(value: object) -> TypeGuard[int | float]:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def percent(value: object) -> int | None:
    return round(value) if finite_number(value) else None


def integer(value: object) -> int | None:
    return int(value) if finite_number(value) else None


def count(value: object) -> int | None:
    if (number := integer(value)) is not None:
        return max(0, number)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value)
    return None


def first_count(*values: object) -> int | None:
    return next((result for value in values if (result := count(value)) is not None), None)


def cost_value(value: object) -> float | None:
    cost = mapping(value)
    candidates = (cost.get("estimated"), cost.get("total"), cost.get("total_cost_usd")) if cost else (value,)
    return next((float(candidate) for candidate in candidates if finite_number(candidate)), None)


def decode_quotas(raw: Mapping[str, object]) -> Mapping[str, Quota]:
    quotas: dict[str, Quota] = {}
    for name, value in raw.items():
        if not (label := normalized_text(name)):
            continue
        item = mapping(value)
        remaining = percent(item.get("remaining_percentage"))
        if remaining is None and finite_number(fraction := item.get("remaining_fraction")):
            remaining = round(fraction * 100)
        reset_seconds = integer(item.get("reset_in_seconds"))
        if remaining is not None:
            quotas[label] = Quota(
                max(0, min(100, remaining)),
                TimeDelta(seconds=max(0, reset_seconds)) if reset_seconds is not None else None,
            )
    return MappingProxyType(quotas)


def decode_vcs(raw: Mapping[str, object]) -> VcsState | None:
    branch = normalized_text(raw.get("branch"))
    if not raw and not branch:
        return None
    return VcsState(
        branch,
        bool(raw.get("dirty")),
        bool(raw.get("is_repo", branch)),
        normalized_text(raw.get("upstream")),
        max(0, integer(raw.get("ahead")) or 0),
        max(0, integer(raw.get("behind")) or 0),
    )


def decode_sandbox(raw: Mapping[str, object]) -> SandboxState | None:
    return SandboxState(bool(raw.get("enabled")), bool(raw.get("allow_network"))) if raw else None


def decode_payload(raw: Mapping[str, object]) -> AgyPayload:
    context = mapping(raw.get("context_window"))
    remaining = percent(context.get("remaining_percentage"))
    if remaining is None and (used := percent(context.get("used_percentage"))) is not None:
        remaining = 100 - used
    model = mapping(raw.get("model"))
    plan = mapping(raw.get("plan"))
    confirmation = raw.get("confirmation_pending")
    if confirmation is None:
        confirmation = mapping(raw.get("confirmation")).get("pending")
    return AgyPayload(
        normalized_text(raw.get("agent_state")) or "idle",
        max(0, min(100, remaining)) if remaining is not None else None,
        normalized_text(raw.get("cwd")) or normalized_text(raw.get("workspace_directory")),
        normalized_text(model.get("display_name")),
        normalized_text(model.get("effort"))
        or normalized_text(model.get("reasoning_effort"))
        or normalized_text(raw.get("effort")),
        normalized_text(raw.get("execution_mode")) or normalized_text(raw.get("mode")),
        normalized_text(plan.get("tier")) or normalized_text(raw.get("plan_tier")),
        normalized_text(raw.get("vim_mode")),
        cost_value(raw.get("cost")),
        max(1, integer(raw.get("terminal_width")) or 80),
        decode_quotas(mapping(raw.get("quota"))),
        decode_vcs(mapping(raw.get("vcs"))),
        decode_sandbox(mapping(raw.get("sandbox"))),
        first_count(raw.get("task_count"), raw.get("tasks")),
        first_count(raw.get("pending_input_count"), raw.get("pending_inputs")),
        bool(confirmation),
        first_count(raw.get("artifact_count"), raw.get("artifacts")),
    )
