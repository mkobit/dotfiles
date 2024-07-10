from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Fetch(Section):
    mirror: bool | None = None
    tags: bool | Literal["all", "autotag", "none"] | None = None
    prune: bool | Literal["true", "false", "tags"] | None = None
    prune_tags: bool | None = None
    unshallow: bool | None = None
    submodule: bool | Literal["none", "on-demand"] | None = None
    update_shallow: bool | None = None
    write_commit_graph: bool | None = None
