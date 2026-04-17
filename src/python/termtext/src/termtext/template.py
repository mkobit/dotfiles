from typing import Any

from rich.console import Console

_console = Console()


class TermText:
    """Wrapper around a rendered rich markup string."""

    def __init__(self, markup: str):
        self.markup = markup

    def render_to_terminal(self, **kwargs: Any) -> None:
        """Renders the evaluated string to the terminal using Rich."""
        _console.print(self.markup, **kwargs)

    def __str__(self) -> str:
        return self.markup


def t(template: Any) -> TermText:
    """
    Template processor for PEP 750 string interpolation.
    Usage: t(t"hello {world}")
    Takes a string.templatelib.Template.
    """
    parts = []
    for i in range(len(template.strings)):
        parts.append(template.strings[i])
        if i < len(template.interpolations):
            parts.append(str(template.interpolations[i].value))

    markup = "".join(parts)
    return TermText(markup)


class LinkMarkup:
    """Represents a rich OSC 8 link."""

    def __init__(self, url: str, text: str):
        self.url = url
        self.text = text

    def __str__(self) -> str:
        return f"[link={self.url}]{self.text}[/link]"


def link(url: str, text: str) -> LinkMarkup:
    """Returns a rich markup link."""
    return LinkMarkup(url, text)


class ColorMarkup:
    """Represents a rich foreground color markup."""

    def __init__(self, color: str, text: str):
        self.color = color
        self.text = text

    def __str__(self) -> str:
        return f"[{self.color}]{self.text}[/{self.color}]"


def fg(color: str, text: str) -> ColorMarkup:
    """Styles text with a foreground color."""
    return ColorMarkup(color, text)


class BgColorMarkup:
    """Represents a rich background color markup."""

    def __init__(self, color: str, text: str):
        self.color = color
        self.text = text

    def __str__(self) -> str:
        return f"[on {self.color}]{self.text}[/on {self.color}]"


def bg(color: str, text: str) -> BgColorMarkup:
    """Styles text with a background color."""
    return BgColorMarkup(color, text)


# Common colors
def red(text: str) -> ColorMarkup:
    return fg("red", text)


def green(text: str) -> ColorMarkup:
    return fg("green", text)


def blue(text: str) -> ColorMarkup:
    return fg("blue", text)
