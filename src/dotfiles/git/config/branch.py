from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from typing import Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Branch(Section):
    autoSetUpRebase: Literal["never", "local", "remote", "always"] | None
    sort: (
        str | None
    )  # todo: change to field names - https://git-scm.com/docs/git-for-each-ref#_field_names
