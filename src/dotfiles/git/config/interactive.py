from typing import final
from src.dotfiles.git.config.section import Section


from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
@final
class Interactive(Section):
    askPass: bool | None = None
    diffFilter: str | None = None
    patch: bool | None = None
    statusFormat: str | None = None
