from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Status(Section):
    relativePaths: bool | None
    short: bool | None
    branch: bool | None
    aheadBehind: bool | None
    renameLimit: int | None
    renames: Literal["copies"] | bool | None
    showStash: bool | None
    showUntrackedFiles: Literal["no", "normal", "all"] | None
    submoduleSummary: bool | None
