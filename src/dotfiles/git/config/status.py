from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Status(Section):
    relative_paths: bool | None = None
    short: bool | None = None
    branch: bool | None = None
    ahead_behind: bool | None = None
    renameLimit: int | None = None
    renames: Literal["copies"] | bool | None = None
    show_stash: bool | None = None
    show_untracked_files: Literal["no", "normal", "all"] | None = None
    submodule_summary: bool | None = None
