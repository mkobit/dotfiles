from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from termtext.color import Color


class SGR(Enum):
    """ANSI Select Graphic Rendition codes."""

    BOLD = 1
    DIM = 2
    ITALIC = 3
    UNDERLINE = 4
    BLINK = 5
    REVERSE = 7
    STRIKETHROUGH = 9


@dataclass(frozen=True)
class FG:
    """Foreground color attribute."""

    color: Color


@dataclass(frozen=True)
class BG:
    """Background color attribute."""

    color: Color


@dataclass(frozen=True)
class Link:
    """OSC 8 hyperlink attribute."""

    url: str


Attribute = SGR | FG | BG | Link
