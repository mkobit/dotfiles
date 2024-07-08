from .section import Section

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Gpg(Section):
    program: str | None
    allowedSignersFile: Path | None
    sign: bool | None
    sortOrder: Literal["unknown", "trusted", "valid", "bad", "untrusted"] | None
    verbose: bool | None
    useAgent: bool | None
    sshOptions: List[str] | None
