from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NamedColor(Enum):
    BLACK = "black"
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"
    WHITE = "white"
    BRIGHT_BLACK = "bright_black"
    BRIGHT_RED = "bright_red"
    BRIGHT_GREEN = "bright_green"
    BRIGHT_YELLOW = "bright_yellow"
    BRIGHT_BLUE = "bright_blue"
    BRIGHT_MAGENTA = "bright_magenta"
    BRIGHT_CYAN = "bright_cyan"
    BRIGHT_WHITE = "bright_white"


@dataclass(frozen=True)
class RGBColor:
    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        for name, val in (("r", self.r), ("g", self.g), ("b", self.b)):
            if not 0 <= val <= 255:
                raise ValueError(f"RGB component {name}={val} out of range 0-255")

    @classmethod
    def from_hex(cls, value: str) -> RGBColor:
        v = value.lstrip("#")
        valid_chars = all(c in "0123456789abcdefABCDEF" for c in v)
        if not (value.startswith("#") and len(v) in (3, 6) and valid_chars):
            raise ValueError(f"Invalid hex color: {value!r}")
        if len(v) == 3:
            v = "".join(c * 2 for c in v)
        return cls(int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))


@dataclass(frozen=True)
class Color256:
    index: int

    def __post_init__(self) -> None:
        if not 0 <= self.index <= 255:
            raise ValueError(f"256-color index {self.index} out of range 0-255")


Color = NamedColor | RGBColor | Color256
