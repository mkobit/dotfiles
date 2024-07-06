from typing import final
from src.dotfiles.git.config.section import Section


from dataclasses import dataclass


@dataclass(frozen=True)
@final
class User(Section):
    email: str | None
    user_name: str | None  # todo: convert output key to name
    signing_key: str | None
    use_config_only: bool | None
