from dataclasses import dataclass
from pathlib import Path
from typing import final

from src.dotfiles.git.config.section import Section


@dataclass(frozen=True, kw_only=True)
@final
class IfGitDir:
    git_dir: Path
    case_insensitive: bool = False


@dataclass(frozen=True, kw_only=True)
@final
class IfOnBranch:
    branch: str


@dataclass(frozen=True, kw_only=True)
@final
class IfHasRemoteUrl:
    remote_url: str


IncludeIf = IfGitDir | IfOnBranch | IfHasRemoteUrl

@dataclass(frozen=True, kw_only=True)
@final
class Include(Section):
    path: Path
    include_if: IncludeIf | None = None
