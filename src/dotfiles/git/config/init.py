from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from pathlib import Path
from typing import Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Init(Section):
    bare: bool | None = None
    default_branch: str | None = "main"
    template_dir: Path | None = None
    shared: bool | Literal["all", "group", "world", "everybody", "umask"] | None = None
    shared_repository: bool | None = None
    template: Path | None = None
