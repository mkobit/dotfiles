from dataclasses import dataclass
from typing import Any


@dataclass
class ModelInfo:
    id: str | None = None
    display_name: str | None = None


@dataclass
class Workspace:
    current_dir: str | None = None
    project_dir: str | None = None


@dataclass
class CurrentUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None


@dataclass
class ContextWindow:
    total_input_tokens: int | None = None
    total_output_tokens: int | None = None
    context_window_size: int | None = None
    used_percentage: float | None = None
    remaining_percentage: float | None = None
    current_usage: CurrentUsage | None = None


@dataclass
class Vcs:
    type: str | None = None
    client: str | None = None
    branch: str | None = None
    dirty: bool | None = None


@dataclass
class Sandbox:
    enabled: bool | None = None
    allow_network: bool | None = None


@dataclass
class AntigravityPayload:
    cwd: str | None = None
    conversation_id: str | None = None
    model: ModelInfo | None = None
    workspace: Workspace | None = None
    version: str | None = None
    context_window: ContextWindow | None = None
    product: str | None = None
    agent_state: str | None = None
    vcs: Vcs | None = None
    sandbox: Sandbox | None = None
    plan_tier: str | None = None
    email: str | None = None
    terminal_width: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AntigravityPayload:
        model_raw = data.get("model")
        model = ModelInfo(**model_raw) if isinstance(model_raw, dict) else None

        workspace_raw = data.get("workspace")
        workspace = Workspace(**workspace_raw) if isinstance(workspace_raw, dict) else None

        cw_raw = data.get("context_window")
        if isinstance(cw_raw, dict):
            cu_raw = cw_raw.get("current_usage")
            cu = CurrentUsage(**cu_raw) if isinstance(cu_raw, dict) else None
            cw = ContextWindow(
                total_input_tokens=cw_raw.get("total_input_tokens"),
                total_output_tokens=cw_raw.get("total_output_tokens"),
                context_window_size=cw_raw.get("context_window_size"),
                used_percentage=cw_raw.get("used_percentage"),
                remaining_percentage=cw_raw.get("remaining_percentage"),
                current_usage=cu,
            )
        else:
            cw = None

        vcs_raw = data.get("vcs")
        vcs = Vcs(**vcs_raw) if isinstance(vcs_raw, dict) else None

        sb_raw = data.get("sandbox")
        sandbox = Sandbox(**sb_raw) if isinstance(sb_raw, dict) else None

        return cls(
            cwd=data.get("cwd"),
            conversation_id=data.get("conversation_id"),
            model=model,
            workspace=workspace,
            version=data.get("version"),
            context_window=cw,
            product=data.get("product"),
            agent_state=data.get("agent_state"),
            vcs=vcs,
            sandbox=sandbox,
            plan_tier=data.get("plan_tier"),
            email=data.get("email"),
            terminal_width=data.get("terminal_width"),
        )
