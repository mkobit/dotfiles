from dataclasses import dataclass
from typing import Literal, final

from .section import Section


@dataclass(frozen=True)
@final
class Column(Section):
    ui: Literal["always", "never", "auto"] | None
