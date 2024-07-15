from src.dotfiles.git.config.section import Section


from dataclasses import dataclass, field
from typing import Any, Mapping, final


@dataclass(frozen=True)
@final
class Alias(Section):
    aliases: Mapping[str, str] = field(default_factory=dict)

    def file_options(self) -> Mapping[str, Any]:
        return dict(self.aliases)
