from dataclasses import dataclass
from pathlib import Path
from typing import Literal, final

from .section import Section


@dataclass(frozen=True, kw_only=True)
@final
class Core(Section):
    autocrlf: Literal["input"] | bool | None = None
    editor: str | None = None
    excludes_file: Path | None = None
    fsmonitor: bool | None = None
    eol: Literal["auto", "native", "input"] | bool | None = None
    safecrlf: Literal["warn"] | bool | None = None
