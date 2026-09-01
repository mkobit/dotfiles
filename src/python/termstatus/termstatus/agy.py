import asyncio
import json
import math
import re
import sys
import unicodedata
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass

ANSI_ESCAPE = re.compile(r"(?:\x1b\[[0-9;]*m|\x1b]8;;.*?(?:\x1b\\\\|\x07))")
STATE_COLORS = {
    "idle": "\033[2m",
    "thinking": "\033[36m",
    "working": "\033[34m",
    "tool_use": "\033[35m",
    "initializing": "\033[33m",
}
GIT_TIMEOUT_SECONDS = 0.125


@dataclass(frozen=True)
class VcsState:
    branch: str | None
    dirty: bool
    is_repo: bool
    upstream: str | None = None
    ahead: int = 0
    behind: int = 0
    origin_url: str | None = None


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
    remaining_context: int | None
    cwd: str | None
    model: str | None
    effort: str | None
    execution_mode: str | None
    plan_tier: str | None
    vim_mode: str | None
    cost: float | None
    terminal_width: int
    quotas: dict[str, Quota]
    vcs: VcsState | None
    sandbox: SandboxState | None
    task_count: int | None
    pending_input_count: int | None
    confirmation_pending: bool
    artifact_count: int | None


@dataclass(frozen=True)
class Slot:
    line: int
    index: int
    minimum_width: int
    text: str


def mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {key: item for key, item in value.items() if isinstance(key, str)}


def normalized_text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def percent(value: object) -> int | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return round(value)
    return None


def integer(value: object) -> int | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return int(value)
    return None


def count(value: object) -> int | None:
    number = integer(value)
    if number is not None:
        return max(0, number)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value)
    return None


def first_count(*values: object) -> int | None:
    for value in values:
        result = count(value)
        if result is not None:
            return result
    return None


def cost_value(value: object) -> float | None:
    cost = mapping(value)
    candidates = (cost.get("estimated"), cost.get("total"), cost.get("total_cost_usd")) if cost else (value,)
    for candidate in candidates:
        if isinstance(candidate, (int, float)) and not isinstance(candidate, bool) and math.isfinite(candidate):
            return float(candidate)
    return None


def decode_quotas(raw: Mapping[str, object]) -> dict[str, Quota]:
    quotas = {}
    for name, value in raw.items():
        item = mapping(value)
        remaining = percent(item.get("remaining_percentage"))
        fraction = item.get("remaining_fraction")
        if (
            remaining is None
            and isinstance(fraction, (int, float))
            and not isinstance(fraction, bool)
            and math.isfinite(fraction)
        ):
            remaining = round(fraction * 100)
        reset = integer(item.get("reset_in_seconds"))
        if remaining is not None and reset is not None:
            quotas[name] = Quota(max(0, min(100, remaining)), max(0, reset))
    return quotas


def decode_vcs(raw: Mapping[str, object]) -> VcsState | None:
    branch = normalized_text(raw.get("branch"))
    upstream = normalized_text(raw.get("upstream"))
    if not raw and not branch:
        return None
    return VcsState(
        branch,
        bool(raw.get("dirty")),
        bool(raw.get("is_repo", branch)),
        upstream,
        max(0, integer(raw.get("ahead")) or 0),
        max(0, integer(raw.get("behind")) or 0),
    )


def decode_sandbox(raw: Mapping[str, object]) -> SandboxState | None:
    if not raw:
        return None
    return SandboxState(bool(raw.get("enabled")), bool(raw.get("allow_network")))


