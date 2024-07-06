from typing import final
from src.dotfiles.git.config.section import Section


from dataclasses import dataclass


@dataclass(frozen=True)
@final
class Rebase(Section):
    stat: bool | None
    autoStash: bool | None
    autoSquash: bool | None
