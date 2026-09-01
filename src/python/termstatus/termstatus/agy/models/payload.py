from collections.abc import Mapping
from dataclasses import dataclass

from termstatus.agy.models.quota import Quota
from termstatus.agy.models.sandbox import SandboxState
from termstatus.agy.models.vcs import VcsState


@dataclass(frozen=True, slots=True)
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
    quotas: Mapping[str, Quota]
    vcs: VcsState | None
    sandbox: SandboxState | None
    task_count: int | None
    pending_input_count: int | None
    confirmation_pending: bool
    artifact_count: int | None
