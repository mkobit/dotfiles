from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True)
@final
class Pull(Section):
    ff: Literal["only"] | bool | None
    rebase: Literal["interactive", "merges", "preserve"] | bool | None
