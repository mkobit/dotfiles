import abc
from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Any, Mapping


@dataclass(frozen=True)
class Section(abc.ABC):
    @property
    def name(self) -> str:
        return self.__class__.__name__.lower()

    def header(self) -> str:
        return f"[{self.name}]"

    def file_options(self) -> Mapping[str, Any]:
        return {_snake_to_camel(k): _convert_value(v) for k, v in asdict(self).items()}

def _convert_value(v: Any) -> Any:
    match v:
        case str():
            return v
        case list():
            return v.join(' ')
        case bool():
            return 'true' if v else 'false'
        case int():
            return v
        case timedelta():
            return v.total_seconds()
        case _:
            return str(v)


def _snake_to_camel(text: str) -> str:
    words = text.split("_")
    return "".join(words[0:1] + [w.title() for w in words[1::]])
