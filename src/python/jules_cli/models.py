from enum import Enum, StrEnum, auto
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from whenever import Instant

# Common configuration for immutable models
# Use alias_generator to convert snake_case (Python) to camelCase (JSON/API)
frozen_config = ConfigDict(frozen=True, alias_generator=to_camel, populate_by_name=True)


class GitHubBranch(BaseModel):
    """
    A GitHub branch.
    See: https://jules.google/docs/api/reference/types#githubbranch
    """

    display_name: str
    model_config = frozen_config


class GitHubRepo(BaseModel):
    """
    Represents a GitHub repository.
    See: https://jules.google/docs/api/reference/types#githubrepo
    """

    owner: str
    repo: str
    is_private: bool | None = None
    default_branch: GitHubBranch | None = None
    branches: list[GitHubBranch] | None = None
    model_config = frozen_config


class Source(BaseModel):
    """
    Represents a Jules source.
    See: https://jules.google/docs/api/reference/types#source
    """

    name: str
    id: str
    github_repo: GitHubRepo | None = None
    model_config = frozen_config


class GitHubRepoContext(BaseModel):
    """
    Context for a GitHub repository source.
    See: https://jules.google/docs/api/reference/types#githubrepocontext
    """

    starting_branch: str
    model_config = frozen_config


class SourceContext(BaseModel):
    """
    Context identifying the source for a session.
    See: https://jules.google/docs/api/reference/types#sourcecontext
    """

    source: str
    github_repo_context: GitHubRepoContext | None = None
    model_config = frozen_config


class AutomationMode(StrEnum):
    """
    Automation modes for a session.
    See: https://jules.google/docs/api/reference/types#automationmode
    """

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
        return name

    AUTOMATION_MODE_UNSPECIFIED = auto()
    AUTO_CREATE_PR = auto()


class CreateSessionRequest(BaseModel):
    """
    Request body for creating a session.
    See: https://jules.google/docs/api/reference/sessions#create
    """

    prompt: str
    source_context: SourceContext
    automation_mode: AutomationMode | None = None
    title: str | None = None
    require_plan_approval: bool | None = None
    model_config = frozen_config


class PullRequest(BaseModel):
    """
    Output details for a Pull Request.
    See: https://jules.google/docs/api/reference/types#pullrequest
    """

    url: str
    title: str
    description: str
    model_config = frozen_config


class SessionOutput(BaseModel):
    """
    Generic output wrapper.
    See: https://jules.google/docs/api/reference/types#sessionoutput
    """

    pull_request: PullRequest | None = None
    model_config = frozen_config


class SessionState(StrEnum):
    """
    State of a session.
    See: https://jules.google/docs/api/reference/types#sessionstate
    """

    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[Any]
    ) -> Any:
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
    """
    Represents a Jules session.
    See: https://jules.google/docs/api/reference/types#session
    """

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
    """
    A single step in a plan.
    See: https://jules.google/docs/api/reference/types#planstep
    """

    id: str
    title: str
    description: str | None = None
    index: int | None = None
    model_config = frozen_config


class Plan(BaseModel):
    """
    A generated plan containing steps.
    See: https://jules.google/docs/api/reference/types#plan
    """

    id: str
    steps: list[PlanStep]
    create_time: Instant | None = None
    model_config = frozen_config


class UserMessaged(BaseModel):
    """
    The user posted a message.
    See: https://jules.google/docs/api/reference/types#usermessaged
    """

    user_message: str
    model_config = frozen_config


class AgentMessaged(BaseModel):
    """
    The agent posted a message.
    See: https://jules.google/docs/api/reference/types#agentmessaged
    """

    agent_message: str
    model_config = frozen_config


class PlanGenerated(BaseModel):
    """
    Activity payload for a generated plan.
    See: https://jules.google/docs/api/reference/types#plangenerated
    """

    plan: Plan
    model_config = frozen_config


class PlanApproved(BaseModel):
    """
    Activity payload for an approved plan.
    See: https://jules.google/docs/api/reference/types#planapproved
    """

    plan_id: str
    model_config = frozen_config


class ProgressUpdated(BaseModel):
    """
    Activity payload for a progress update.
    See: https://jules.google/docs/api/reference/types#progressupdated
    """

    title: str
    description: str | None = None
    model_config = frozen_config


class BashOutput(BaseModel):
    """
    Output from a bash command execution.
    See: https://jules.google/docs/api/reference/types#bashoutput
    """

    command: str | None = None
    output: str
    exit_code: int | None = None
    model_config = frozen_config


class SessionFailed(BaseModel):
    """
    The session failed.
    See: https://jules.google/docs/api/reference/types#sessionfailed
    """

    reason: str
    model_config = frozen_config


class SessionCompleted(BaseModel):
    """
    The session was completed.
    See: https://jules.google/docs/api/reference/types#sessioncompleted
    """

    model_config = frozen_config


class GitPatch(BaseModel):
    """
    A patch in Git format.
    See: https://jules.google/docs/api/reference/types#gitpatch
    """

    unidiff_patch: str
    base_commit_id: str
    suggested_commit_message: str
    model_config = frozen_config


class ChangeSet(BaseModel):
    """
    A change set was produced.
    See: https://jules.google/docs/api/reference/types#changeset
    """

    source: str
    git_patch: GitPatch | None = None
    model_config = frozen_config


class Media(BaseModel):
    """
    A media output.
    See: https://jules.google/docs/api/reference/types#media
    """

    data: bytes
    mime_type: str
    model_config = frozen_config


class Artifact(BaseModel):
    """
    Artifact produced during an activity.
    See: https://jules.google/docs/api/reference/types#artifact
    """

    change_set: ChangeSet | None = None
    media: Media | None = None
    bash_output: BashOutput | None = None
    model_config = frozen_config


class Activity(BaseModel):
    """
    Represents an activity within a session.
    See: https://jules.google/docs/api/reference/types#activity
    """

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
    """
    Response from listing sources.
    See: https://jules.google/docs/api/reference/types#listsourcesresponse
    """

    sources: list[Source]
    next_page_token: str | None = None
    model_config = frozen_config


class ListSessionsResponse(BaseModel):
    """
    Response from listing sessions.
    See: https://jules.google/docs/api/reference/types#listsessionsresponse
    """

    sessions: list[Session] = Field(default_factory=list)
    next_page_token: str | None = None
    model_config = frozen_config


class ListActivitiesResponse(BaseModel):
    """
    Response from listing activities.
    See: https://jules.google/docs/api/reference/types#listactivitiesresponse
    """

    activities: list[Activity] = Field(default_factory=list)
    next_page_token: str | None = None
    model_config = frozen_config


class JulesContext(BaseModel):
    """
    Context passed between Click commands.
    """

    api_key: str | None = None
