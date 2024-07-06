from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True)
@final
class Fetch(Section):
    mirror: bool | None
    tags: bool | Literal["all", "autotag", "none"] | None
    prune: bool | Literal["true", "false", "tags"] | None
    pruneTags: bool | None
    unshallow: bool | None
    submodule: bool | Literal["none", "on-demand"] | None
    updateShallow: bool | None
    writeCommitGraph: bool | None
