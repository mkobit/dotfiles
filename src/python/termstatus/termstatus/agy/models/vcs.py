from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VcsState:
    branch: str | None
    dirty: bool
    is_repo: bool
    upstream: str | None = None
    ahead: int = 0
    behind: int = 0
    origin_url: str | None = None