def decode_payload(raw: Mapping[str, object]) -> AgyPayload:
    context = mapping(raw.get("context_window"))
    remaining = percent(context.get("remaining_percentage"))
    if remaining is None and (used := percent(context.get("used_percentage"))) is not None:
        remaining = 100 - used
    model = mapping(raw.get("model"))
    effort = (
        normalized_text(model.get("effort"))
        or normalized_text(model.get("reasoning_effort"))
        or normalized_text(raw.get("effort"))
    )
    plan = mapping(raw.get("plan"))
    confirmation = raw.get("confirmation_pending")
    if confirmation is None:
        confirmation = mapping(raw.get("confirmation")).get("pending")
    return AgyPayload(
        state=normalized_text(raw.get("agent_state")) or "idle",
        remaining_context=max(0, min(100, remaining)) if remaining is not None else None,
        cwd=normalized_text(raw.get("cwd")) or normalized_text(raw.get("workspace_directory")),
        model=normalized_text(model.get("display_name")),
        effort=effort,
        execution_mode=normalized_text(raw.get("execution_mode")) or normalized_text(raw.get("mode")),
        plan_tier=normalized_text(plan.get("tier")) or normalized_text(raw.get("plan_tier")),
        vim_mode=normalized_text(raw.get("vim_mode")),
        cost=cost_value(raw.get("cost")),
        terminal_width=max(1, integer(raw.get("terminal_width")) or 80),
        quotas=decode_quotas(mapping(raw.get("quota"))),
        vcs=decode_vcs(mapping(raw.get("vcs"))),
        sandbox=decode_sandbox(mapping(raw.get("sandbox"))),
        task_count=first_count(raw.get("task_count"), raw.get("tasks")),
        pending_input_count=first_count(raw.get("pending_input_count"), raw.get("pending_inputs")),
        confirmation_pending=bool(confirmation),
        artifact_count=first_count(raw.get("artifact_count"), raw.get("artifacts")),
    )


def parse_git_status(stdout: bytes) -> VcsState | None:
    branch: str | None = None
    upstream: str | None = None
    ahead = behind = 0
    dirty = False
    saw_header = False
    for line in stdout.decode(errors="replace").splitlines():
        if line.startswith("# branch.head "):
            saw_header = True
            value = line.removeprefix("# branch.head ").strip()
            branch = None if value.startswith("(") else normalized_text(value)
        elif line.startswith("# branch.upstream "):
            upstream = normalized_text(line.removeprefix("# branch.upstream "))
        elif match := re.fullmatch(r"# branch\.ab \+(\d+) -(\d+)", line):
            ahead, behind = (int(value) for value in match.groups())
        elif not line.startswith("# "):
            dirty = True
    if not saw_header:
        return None
    return VcsState(branch, dirty, True, upstream, ahead, behind)


def github_url(remote: str | None) -> str | None:
    if not remote:
        return None
    match = re.fullmatch(
        r"(?:git@github\.com:|ssh://git@github\.com/|https?://github\.com/|git://github\.com/)([^/:\s]+/[^/\s]+?)(?:\.git)?/?",
        remote.strip(),
    )
    return f"https://github.com/{match.group(1)}" if match else None


