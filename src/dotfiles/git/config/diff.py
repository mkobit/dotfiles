from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final

from src.dotfiles.git.config.values import Color


@dataclass(frozen=True, kw_only=True)
@final
class Diff(Section):
    compaction_heuristic: bool | None = None
    indent_heuristic: bool | None = None
    algorithm: Literal["myers", "histogram", "minimal", "patience", "none"] | None = (
        None
    )
    ws_error_highlight: Literal["none", "all", "indentation", "trailing"] | None = None
    context: int | None = None
    inter_hunk_context: int | None = None
    renames: bool | Literal["copies", "copy"] | None = None
    rerere: bool | None = None
    show_func: bool | None = None
    show_notes: bool | None = None
    suppress_blank_empty: bool | None = None
    colorMoved: Color | None = None
    mnemonic_prefix: bool | None = None
