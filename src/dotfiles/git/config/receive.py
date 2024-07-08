from typing import final
from src.dotfiles.git.config.section import Section


from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
@final
class Receive(Section):
    fsck_objects: bool | None
