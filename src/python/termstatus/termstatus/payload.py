from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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
        model_raw = data.get("model")
        model = ModelInfo(**model_raw) if isinstance(model_raw, dict) else ModelInfo()

        workspace_raw = data.get("workspace")
        workspace = WorkspaceInfo(**workspace_raw) if isinstance(workspace_raw, dict) else WorkspaceInfo()

        cost_raw = data.get("cost")
        cost = CostInfo(**cost_raw) if isinstance(cost_raw, dict) else CostInfo()

        cw_raw = data.get("context_window")
        if isinstance(cw_raw, dict):
            cu_raw = cw_raw.get("current_usage")
            cu = CurrentUsageInfo(**cu_raw) if isinstance(cu_raw, dict) else CurrentUsageInfo()
            cw = ContextWindowInfo(
                total_input_tokens=cw_raw.get("total_input_tokens", 0),
                total_output_tokens=cw_raw.get("total_output_tokens", 0),
                context_window_size=cw_raw.get("context_window_size", 0),
                used_percentage=cw_raw.get("used_percentage", 0.0),
                remaining_percentage=cw_raw.get("remaining_percentage", 0.0),
                current_usage=cu,
            )
        else:
            cw = ContextWindowInfo()

        rl_raw = data.get("rate_limits")
        if isinstance(rl_raw, dict):
            fh_raw = rl_raw.get("five_hour")
            fh = RateLimitWindow(**fh_raw) if isinstance(fh_raw, dict) else RateLimitWindow()
            sd_raw = rl_raw.get("seven_day")
            sd = RateLimitWindow(**sd_raw) if isinstance(sd_raw, dict) else RateLimitWindow()
            rl = RateLimits(five_hour=fh, seven_day=sd)
        else:
            rl = RateLimits()

        out_raw = data.get("output_style")
        output_style = OutputStyle(**out_raw) if isinstance(out_raw, dict) else OutputStyle()

        vim_raw = data.get("vim")
        vim = VimInfo(**vim_raw) if isinstance(vim_raw, dict) else VimInfo()

        agent_raw = data.get("agent")
        agent = AgentInfo(**agent_raw) if isinstance(agent_raw, dict) else AgentInfo()

        wt_raw = data.get("worktree")
        worktree = WorktreeInfo(**wt_raw) if isinstance(wt_raw, dict) else WorktreeInfo()

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
