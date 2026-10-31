import pytest

from termtext.color import Color256, RGBColor


@pytest.mark.parametrize(
    ("components", "match"),
    [
        ((256, 0, 0), "RGB component r=256 out of range 0-255"),
        ((0, -1, 0), "RGB component g=-1 out of range 0-255"),
    ],
)
def test_rgb_color_out_of_bounds(components: tuple[int, int, int], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        RGBColor(*components)


@pytest.mark.parametrize("invalid_hex", ["#zzzzzz", "#12", "#1234", "123456"])
def test_rgb_color_from_hex_invalid(invalid_hex: str) -> None:
    with pytest.raises(ValueError, match="Invalid hex color"):
        RGBColor.from_hex(invalid_hex)


def test_rgb_color_from_hex_short_length() -> None:
    c = RGBColor.from_hex("#f80")
    assert c == RGBColor(255, 136, 0)


@pytest.mark.parametrize(
    ("index", "match"),
    [
        (256, "256-color index 256 out of range 0-255"),
        (-1, "256-color index -1 out of range 0-255"),
    ],
)
def test_color256_out_of_bounds(index: int, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        Color256(index)
