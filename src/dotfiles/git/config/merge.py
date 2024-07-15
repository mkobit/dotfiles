from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Merge(Section):
    ff: bool | Literal["only"] | None = None
    conflict_style: Literal["merge", "diff3", "zdiff3"] | None = None
    commit: bool | None = None
    verify_signatures: bool | None = None
    restrict_commit_types: str | None = None
    rename_limit: int | None = None
    allow_unrelated_histories: bool | None = None
    show_merge_errors: bool | None = None
    default_to_upstream: bool | None = None
    log: bool | None = None
