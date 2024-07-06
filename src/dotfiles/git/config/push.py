from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True)
@final
class Push(Section):
    autoSetupRemote: bool | None
    default: Literal["nothing", "current", "upstream", "simple", "matching"] | None
    followTags: bool | None
    gpgSign: Literal["if-asked"] | bool | None
    recurseSubmodules: Literal["check", "on-demand", "only", "no"] | None
    useForceIfIncludes: bool | None
    negotiate: bool | None
