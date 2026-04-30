from pydantic import BaseModel


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
    stash_count: int = 0
