from collections import namedtuple
from typing import Any

import pytest

from transcribe.formatter import Formatter

# Mock segment and info
Segment = namedtuple("Segment", ["start", "end", "text"])
Info = namedtuple("Info", ["language", "language_probability", "duration"])


@pytest.fixture
def sample_segments() -> list[Any]:
    return [Segment(0.0, 1.5, "Hello world"), Segment(1.5, 3.0, "This is a test")]


@pytest.fixture
def sample_info() -> Any:
    return Info("en", 0.99, 3.0)


def test_formatter_default(sample_segments: list[Any], sample_info: Any) -> None:
    result = Formatter.format_segments(sample_segments, sample_info)
    assert result == "Hello world\nThis is a test\n"


def test_formatter_jinja_string(sample_segments: list[Any], sample_info: Any) -> None:
    template = "{{ info.language }}: {% for seg in segments %}{{ seg.text }} {% endfor %}"
    result = Formatter.format_segments(sample_segments, sample_info, template_string=template)
    assert result == "en: Hello world This is a test "


def test_formatter_jinja_with_timestamp(sample_segments: list[Any], sample_info: Any) -> None:
    template = "{% for seg in segments %}{{ format_timestamp(seg.start) }} -> {{ seg.text }}\n{% endfor %}"
    result = Formatter.format_segments(sample_segments, sample_info, template_string=template)
    expected = "00:00:00,000 -> Hello world\n00:00:01,500 -> This is a test\n"
    assert result == expected


def test_formatter_jinja_file(sample_segments: list[Any], sample_info: Any, tmp_path: Any) -> None:
    template_content = "{% for seg in segments %}{{ seg.text }}{% if not loop.last %} | {% endif %}{% endfor %}"
    template_file = tmp_path / "template.j2"
    template_file.write_text(template_content)

    result = Formatter.format_segments(sample_segments, sample_info, template_file=str(template_file))
    assert result == "Hello world | This is a test"
