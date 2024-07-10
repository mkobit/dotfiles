from .section import Section

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Gpg(Section):
    program: str | None = None
    allowed_signers_file: Path | None = None
    sign: bool | None = None
    sort_order: Literal["unknown", "trusted", "valid", "bad", "untrusted"] | None = None
    verbose: bool | None = None
    use_agent: bool | None = None
    ssh_options: List[str] | None = None
