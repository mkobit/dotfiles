from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

from termtext.style import Style

EscapedText = NewType("EscapedText", str)


@dataclass(frozen=True)
class Segment:
    """A run of escaped text with an associated style."""

    text: EscapedText
    style: Style
