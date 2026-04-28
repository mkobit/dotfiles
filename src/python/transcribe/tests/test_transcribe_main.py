from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from transcribe.main import cli
from transcribe.models import TranscriptionInfo, TranscriptionSegment
from transcribe.transcriber import FasterWhisperTranscriber


@pytest.fixture
def mock_transcriber() -> Generator[MagicMock, None, None]:
    with patch("transcribe.main.FasterWhisperTranscriber") as mock:
        yield mock


def test_main_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Transcribe audio files" in result.output


def test_main_default(mock_transcriber: MagicMock) -> None:
    instance = mock_transcriber.return_value

    segment = TranscriptionSegment(start=0.0, end=1.0, text="Hello")
    info = TranscriptionInfo(language="en", language_probability=1.0, duration=1.0)

    def segment_gen() -> Generator[TranscriptionSegment, None, None]:
        yield segment

    instance.transcribe.return_value = (segment_gen(), info)

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("test.wav", "w") as f:
            f.write("dummy")

        result = runner.invoke(cli, ["test.wav"])

        assert result.exit_code == 0
        assert "Hello" in result.output


def test_main_template_string(mock_transcriber: MagicMock) -> None:
    instance = mock_transcriber.return_value

    segment = TranscriptionSegment(start=0.0, end=1.0, text="Hello")
    info = TranscriptionInfo(language="en", language_probability=1.0, duration=1.0)

    def segment_gen() -> Generator[TranscriptionSegment, None, None]:
        yield segment

    instance.transcribe.return_value = (segment_gen(), info)

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("test.wav", "w") as f:
            f.write("dummy")

        result = runner.invoke(cli, ["test.wav", "--template", "custom: {{ segments[0].text }}"])

        assert result.exit_code == 0
        assert "custom: Hello" in result.output


def test_faster_whisper_transcriber_init() -> None:
    with patch("transcribe.transcriber.WhisperModel") as mock_model:
        t = FasterWhisperTranscriber()
        mock_model.assert_called_once_with("base", device="auto", compute_type="default")

        # Setup mock for transcribe method
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.99
        mock_info.duration = 10.0

        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 2.0
        mock_segment.text = "Mocked text"

        mock_model.return_value.transcribe.return_value = ([mock_segment], mock_info)

        # Transcribe
        segments_gen, info = t.transcribe("test.wav")
        mock_model.return_value.transcribe.assert_called_once_with("test.wav", language=None, beam_size=5)

        # Verify mapped info
        assert isinstance(info, TranscriptionInfo)
        assert info.language == "en"
        assert info.language_probability == 0.99
        assert info.duration == 10.0

        # Verify mapped segments
        segments = list(segments_gen)
        assert len(segments) == 1
        assert isinstance(segments[0], TranscriptionSegment)
        assert segments[0].start == 0.0
        assert segments[0].end == 2.0
        assert segments[0].text == "Mocked text"
