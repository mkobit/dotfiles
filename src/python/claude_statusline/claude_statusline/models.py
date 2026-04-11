from pathlib import Path

from pydantic import BaseModel, Field

# --- Pydantic Models for Claude Code JSON Payload ---
# See: https://code.claude.com/docs/en/statusline


class ModelInfo(BaseModel):
    id: str | None = None
    display_name: str = "Unknown Model"


class WorkspaceInfo(BaseModel):
    current_dir: str = Field(default_factory=lambda: str(Path.cwd()))
    project_dir: str | None = None
    added_dirs: list[str] = Field(default_factory=list)
    git_worktree: str | None = None


class CostInfo(BaseModel):
    total_cost_usd: float | None = 0.0
    total_duration_ms: int | None = 0
    total_api_duration_ms: int | None = 0
    total_lines_added: int | None = 0
    total_lines_removed: int | None = 0


class CurrentUsageInfo(BaseModel):
    input_tokens: int | None = 0
    output_tokens: int | None = 0
    cache_creation_input_tokens: int | None = 0
    cache_read_input_tokens: int | None = 0


class ContextWindowInfo(BaseModel):
    total_input_tokens: int | None = 0
    total_output_tokens: int | None = 0
    context_window_size: int | None = 0
    used_percentage: float | None = 0.0
    remaining_percentage: float | None = 0.0
    current_usage: CurrentUsageInfo | None = Field(default_factory=CurrentUsageInfo)


class Exceeds200kTokens(BaseModel):
    pass  # this is just a boolean, no need for a class


class RateLimitWindow(BaseModel):
    used_percentage: float | None = 0.0
    resets_at: int | None = 0


class RateLimits(BaseModel):
    five_hour: RateLimitWindow | None = Field(default_factory=RateLimitWindow)
    seven_day: RateLimitWindow | None = Field(default_factory=RateLimitWindow)


class OutputStyle(BaseModel):
    name: str | None = None


class VimInfo(BaseModel):
    mode: str | None = None


class AgentInfo(BaseModel):
    name: str | None = None


class WorktreeInfo(BaseModel):
    name: str | None = None
    path: str | None = None
    branch: str | None = None
    original_cwd: str | None = None
    original_branch: str | None = None


class StatusLineStdIn(BaseModel):
    """
    Pydantic model representing the JSON payload sent via stdin to the statusline.
    Available data fields: https://code.claude.com/docs/en/statusline#available-data
    """

    model: ModelInfo = Field(default_factory=ModelInfo)
    cwd: str | None = None  # Preferred to use workspace.current_dir
    workspace: WorkspaceInfo = Field(default_factory=WorkspaceInfo)
    cost: CostInfo = Field(default_factory=CostInfo)
    context_window: ContextWindowInfo = Field(default_factory=ContextWindowInfo)
    exceeds_200k_tokens: bool | None = False
    rate_limits: RateLimits | None = Field(default_factory=RateLimits)
    session_id: str | None = None
    session_name: str | None = None
    transcript_path: str | None = None
    version: str | None = None
    output_style: OutputStyle | None = Field(default_factory=OutputStyle)
    vim: VimInfo | None = Field(default_factory=VimInfo)
    agent: AgentInfo = Field(default_factory=AgentInfo)
    worktree: WorktreeInfo | None = Field(default_factory=WorktreeInfo)


# --- Internal Data Models ---
class GitInfo(BaseModel):
    branch: str
    remote: str | None
    dirty: bool
    staged: bool
    untracked: bool
    ahead: int
    behind: int
    is_repo: bool
    is_worktree: bool = False


class Segment(BaseModel):
    text: str


class SegmentGenerationResult(BaseModel):
    segment: Segment
    generator: str = "internal"
    line: int = 1
    index: int = 0
    cache_duration_seconds: int | None = None
    next_call_timestamp: float | None = None
