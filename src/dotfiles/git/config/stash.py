from typing import final
from src.dotfiles.git.config.section import Section


from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
@final
class Stash(Section):
    show_include_untracked: bool | None = None
    show_patch: bool | None = None
    show_stat: bool | None = None
