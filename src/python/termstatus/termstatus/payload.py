from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any


def _instantiate_dataclass[T](cls: type[T], data: Any) -> T:
    if not isinstance(data, dict):
        return cls()
    valid_fields = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    return cls(**filtered)


@dataclass
class ModelInfo:
    id: str | None = None
    display_name: str = "Unknown Model"


@dataclass
class WorkspaceInfo:
    current_dir: str = field(default_factory=lambda: str(Path.cwd()))
    project_dir: str | None = None
    added_dirs: list[str] = field(default_factory=list)
    git_worktree: str | None = None


@dataclass
class CostInfo:
    total_cost_usd: float | None = 0.0
    total_duration_ms: int | None = 0
    total_api_duration_ms: int | None = 0
    total_lines_added: int | None = 0
    total_lines_removed: int | None = 0


@dataclass
class CurrentUsageInfo:
    input_tokens: int | None = 0
    output_tokens: int | None = 0
    cache_creation_input_tokens: int | None = 0
    cache_read_input_tokens: int | None = 0


@dataclass
class ContextWindowInfo:
    total_input_tokens: int | None = 0
    total_output_tokens: int | None = 0
    context_window_size: int | None = 0
    used_percentage: float | None = 0.0
    remaining_percentage: float | None = 0.0
    current_usage: CurrentUsageInfo | None = field(default_factory=CurrentUsageInfo)


@dataclass
class RateLimitWindow:
    used_percentage: float | None = 0.0
    resets_at: int | None = 0


@dataclass
class RateLimits:
    five_hour: RateLimitWindow | None = field(default_factory=RateLimitWindow)
    seven_day: RateLimitWindow | None = field(default_factory=RateLimitWindow)


@dataclass
class OutputStyle:
    name: str | None = None


@dataclass
class VimInfo:
    mode: str | None = None


@dataclass
class AgentInfo:
    name: str | None = None


@dataclass
class WorktreeInfo:
    name: str | None = None
    path: str | None = None
    branch: str | None = None
    original_cwd: str | None = None
    original_branch: str | None = None


@dataclass
class StatusLineStdIn:
    model: ModelInfo = field(default_factory=ModelInfo)
    cwd: str | None = None
    workspace: WorkspaceInfo = field(default_factory=WorkspaceInfo)
    cost: CostInfo = field(default_factory=CostInfo)
    context_window: ContextWindowInfo = field(default_factory=ContextWindowInfo)
    exceeds_200k_tokens: bool | None = False
    rate_limits: RateLimits | None = field(default_factory=RateLimits)
    session_id: str | None = None
    session_name: str | None = None
    transcript_path: str | None = None
    version: str | None = None
    output_style: OutputStyle | None = field(default_factory=OutputStyle)
    vim: VimInfo | None = field(default_factory=VimInfo)
    agent: AgentInfo = field(default_factory=AgentInfo)
    worktree: WorktreeInfo | None = field(default_factory=WorktreeInfo)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StatusLineStdIn:
        if not isinstance(data, dict):
            return cls()

        model = _instantiate_dataclass(ModelInfo, data.get("model"))
        workspace = _instantiate_dataclass(WorkspaceInfo, data.get("workspace"))
        cost = _instantiate_dataclass(CostInfo, data.get("cost"))

        cw_raw = data.get("context_window")
        if isinstance(cw_raw, dict):
            cw = _instantiate_dataclass(ContextWindowInfo, cw_raw)
            cw.current_usage = _instantiate_dataclass(CurrentUsageInfo, cw_raw.get("current_usage"))
        else:
            cw = ContextWindowInfo()

        rl_raw = data.get("rate_limits")
        if isinstance(rl_raw, dict):
            fh = _instantiate_dataclass(RateLimitWindow, rl_raw.get("five_hour"))
            sd = _instantiate_dataclass(RateLimitWindow, rl_raw.get("seven_day"))
            rl = RateLimits(five_hour=fh, seven_day=sd)
        else:
            rl = RateLimits()

        output_style = _instantiate_dataclass(OutputStyle, data.get("output_style"))
        vim = _instantiate_dataclass(VimInfo, data.get("vim"))
        agent = _instantiate_dataclass(AgentInfo, data.get("agent"))
        worktree = _instantiate_dataclass(WorktreeInfo, data.get("worktree"))

        return cls(
            model=model,
            cwd=data.get("cwd"),
            workspace=workspace,
            cost=cost,
            context_window=cw,
            exceeds_200k_tokens=data.get("exceeds_200k_tokens", False),
            rate_limits=rl,
            session_id=data.get("session_id"),
            session_name=data.get("session_name"),
            transcript_path=data.get("transcript_path"),
            version=data.get("version"),
            output_style=output_style,
            vim=vim,
            agent=agent,
            worktree=worktree,
        )

