"""_summary_
See [Git documentation](https://git-scm.com/docs/git-config).
"""

from dataclasses import dataclass
from typing import Literal, Union, final

GitColor = Union[
    Literal["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"], str
]


@dataclass(frozen=True)
class Section:
    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()

