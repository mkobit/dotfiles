from typing import final
from src.dotfiles.git.config.section import Section


from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
@final
class Rerere(Section):
    auto_update: bool | None = None
    enabled: bool | None = None
