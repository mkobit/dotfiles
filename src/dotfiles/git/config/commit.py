from dataclasses import dataclass
from typing import final

from .section import Section


@dataclass(frozen=True, kw_only=True)
@final
class Commit(Section):
    gpg_sign: bool | None = None
    status: bool | None = None
    verbose: bool | None = None