async def probe_git(cwd: str) -> VcsState | None:
    processes: list[asyncio.subprocess.Process] = []
    launches = [
        asyncio.create_task(
            asyncio.create_subprocess_exec(
                "git",
                "-C",
                cwd,
                "status",
                "--porcelain=v2",
                "--branch",
                "-uno",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
        ),
        asyncio.create_task(
            asyncio.create_subprocess_exec(
                "git",
                "-C",
                cwd,
                "remote",
                "get-url",
                "origin",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
        ),
    ]
    try:
        async with asyncio.timeout(GIT_TIMEOUT_SECONDS):
            processes = list(await asyncio.gather(*launches))
            results = await asyncio.gather(*(process.communicate() for process in processes))
    except TimeoutError, OSError:
        for launch in launches:
            if not launch.done():
                launch.cancel()
        for process in processes:
            with suppress(ProcessLookupError):
                process.kill()
        return None
    if any(process.returncode != 0 for process in processes):
        return None
    vcs = parse_git_status(results[0][0])
    if vcs is None:
        return None
    return VcsState(
        vcs.branch,
        vcs.dirty,
        vcs.is_repo,
        vcs.upstream,
        vcs.ahead,
        vcs.behind,
        normalized_text(results[1][0].decode(errors="replace")),
    )


async def resolve_vcs(payload: AgyPayload) -> VcsState | None:
    if not payload.cwd:
        return payload.vcs
    if vcs := await probe_git(payload.cwd):
        return vcs
    if payload.vcs:
        return VcsState(payload.vcs.branch, payload.vcs.dirty, payload.vcs.is_repo)
    return None


def strip_ansi(value: str) -> str:
    return ANSI_ESCAPE.sub("", value)


def display_width(value: str) -> int:
    plain = strip_ansi(value)
    return sum(
        0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
        for char in plain
    )


def format_meter(remaining: int) -> str:
    return f"{remaining}%"


def format_cost(cost: float) -> str:
    if cost < 0.001:
        return "<$0.001" if cost > 0 else "$0.00"
    if cost < 0.0095:
        return f"${cost:.3f}"
    return f"${cost:.2f}"


def model_name(model: str | None, effort: str | None) -> str | None:
    if not model or not effort:
        return model
    return re.sub(rf"\s*\({re.escape(effort)}\)$", "", model)


def git_branch(vcs: VcsState) -> str | None:
    if not vcs.branch:
        return None
    branch = vcs.branch + ("*" if vcs.dirty else "")
    return f"\033]8;;{url}\033\\{branch}\033]8;;\033\\" if (url := github_url(vcs.origin_url)) else branch


def fit_slots(slots: list[Slot], width: int) -> str | None:
    chosen: list[str] = []
    for slot in sorted(slots, key=lambda item: item.index):
        if width < slot.minimum_width:
            continue
        candidate = " ".join((*chosen, slot.text))
        if display_width(candidate) <= width:
            chosen.append(slot.text)
    return " ".join(chosen) or None


def identity_slots(payload: AgyPayload) -> list[Slot]:
    state = f"{STATE_COLORS.get(payload.state, '\033[37m')}[{payload.state}]\033[0m"
    model = model_name(payload.model, payload.effort)
    slots = [Slot(0, 0, 1, state)]
    for index, minimum_width, text in (
        (1, 30, model),
        (2, 45, payload.effort),
        (3, 65, payload.execution_mode),
        (4, 85, f"plan:{payload.plan_tier}" if payload.plan_tier else None),
        (
            5,
            105,
            f"sandbox:{'net' if payload.sandbox.allow_network else 'no-net'}"
            if payload.sandbox and payload.sandbox.enabled
            else None,
        ),
        (6, 125, f"vim:{payload.vim_mode}" if payload.vim_mode else None),
    ):
        if text:
            slots.append(Slot(0, index, minimum_width, text))
    return slots


def resource_slots(payload: AgyPayload) -> list[Slot]:
    slots: list[Slot] = []
    if payload.cwd:
        slots.append(Slot(1, 0, 10, payload.cwd))
    if payload.remaining_context is not None:
        slots.append(Slot(1, 1, 20, f"{format_meter(payload.remaining_context)} ctx"))
    for index, (name, quota) in enumerate(payload.quotas.items(), start=2):
        slots.append(Slot(1, index, 45, f"{name}:{format_meter(quota.remaining)}"))
    if payload.cost is not None:
        slots.append(Slot(1, len(payload.quotas) + 2, 90, format_cost(payload.cost)))
    return slots


def vcs_slots(vcs: VcsState | None) -> list[Slot]:
    slots: list[Slot] = []
    if vcs:
        if branch := git_branch(vcs):
            slots.append(Slot(2, 0, 10, branch))
        if vcs.upstream:
            slots.append(Slot(2, 1, 55, vcs.upstream))
        if vcs.ahead:
            slots.append(Slot(2, 2, 75, f"ahead:{vcs.ahead}"))
        if vcs.behind:
            slots.append(Slot(2, 3, 90, f"behind:{vcs.behind}"))
    return slots


def activity_slots(payload: AgyPayload) -> list[Slot]:
    slots: list[Slot] = []
    if payload.task_count is not None:
        slots.append(Slot(3, 0, 10, f"tasks:{payload.task_count}"))
    if payload.pending_input_count is not None:
        slots.append(Slot(3, 1, 30, f"input:{payload.pending_input_count}"))
    if payload.confirmation_pending:
        slots.append(Slot(3, 2, 50, "confirm"))
    if payload.artifact_count is not None:
        slots.append(Slot(3, 3, 65, f"artifacts:{payload.artifact_count}"))
    return slots


def render_statusline(payload: AgyPayload, vcs: VcsState | None) -> str:
    slots = identity_slots(payload) + resource_slots(payload) + vcs_slots(vcs or payload.vcs) + activity_slots(payload)
    rows = [fit_slots([slot for slot in slots if slot.line == line], payload.terminal_width) for line in range(4)]
    return "\n".join(row for row in rows if row)


def render_from_stdin() -> None:
    try:
        raw = json.loads(sys.stdin.read())
    except Exception:
        raw = {}
    payload = decode_payload(mapping(raw))
    try:
        vcs = asyncio.run(resolve_vcs(payload))
    except Exception:
        vcs = payload.vcs
    print(render_statusline(payload, vcs))
