from typing import Any, Mapping, final
from src.dotfiles.git.config.section import Section


from dataclasses import dataclass


@dataclass(frozen=True)
@final
class User(Section):
    email: str | None = None
    user_name: str | None = None  # todo: convert output key to name
    signing_key: str | None = None
    use_config_only: bool | None = None

    def file_options(self) -> Mapping[str, Any]:
        options = super().file_options()
        return {"name" if k == "userName" else k: v for k, v in options.items()}
