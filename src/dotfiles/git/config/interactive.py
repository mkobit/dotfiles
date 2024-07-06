from typing import final
from src.dotfiles.git.config.section import Section


from dataclasses import dataclass


@dataclass(frozen=True)
@final
class Interactive(Section):
    askPass: bool | None
    diffFilter: str | None
    patch: bool | None
    statusFormat: str | None
