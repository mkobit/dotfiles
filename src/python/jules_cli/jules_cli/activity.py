from pydantic import BaseModel, Field
from whenever import Instant

from jules_cli.core import frozen_config


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


class ListActivitiesResponse(BaseModel):
    """Response from listing activities."""

    activities: list[Activity] = Field(default_factory=list)
    next_page_token: str | None = None
    model_config = frozen_config
