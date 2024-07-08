from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Pull(Section):
    ff: Literal["only"] | bool | None = None
    rebase: Literal["interactive", "merges", "preserve"] | bool | None = None
