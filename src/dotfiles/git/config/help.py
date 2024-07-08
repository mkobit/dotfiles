from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from datetime import timedelta
from typing import Literal, final


@dataclass(frozen=True, kw_only=True)
@final
class Help(Section):
    autocorrect: timedelta | None
    format: Literal["man", "info", "web", "html"] | None
    all: bool | None
    verbose: bool | None
    version: bool | None
    # "autocorrect" to autocorrect?.let {
    #   totalMillis = it.toLong(DurationUnit.MILLISECONDS)
    #   seconds = totalMillis / 1000
    #   tenths = (totalMillis % 1000) / 100
    #   "$seconds.$tenths"
    # }
