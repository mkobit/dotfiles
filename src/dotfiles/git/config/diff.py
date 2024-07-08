from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Diff(Section):
    compactionHeuristic: bool | None
    indentHeuristic: bool | None
    algorithm: Literal["myers", "histogram", "minimal", "patience", "none"] | None
    wsErrorHighlight: Literal["none", "all", "indentation", "trailing"] | None
    context: int | None
    interHunkContext: int | None
    renames: bool | Literal["copies", "copy"] | None
    rerere: bool | None
    showFunc: bool | None
    showNotes: bool | None
    suppressBlankEmpty: bool | None
