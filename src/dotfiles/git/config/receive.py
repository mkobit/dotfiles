from typing import final
from src.dotfiles.git.config.section import Section


from dataclasses import dataclass


@dataclass(frozen=True)
@final
class Receive(Section):
    fsckObjects: bool | None
