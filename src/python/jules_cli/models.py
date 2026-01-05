from typing import Any, Union
from pydantic import BaseModel, ConfigDict, Field

# Common configuration for immutable models
frozen_config = ConfigDict(frozen=True)

class GitHubRepo(BaseModel):
    owner: str
    repo: str
    model_config = frozen_config

class Source(BaseModel):
    name: str
    id: str
    githubRepo: GitHubRepo | None = None
    model_config = frozen_config

class GitHubRepoContext(BaseModel):
    startingBranch: str
    model_config = frozen_config

class SourceContext(BaseModel):
    source: str
    githubRepoContext: GitHubRepoContext | None = None
    model_config = frozen_config

class PullRequestOutput(BaseModel):
    url: str
    title: str
    description: str
    model_config = frozen_config

class Output(BaseModel):
    pullRequest: PullRequestOutput | None = None
    model_config = frozen_config

class Session(BaseModel):
    name: str
    id: str
    title: str
    sourceContext: SourceContext
    prompt: str
    outputs: list[Output] | None = None
    createTime: str | None = None
    model_config = frozen_config

class PlanStep(BaseModel):
    id: str
    title: str
    index: int | None = None
    model_config = frozen_config

class Plan(BaseModel):
    id: str
    steps: list[PlanStep]
    model_config = frozen_config

class PlanGenerated(BaseModel):
    plan: Plan
    model_config = frozen_config

class PlanApproved(BaseModel):
    planId: str
    model_config = frozen_config

class ProgressUpdated(BaseModel):
    title: str
    description: str | None = None
    model_config = frozen_config

class BashOutput(BaseModel):
    command: str | None = None
    output: str
    exitCode: int | None = None
    model_config = frozen_config

class Artifact(BaseModel):
    bashOutput: BashOutput | None = None
    model_config = frozen_config

class Activity(BaseModel):
    name: str
    id: str
    createTime: str
    originator: str  # 'agent' or 'user'
    planGenerated: PlanGenerated | None = None
    planApproved: PlanApproved | None = None
    progressUpdated: ProgressUpdated | None = None
    artifacts: list[Artifact] | None = None
    sessionCompleted: dict[str, Any] | None = None
    model_config = frozen_config

class ListSourcesResponse(BaseModel):
    sources: list[Source]
    nextPageToken: str | None = None
    model_config = frozen_config

class ListSessionsResponse(BaseModel):
    sessions: list[Session] = Field(default_factory=list)
    nextPageToken: str | None = None
    model_config = frozen_config

class ListActivitiesResponse(BaseModel):
    activities: list[Activity] = Field(default_factory=list)
    nextPageToken: str | None = None
    model_config = frozen_config
