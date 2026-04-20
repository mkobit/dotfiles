from __future__ import annotations

from dataclasses import dataclass, field

from termtext.attribute import FG, SGR
from termtext.color import NamedColor
from termtext.style import Style


def _default_styles() -> dict[str, Style]:
    return {
        # SGR attributes
        "bold": Style(frozenset({SGR.BOLD})),
        "dim": Style(frozenset({SGR.DIM})),
        "italic": Style(frozenset({SGR.ITALIC})),
        "underline": Style(frozenset({SGR.UNDERLINE})),
        "blink": Style(frozenset({SGR.BLINK})),
        "reverse": Style(frozenset({SGR.REVERSE})),
        "strikethrough": Style(frozenset({SGR.STRIKETHROUGH})),
        # named foreground colors
        "black": Style(frozenset({FG(NamedColor.BLACK)})),
        "red": Style(frozenset({FG(NamedColor.RED)})),
        "green": Style(frozenset({FG(NamedColor.GREEN)})),
        "yellow": Style(frozenset({FG(NamedColor.YELLOW)})),
        "blue": Style(frozenset({FG(NamedColor.BLUE)})),
        "magenta": Style(frozenset({FG(NamedColor.MAGENTA)})),
        "cyan": Style(frozenset({FG(NamedColor.CYAN)})),
        "white": Style(frozenset({FG(NamedColor.WHITE)})),
        "bright_black": Style(frozenset({FG(NamedColor.BRIGHT_BLACK)})),
        "bright_red": Style(frozenset({FG(NamedColor.BRIGHT_RED)})),
        "bright_green": Style(frozenset({FG(NamedColor.BRIGHT_GREEN)})),
        "bright_yellow": Style(frozenset({FG(NamedColor.BRIGHT_YELLOW)})),
        "bright_blue": Style(frozenset({FG(NamedColor.BRIGHT_BLUE)})),
        "bright_magenta": Style(frozenset({FG(NamedColor.BRIGHT_MAGENTA)})),
        "bright_cyan": Style(frozenset({FG(NamedColor.BRIGHT_CYAN)})),
        "bright_white": Style(frozenset({FG(NamedColor.BRIGHT_WHITE)})),
    }


@dataclass(frozen=True)
class Config:
    """
    Rendering configuration.

    styles: named style tokens resolved during format spec parsing.
            All built-in names (bold, red, etc.) are overridable.
    """

    styles: dict[str, Style] = field(default_factory=_default_styles)

    def resolve(self, name: str) -> Style | None:
        return self.styles.get(name)

    def with_styles(self, overrides: dict[str, Style]) -> Config:
        """Return a new Config with the given style overrides applied."""
        return Config(styles={**self.styles, **overrides})


DEFAULT_CONFIG = Config()
