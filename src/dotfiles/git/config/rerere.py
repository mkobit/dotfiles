from typing import final
from src.dotfiles.git.config.section import Section


from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
@final
class Rerere(Section):
    autoUpdate: bool | None
    enabled: bool | None
