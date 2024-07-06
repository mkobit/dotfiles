from dataclasses import dataclass
from pathlib import Path
from typing import final

from src.dotfiles.git.config.section import Section


@dataclass(frozen=True)
@final
class IfGitDir:
    git_dir: Path
    case_insensitive: bool = False


@dataclass(frozen=True)
@final
class IfOnBranch:
    branch: str


@dataclass(frozen=True)
@final
class IfHasRemoteUrl:
    remote_url: str


IncludeIf = IfGitDir | IfOnBranch | IfHasRemoteUrl

@dataclass(frozen=True)
@final
class Include(Section):
    path: Path
    include_if: IncludeIf | None = None
