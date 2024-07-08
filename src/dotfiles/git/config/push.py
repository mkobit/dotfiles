from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Push(Section):
    auto_setup_remote: bool | None = None
    default: Literal["nothing", "current", "upstream", "simple", "matching"] | None = None
    follow_tags: bool | None = None
    gpg_sign: Literal["if-asked"] | bool | None = None
    recurse_submodules: Literal["check", "on-demand", "only", "no"] | None = None
    use_force_if_includes: bool | None = None
    negotiate: bool | None = None
