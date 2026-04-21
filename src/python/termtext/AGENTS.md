# termtext

Type-safe terminal markup DSL built on PEP 750 t-strings.
Requires Python 3.14+.

## Architecture

- `color.py` — `NamedColor`, `RGBColor` (use `RGBColor.from_hex()`), `Color256`
- `attribute.py` — `SGR`, `FG`, `BG`, `Link` — all typed, no booleans
- `style.py` — `Style(frozenset[Attribute])` with ordered merge; last token wins for `FG`/`BG`/`Link`, `SGR` codes are additive
- `config.py` — `Config` with overridable named styles; all built-ins (`bold`, `red`, etc.) can be redefined
- `segment.py` — `Segment(EscapedText, Style)`; `EscapedText` is a `NewType` of `str`
- `term_text.py` — `TermText.render(template, *, config=)` entry point; `.to_ansi()` and `.to_plain()`

## Format spec mini-language

Tokens are space-separated and resolved via `Config.styles`.
`{name:bold red}` applies both.
`{path:link={url}}` — `link=<url>` is a special form for OSC 8 links.
Bare hex tokens (`{val:#f7768e}`) resolve directly to `FG(RGBColor.from_hex(...))`.
Unknown tokens raise `ValueError`.

## Constraints

Never store raw strings where a typed value is possible.
Do not add `HexColor` back — use `RGBColor.from_hex()`.
Do not add Rich as a dependency.
