from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from whenever import Instant

# Common configuration for immutable models
# Use alias_generator to convert snake_case (Python) to camelCase (JSON/API)
frozen_config = ConfigDict(
    frozen=True,
    alias_generator=to_camel,
    populate_by_name=True
)

class GitHubRepo(BaseModel):
    """
    Represents a GitHub repository.
    See: https://developers.google.com/jules/api/reference/rest/v1alpha/sources
    """
    owner: str
    repo: str
    model_config = frozen_config

class Source(BaseModel):
    """
    Represents a Jules source.
    See: https://developers.google.com/jules/api/reference/rest/v1alpha/sources
    """
    name: str
    id: str
    github_repo: GitHubRepo | None = None
    model_config = frozen_config

class GitHubRepoContext(BaseModel):
    """
    Context for a GitHub repository source.
    """
    starting_branch: str
    model_config = frozen_config

class SourceContext(BaseModel):
    """
    Context identifying the source for a session.
    """
    source: str
    github_repo_context: GitHubRepoContext | None = None
    model_config = frozen_config

class PullRequestOutput(BaseModel):
    """
    Output details for a Pull Request.
    """
    url: str
    title: str
    description: str
    model_config = frozen_config

class Output(BaseModel):
    """
    Generic output wrapper.
    """
    pull_request: PullRequestOutput | None = None
    model_config = frozen_config

class Session(BaseModel):
    """
    Represents a Jules session.
    See: https://developers.google.com/jules/api/reference/rest/v1alpha/sessions
    """
    name: str
    id: str
    title: str
    source_context: SourceContext
    prompt: str
    outputs: list[Output] | None = None
    create_time: Instant | None = None
    model_config = frozen_config

class PlanStep(BaseModel):
    """
    A single step in a plan.
    """
    id: str
    title: str
    index: int | None = None
    model_config = frozen_config

class Plan(BaseModel):
    """
    A generated plan containing steps.
    """
    id: str
    steps: list[PlanStep]
    model_config = frozen_config

class PlanGenerated(BaseModel):
    """
    Activity payload for a generated plan.
    """
    plan: Plan
    model_config = frozen_config

class PlanApproved(BaseModel):
    """
    Activity payload for an approved plan.
    """
    plan_id: str
    model_config = frozen_config

class ProgressUpdated(BaseModel):
    """
    Activity payload for a progress update.
    """
    title: str
    description: str | None = None
    model_config = frozen_config

class BashOutput(BaseModel):
    """
    Output from a bash command execution.
    """
    command: str | None = None
    output: str
    exit_code: int | None = None
    model_config = frozen_config

class Artifact(BaseModel):
    """
    Artifact produced during an activity.
    """
    bash_output: BashOutput | None = None
    model_config = frozen_config

class Activity(BaseModel):
    """
    Represents an activity within a session.
    See: https://developers.google.com/jules/api/reference/rest/v1alpha/sessions.activities
    """
    name: str
    id: str
    create_time: Instant
    originator: str  # 'agent' or 'user'
    plan_generated: PlanGenerated | None = None
    plan_approved: PlanApproved | None = None
    progress_updated: ProgressUpdated | None = None
    artifacts: list[Artifact] | None = None
    session_completed: dict[str, Any] | None = None
    model_config = frozen_config

class ListSourcesResponse(BaseModel):
    sources: list[Source]
    next_page_token: str | None = None
    model_config = frozen_config

class ListSessionsResponse(BaseModel):
    sessions: list[Session] = Field(default_factory=list)
    next_page_token: str | None = None
    model_config = frozen_config

class ListActivitiesResponse(BaseModel):
    activities: list[Activity] = Field(default_factory=list)
    next_page_token: str | None = None
    model_config = frozen_config
