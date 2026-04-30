from typing import Any

import pytest

from transcribe.formatter import Formatter
from transcribe.models import TranscriptionInfo, TranscriptionSegment


@pytest.fixture
def sample_segments() -> list[TranscriptionSegment]:
    return [
        TranscriptionSegment(start=0.0, end=1.5, text="Hello world"),
        TranscriptionSegment(start=1.5, end=3.0, text="This is a test"),
    ]


@pytest.fixture
def sample_info() -> TranscriptionInfo:
    return TranscriptionInfo(language="en", language_probability=0.99, duration=3.0)


def test_formatter_default(sample_segments: list[TranscriptionSegment], sample_info: TranscriptionInfo) -> None:
    result = Formatter.format_segments(sample_segments, sample_info)
    assert result == "Hello world\nThis is a test\n"


def test_formatter_jinja_string(sample_segments: list[TranscriptionSegment], sample_info: TranscriptionInfo) -> None:
    template = "{{ info.language }}: {% for seg in segments %}{{ seg.text }} {% endfor %}"
    result = Formatter.format_segments(sample_segments, sample_info, template_string=template)
    assert result == "en: Hello world This is a test "


def test_formatter_jinja_with_timestamp(
    sample_segments: list[TranscriptionSegment], sample_info: TranscriptionInfo
) -> None:
    template = "{% for seg in segments %}{{ format_timestamp(seg.start) }} -> {{ seg.text }}\n{% endfor %}"
    result = Formatter.format_segments(sample_segments, sample_info, template_string=template)
    expected = "00:00:00,000 -> Hello world\n00:00:01,500 -> This is a test\n"
    assert result == expected


def test_formatter_jinja_file(
    sample_segments: list[TranscriptionSegment], sample_info: TranscriptionInfo, tmp_path: Any
) -> None:
    template_content = "{% for seg in segments %}{{ seg.text }}{% if not loop.last %} | {% endif %}{% endfor %}"
    template_file = tmp_path / "template.j2"
    template_file.write_text(template_content)

    result = Formatter.format_segments(sample_segments, sample_info, template_file=str(template_file))
    assert result == "Hello world | This is a test"
