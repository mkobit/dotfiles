import pytest

from termtext import BG, FG, SGR, Config, Link, NamedColor, RGBColor, Style, TermText


def test_plain_literal() -> None:
    tt = TermText.render(t"hello world")
    assert tt.to_plain() == "hello world"


def test_interpolation_no_style() -> None:
    name = "alice"
    tt = TermText.render(t"hello {name}")
    assert tt.to_plain() == "hello alice"


def test_interpolation_bold() -> None:
    name = "alice"
    tt = TermText.render(t"hello {name:bold}")
    assert tt.to_plain() == "hello alice"
    assert any(SGR.BOLD in s.style.attributes for s in tt.segments)


def test_interpolation_fg_color() -> None:
    count = 3
    tt = TermText.render(t"found {count:red} errors")
    assert tt.to_plain() == "found 3 errors"
    styled = next(s for s in tt.segments if s.text == "3")
    assert FG(NamedColor.RED) in styled.style.attributes


def test_interpolation_combined_style() -> None:
    msg = "oops"
    tt = TermText.render(t"{msg:bold red}")
    styled = tt.segments[0]
    assert FG(NamedColor.RED) in styled.style.attributes
    assert SGR.BOLD in styled.style.attributes


def test_interpolation_hex_color() -> None:
    val = "hi"
    tt = TermText.render(t"{val:#f7768e}")
    styled = tt.segments[0]
    assert FG(RGBColor.from_hex("#f7768e")) in styled.style.attributes


def test_interpolation_link() -> None:
    label = "click here"
    url = "https://example.com"
    tt = TermText.render(t"{label:link={url}}")
    styled = tt.segments[0]
    assert Link("https://example.com") in styled.style.attributes


def test_interpolation_bg_color() -> None:
    val = "hi"
    highlight = Style(frozenset({BG(NamedColor.CYAN)}))
    config = Config().with_styles({"highlight": highlight})
    tt = TermText.render(t"{val:highlight}", config=config)
    styled = tt.segments[0]
    assert BG(NamedColor.CYAN) in styled.style.attributes


def test_config_override_bold() -> None:
    """bold can be redefined to mean something entirely different."""
    val = "text"
    config = Config().with_styles({"bold": Style(frozenset({FG(RGBColor.from_hex("#7aa2f7")), SGR.UNDERLINE}))})
    tt = TermText.render(t"{val:bold}", config=config)
    styled = tt.segments[0]
    assert FG(RGBColor.from_hex("#7aa2f7")) in styled.style.attributes
    assert SGR.UNDERLINE in styled.style.attributes
    assert SGR.BOLD not in styled.style.attributes


def test_unknown_style_token_raises() -> None:
    val = "x"
    with pytest.raises(ValueError, match="Unknown style token"):
        TermText.render(t"{val:nonexistent_token}")


def test_to_ansi_unstyled() -> None:
    tt = TermText.render(t"plain text")
    assert tt.to_ansi() == "plain text"


def test_to_ansi_bold() -> None:
    val = "hi"
    tt = TermText.render(t"{val:bold}")
    ansi = tt.to_ansi()
    assert "\x1b[" in ansi
    assert "hi" in ansi
    assert "\x1b[0m" in ansi


def test_last_fg_wins() -> None:
    """When two fg colors are specified, last one wins."""
    val = "x"
    tt = TermText.render(t"{val:blue red}")
    styled = tt.segments[0]
    assert FG(NamedColor.RED) in styled.style.attributes
    assert FG(NamedColor.BLUE) not in styled.style.attributes


def test_multiple_sgr_additive() -> None:
    """Multiple SGR codes (bold + italic) both survive merging."""
    val = "x"
    tt = TermText.render(t"{val:bold italic}")
    styled = tt.segments[0]
    assert SGR.BOLD in styled.style.attributes
    assert SGR.ITALIC in styled.style.attributes
