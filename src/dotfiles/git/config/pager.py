from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, Mapping, final


@dataclass(frozen=True, kw_only=True)
@final
class Pager(Section):
    commands: Mapping[Literal["diff", "show", "log"], str]
