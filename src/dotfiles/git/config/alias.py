from src.dotfiles.git.config.section import Section


from dataclasses import dataclass, field
from typing import Dict, final


@dataclass(frozen=True)
@final
class Alias(Section):
    aliases: Dict[str, str] = field(default_factory=dict)
