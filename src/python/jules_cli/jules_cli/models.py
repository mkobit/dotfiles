from enum import StrEnum, auto
from typing import override

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from whenever import Instant

# Common configuration for immutable models
# Use alias_generator to convert snake_case (Python) to camelCase (JSON/API)
frozen_config = ConfigDict(frozen=True, alias_generator=to_camel, populate_by_name=True)


class GitHubBranch(BaseModel):
    """A GitHub branch."""

    display_name: str
    model_config = frozen_config


class GitHubRepo(BaseModel):
    """Represents a GitHub repository."""

    owner: str
    repo: str
    is_private: bool | None = None
    default_branch: GitHubBranch | None = None
    branches: list[GitHubBranch] | None = None
    model_config = frozen_config


class Source(BaseModel):
    """Represents a Jules source."""

    name: str
    id: str
    github_repo: GitHubRepo | None = None
    model_config = frozen_config


class GitHubRepoContext(BaseModel):
    """Context for a GitHub repository source."""

    starting_branch: str
    model_config = frozen_config


class SourceContext(BaseModel):
    """Context identifying the source for a session."""

    source: str
    github_repo_context: GitHubRepoContext | None = None
    model_config = frozen_config


class AutomationMode(StrEnum):
    """Automation modes for a session."""

    @staticmethod
    @override
    def _generate_next_value_(
        name: str,
        start: int,
        count: int,
        last_values: list[str],
    ) -> str:  # type: ignore[override]
        _ = start, count, last_values
        return name

    AUTOMATION_MODE_UNSPECIFIED = auto()
    AUTO_CREATE_PR = auto()


class CreateSessionRequest(BaseModel):
    """Request body for creating a session."""

    prompt: str
    source_context: SourceContext
    automation_mode: AutomationMode | None = None
    title: str | None = None
    require_plan_approval: bool | None = None
    model_config = frozen_config


class PullRequest(BaseModel):
    """Output details for a Pull Request."""

    url: str
    title: str
    description: str
    model_config = frozen_config


class SessionOutput(BaseModel):
    """Generic output wrapper."""

    pull_request: PullRequest | None = None
    model_config = frozen_config


class SessionState(StrEnum):
    """State of a session."""

    @staticmethod
    @override
    def _generate_next_value_(
        name: str,
        start: int,
        count: int,
        last_values: list[str],
    ) -> str:  # type: ignore[override]
        _ = start, count, last_values
        return name

    STATE_UNSPECIFIED = auto()
    QUEUED = auto()
    PLANNING = auto()
    AWAITING_PLAN_APPROVAL = auto()
    AWAITING_USER_FEEDBACK = auto()
    IN_PROGRESS = auto()
    PAUSED = auto()
    FAILED = auto()
    COMPLETED = auto()


class Session(BaseModel):
    """Represents a Jules session."""

    name: str
    id: str
    title: str | None = None
    source_context: SourceContext
    prompt: str
    outputs: list[SessionOutput] | None = None
    create_time: Instant | None = None
    update_time: Instant | None = None
    state: SessionState | None = None
    url: str | None = None
    require_plan_approval: bool | None = None
    automation_mode: AutomationMode | None = None
    model_config = frozen_config


class PlanStep(BaseModel):
    """A single step in a plan."""

    id: str
    title: str
    description: str | None = None
    index: int | None = None
    model_config = frozen_config


class Plan(BaseModel):
    """A generated plan containing steps."""

    id: str
    steps: list[PlanStep]
    create_time: Instant | None = None
    model_config = frozen_config


class UserMessaged(BaseModel):
    """The user posted a message."""

    user_message: str
    model_config = frozen_config


class AgentMessaged(BaseModel):
    """The agent posted a message."""

    agent_message: str
    model_config = frozen_config


class PlanGenerated(BaseModel):
    """Activity payload for a generated plan."""

    plan: Plan
    model_config = frozen_config


class PlanApproved(BaseModel):
    """Activity payload for an approved plan."""

    plan_id: str
    model_config = frozen_config


class ProgressUpdated(BaseModel):
    """Activity payload for a progress update."""

    title: str | None = None
    description: str | None = None
    model_config = frozen_config


class BashOutput(BaseModel):
    """Output from a bash command execution."""

    command: str | None = None
    output: str
    exit_code: int | None = None
    model_config = frozen_config


class SessionFailed(BaseModel):
    """The session failed."""

    reason: str
    model_config = frozen_config


class SessionCompleted(BaseModel):
    """The session was completed."""

    model_config = frozen_config


class GitPatch(BaseModel):
    """A patch in Git format."""

    unidiff_patch: str
    base_commit_id: str | None = None
    suggested_commit_message: str | None = None
    model_config = frozen_config


class ChangeSet(BaseModel):
    """A change set was produced."""

    source: str
    git_patch: GitPatch | None = None
    model_config = frozen_config


class Media(BaseModel):
    """A media output."""

    data: bytes
    mime_type: str
    model_config = frozen_config


class Artifact(BaseModel):
    """Artifact produced during an activity."""

    change_set: ChangeSet | None = None
    media: Media | None = None
    bash_output: BashOutput | None = None
    model_config = frozen_config


class Activity(BaseModel):
    """Represents an activity within a session."""

    name: str
    id: str
    description: str | None = None
    create_time: Instant
    originator: str  # 'agent' or 'user'
    agent_messaged: AgentMessaged | None = None
    user_messaged: UserMessaged | None = None
    plan_generated: PlanGenerated | None = None
    plan_approved: PlanApproved | None = None
    progress_updated: ProgressUpdated | None = None
    artifacts: list[Artifact] | None = None
    session_completed: SessionCompleted | None = None
    session_failed: SessionFailed | None = None
    model_config = frozen_config


class ListSourcesResponse(BaseModel):
    """Response from listing sources."""

    sources: list[Source]
    next_page_token: str | None = None
    model_config = frozen_config


class ListSessionsResponse(BaseModel):
    """Response from listing sessions."""

    sessions: list[Session] = Field(default_factory=list)
    next_page_token: str | None = None
    model_config = frozen_config


class ListActivitiesResponse(BaseModel):
    """Response from listing activities."""

    activities: list[Activity] = Field(default_factory=list)
    next_page_token: str | None = None
    model_config = frozen_config


class JulesContext(BaseModel):
    """Context passed between Click commands."""

    api_key: str | None = None
