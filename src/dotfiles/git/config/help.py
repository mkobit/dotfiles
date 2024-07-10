from src.dotfiles.git.config.section import Section


from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Literal, Mapping, final


@dataclass(frozen=True, kw_only=True)
@final
class Help(Section):
    autocorrect: timedelta | None = None
    format: Literal["man", "info", "web", "html"] | None = None
    all: bool | None = None
    verbose: bool | None = None
    version: bool | None = None

    def file_options(self) -> Mapping[str, Any]:
        file_options = dict(super().file_options())
        if self.autocorrect:
            total_seconds = self.autocorrect.total_seconds()
            seconds = int(total_seconds)
            tenths = int((total_seconds - seconds) * 10)
            file_options["autocorrect"] = f"{seconds}.{tenths}"
        return file_options
    # "autocorrect" to autocorrect?.let {
    #   totalMillis = it.toLong(DurationUnit.MILLISECONDS)
    #   seconds = totalMillis / 1000
    #   tenths = (totalMillis % 1000) / 100
    #   "$seconds.$tenths"
    # }
