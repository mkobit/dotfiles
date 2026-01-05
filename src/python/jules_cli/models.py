from typing import List, Optional, Dict, Any, Union
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
    githubRepo: Optional[GitHubRepo] = None
    model_config = frozen_config

class GitHubRepoContext(BaseModel):
    startingBranch: str
    model_config = frozen_config

class SourceContext(BaseModel):
    source: str
    githubRepoContext: Optional[GitHubRepoContext] = None
    model_config = frozen_config

class PullRequestOutput(BaseModel):
    url: str
    title: str
    description: str
    model_config = frozen_config

class Output(BaseModel):
    pullRequest: Optional[PullRequestOutput] = None
    model_config = frozen_config

class Session(BaseModel):
    name: str
    id: str
    title: str
    sourceContext: SourceContext
    prompt: str
    outputs: Optional[List[Output]] = None
    createTime: Optional[str] = None
    model_config = frozen_config

class PlanStep(BaseModel):
    id: str
    title: str
    index: Optional[int] = None
    model_config = frozen_config

class Plan(BaseModel):
    id: str
    steps: List[PlanStep]
    model_config = frozen_config

class PlanGenerated(BaseModel):
    plan: Plan
    model_config = frozen_config

class PlanApproved(BaseModel):
    planId: str
    model_config = frozen_config

class ProgressUpdated(BaseModel):
    title: str
    description: Optional[str] = None
    model_config = frozen_config

class BashOutput(BaseModel):
    command: Optional[str] = None
    output: str
    exitCode: Optional[int] = None
    model_config = frozen_config

class Artifact(BaseModel):
    bashOutput: Optional[BashOutput] = None
    model_config = frozen_config

class Activity(BaseModel):
    name: str
    id: str
    createTime: str
    originator: str  # 'agent' or 'user'
    planGenerated: Optional[PlanGenerated] = None
    planApproved: Optional[PlanApproved] = None
    progressUpdated: Optional[ProgressUpdated] = None
    artifacts: Optional[List[Artifact]] = None
    sessionCompleted: Optional[Dict[str, Any]] = None
    model_config = frozen_config

class ListSourcesResponse(BaseModel):
    sources: List[Source]
    nextPageToken: Optional[str] = None
    model_config = frozen_config

class ListSessionsResponse(BaseModel):
    sessions: List[Session] = Field(default_factory=list)
    nextPageToken: Optional[str] = None
    model_config = frozen_config

class ListActivitiesResponse(BaseModel):
    activities: List[Activity] = Field(default_factory=list)
    nextPageToken: Optional[str] = None
    model_config = frozen_config
