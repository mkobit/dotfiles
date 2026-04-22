import pytest

from termtext import Color256, RGBColor


def test_rgb_color_out_of_bounds() -> None:
    with pytest.raises(ValueError, match="RGB component r=256 out of range 0-255"):
        RGBColor(256, 0, 0)
    with pytest.raises(ValueError, match="RGB component g=-1 out of range 0-255"):
        RGBColor(0, -1, 0)


def test_rgb_color_from_hex_invalid_chars() -> None:
    with pytest.raises(ValueError, match="Invalid hex color"):
        RGBColor.from_hex("#zzzzzz")


def test_rgb_color_from_hex_short_length() -> None:
    c = RGBColor.from_hex("#f80")
    assert c == RGBColor(255, 136, 0)


def test_rgb_color_from_hex_invalid_length() -> None:
    with pytest.raises(ValueError, match="Invalid hex color"):
        RGBColor.from_hex("#12")
    with pytest.raises(ValueError, match="Invalid hex color"):
        RGBColor.from_hex("#1234")
    with pytest.raises(ValueError, match="Invalid hex color"):
        RGBColor.from_hex("123456")


def test_color256_out_of_bounds() -> None:
    with pytest.raises(ValueError, match="256-color index 256 out of range 0-255"):
        Color256(256)
    with pytest.raises(ValueError, match="256-color index -1 out of range 0-255"):
        Color256(-1)
