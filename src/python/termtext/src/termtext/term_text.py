from __future__ import annotations

from dataclasses import dataclass
from string.templatelib import Interpolation, Template, convert
from typing import Literal

from termtext.attribute import BG, FG, SGR, Link
from termtext.color import Color, Color256, NamedColor, RGBColor
from termtext.config import DEFAULT_CONFIG, Config
from termtext.segment import EscapedText, Segment
from termtext.style import Style

_ESC = "\x1b"
_OSC = "\x1b]"
_ST = "\x1b\\"

_SGR_RESET = f"{_ESC}[0m"

_NAMED_FG: dict[NamedColor, int] = {
    NamedColor.BLACK: 30,
    NamedColor.RED: 31,
    NamedColor.GREEN: 32,
    NamedColor.YELLOW: 33,
    NamedColor.BLUE: 34,
    NamedColor.MAGENTA: 35,
    NamedColor.CYAN: 36,
    NamedColor.WHITE: 37,
    NamedColor.BRIGHT_BLACK: 90,
    NamedColor.BRIGHT_RED: 91,
    NamedColor.BRIGHT_GREEN: 92,
    NamedColor.BRIGHT_YELLOW: 93,
    NamedColor.BRIGHT_BLUE: 94,
    NamedColor.BRIGHT_MAGENTA: 95,
    NamedColor.BRIGHT_CYAN: 96,
    NamedColor.BRIGHT_WHITE: 97,
}
_NAMED_BG: dict[NamedColor, int] = {k: v + 10 for k, v in _NAMED_FG.items()}


def _color_sgr(color: Color, *, bg: bool = False) -> str:
    match color:
        case NamedColor():
            return str(_NAMED_BG[color] if bg else _NAMED_FG[color])
        case RGBColor():
            base = 48 if bg else 38
            return f"{base};2;{color.r};{color.g};{color.b}"
        case Color256():
            base = 48 if bg else 38
            return f"{base};5;{color.index}"


def _open_sequence(style: Style) -> str:
    codes: list[str] = []
    link_url: str | None = None

    for attr in style.attributes:
        match attr:
            case SGR():
                codes.append(str(attr.value))
            case FG(color):
                codes.append(_color_sgr(color, bg=False))
            case BG(color):
                codes.append(_color_sgr(color, bg=True))
            case Link(url):
                link_url = url

    return "".join(
        [
            f"{_ESC}[{';'.join(codes)}m" if codes else "",
            f"{_OSC}8;;{link_url}{_ST}" if link_url is not None else "",
        ]
    )


def _close_sequence(style: Style) -> str:
    has_sgr = any(isinstance(a, (SGR, FG, BG)) for a in style.attributes)
    has_link = any(isinstance(a, Link) for a in style.attributes)
    return "".join(
        [
            _SGR_RESET if has_sgr else "",
            f"{_OSC}8;;{_ST}" if has_link else "",
        ]
    )


def _parse_format_spec(spec: str, config: Config) -> Style:
    """Parse a space-separated format spec into a Style.

    Tokens are resolved via config. Special form `link=<url>` creates a
    Link attribute directly. Last token wins on type conflicts.
    """
    if not spec:
        return Style()

    def resolve_token(token: str) -> Style:
        if token.startswith("link="):
            return Style(frozenset({Link(token[len("link=") :])}))
        resolved = config.resolve(token)
        if resolved is not None:
            return resolved
        if token.startswith("#"):
            return Style(frozenset({FG(RGBColor.from_hex(token))}))
        raise ValueError(f"Unknown style token: {token!r}")

    result = Style()
    for token in spec.split():
        result = result.merge(resolve_token(token))
    return result


def _to_text(value: object, conversion: Literal["r", "s", "a"] | None) -> str:
    if conversion is not None:
        return str(convert(value, conversion))
    return str(value)


@dataclass(frozen=True)
class TermText:
    segments: tuple[Segment, ...]

    @classmethod
    def render(cls, template: Template, *, config: Config | None = None) -> TermText:
        cfg = config or DEFAULT_CONFIG
        empty_style = Style()

        def to_segment(item: str | Interpolation) -> Segment:
            match item:
                case str():
                    return Segment(EscapedText(item), empty_style)
                case Interpolation(value, _, conversion, format_spec):
                    return Segment(
                        EscapedText(_to_text(value, conversion)),
                        _parse_format_spec(format_spec, cfg),
                    )

        return cls(tuple(to_segment(item) for item in template))

    def to_ansi(self) -> str:
        return "".join(
            segment.text
            if not segment.style.attributes
            else "".join(
                [
                    _open_sequence(segment.style),
                    segment.text,
                    _close_sequence(segment.style),
                ]
            )
            for segment in self.segments
        )

    def to_plain(self) -> str:
        return "".join(s.text for s in self.segments)
