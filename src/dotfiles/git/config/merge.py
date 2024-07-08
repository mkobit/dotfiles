from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Merge(Section):
    ff: bool | Literal["only"] | None
    conflictStyle: Literal["merge", "diff3", "zdiff3"] | None
    commit: bool | None
    verifySignatures: bool | None
    restrictCommitTypes: str | None
    renameLimit: int | None
    allowUnrelatedHistories: bool | None
    showMergeErrors: bool | None
    defaultToUpstream: bool | None
    log: bool | None
