from dataclasses import dataclass
from typing import final

from .section import Section


@dataclass(frozen=True, kw_only=True)
@final
class Commit(Section):
    gpgSign: bool | None
    status: bool | None
    verbose: bool | None
