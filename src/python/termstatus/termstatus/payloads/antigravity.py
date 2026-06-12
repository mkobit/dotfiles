from pydantic import BaseModel


class ModelInfo(BaseModel):
    id: str | None = None
    display_name: str | None = None


class Workspace(BaseModel):
    current_dir: str | None = None
    project_dir: str | None = None


class CurrentUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None


class ContextWindow(BaseModel):
    total_input_tokens: int | None = None
    total_output_tokens: int | None = None
    context_window_size: int | None = None
    used_percentage: float | None = None
    remaining_percentage: float | None = None
    current_usage: CurrentUsage | None = None


class Vcs(BaseModel):
    type: str | None = None
    client: str | None = None
    branch: str | None = None
    dirty: bool | None = None


class Sandbox(BaseModel):
    enabled: bool | None = None
    allow_network: bool | None = None


class AntigravityPayload(BaseModel):
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
