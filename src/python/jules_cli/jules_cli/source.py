from pydantic import BaseModel

from jules_cli.core import frozen_config


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


class ListSourcesResponse(BaseModel):
    """Response from listing sources."""

    sources: list[Source]
    next_page_token: str | None = None
    model_config = frozen_config
