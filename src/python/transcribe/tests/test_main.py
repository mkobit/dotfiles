import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from src.python.transcribe.main import main
from typing import Generator, Any

@pytest.fixture
def mock_transcriber() -> Generator[MagicMock, None, None]:
    with patch("src.python.transcribe.main.Transcriber") as mock:
        yield mock

def test_main_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Transcribe audio files" in result.output

def test_main_default(mock_transcriber: MagicMock) -> None:
    # Setup mock
    instance = mock_transcriber.return_value

    # Mock return values
    Segment = MagicMock()
    Segment.start = 0.0
    Segment.end = 1.0
    Segment.text = "Hello"

    Info = MagicMock()
    Info.language = "en"
    Info.language_probability = 1.0
    Info.duration = 1.0

    # Mock generator
    def segment_gen() -> Generator[Any, None, None]:
        yield Segment

    instance.transcribe.return_value = (segment_gen(), Info)

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("test.wav", "w") as f:
            f.write("dummy")

        result = runner.invoke(main, ["test.wav"])

        assert result.exit_code == 0
        assert "Hello" in result.output

def test_main_template_string(mock_transcriber: MagicMock) -> None:
    # Setup mock
    instance = mock_transcriber.return_value

    # Mock return values
    Segment = MagicMock()
    Segment.start = 0.0
    Segment.end = 1.0
    Segment.text = "Hello"

    Info = MagicMock()
    Info.language = "en"
    Info.language_probability = 1.0
    Info.duration = 1.0

    # Mock generator
    def segment_gen() -> Generator[Any, None, None]:
        yield Segment

    instance.transcribe.return_value = (segment_gen(), Info)

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("test.wav", "w") as f:
            f.write("dummy")

        result = runner.invoke(main, ["test.wav", "--template-string", "custom: {{ segments[0].text }}"])

        assert result.exit_code == 0
        assert "custom: Hello" in result.output
