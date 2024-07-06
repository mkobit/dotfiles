from dataclasses import dataclass
from pathlib import Path
from typing import Literal, final

from .section import Section


@dataclass(frozen=True)
@final
class Core(Section):
    autocrlf: Literal["input"] | bool | None
    editor: str | None
    excludesFile: Path | None
    fsmonitor: bool | None
    eol: Literal["auto", "native", "input"] | bool | None
    safecrlf: Literal["warn"] | bool | None
