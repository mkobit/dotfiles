"""_summary_
See [Git documentation](https://git-scm.com/docs/git-config).
"""

import abc
from dataclasses import asdict, dataclass
import operator
from typing import Any, Mapping


@dataclass(frozen=True)
class Section(abc.ABC):
    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()

    def header(self) -> str:
        return f"[{self.name}]"

    def file_options(self) -> Mapping[str, Any]:
        view = asdict(self).items()
        camel_case = [(_snake_case_to_camel_case(k), v) for k, v in view]

        return dict(sorted(camel_case, key=operator.itemgetter(0)))


def _snake_case_to_camel_case(text: str) -> str:
    words = text.split("_")
    return "".join(words[0:1] + [w.title() for w in words[1::]])
