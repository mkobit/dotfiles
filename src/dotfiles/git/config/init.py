from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from pathlib import Path
from typing import Literal, final


@dataclass(frozen=True)
@final
class Init(Section):
    template_dir: Path | None
    bare: bool | None
    shared: bool | Literal["all", "group", "world", "everybody", "umask"] | None
    shared_repository: bool | None
    template: Path | None
    default_branch: str | None = "main"
