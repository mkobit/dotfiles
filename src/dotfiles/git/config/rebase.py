from typing import final
from src.dotfiles.git.config.section import Section


from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
@final
class Rebase(Section):
    stat: bool | None = None
    auto_stash: bool | None = None
    auto_squash: bool | None = None
