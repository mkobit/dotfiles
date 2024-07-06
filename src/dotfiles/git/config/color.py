from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True)
@final
class Color(Section):
    branch: bool | Literal["always"] | None
    status: bool | Literal["always"] | None
    ui: bool | Literal["always"] | None
