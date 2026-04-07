from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from transcribe.main import main


@pytest.fixture
def mock_transcriber() -> Generator[MagicMock, None, None]:
    with patch("transcribe.main.Transcriber") as mock:
        yield mock


def test_main_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Transcribe audio files" in result.output


def test_main_default(mock_transcriber: MagicMock) -> None:
    instance = mock_transcriber.return_value

    segment = MagicMock()
    segment.start = 0.0
    segment.end = 1.0
    segment.text = "Hello"

    info = MagicMock()
    info.language = "en"
    info.language_probability = 1.0
    info.duration = 1.0

    def segment_gen() -> Generator[Any, None, None]:
        yield segment

    instance.transcribe.return_value = (segment_gen(), info)

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("test.wav", "w") as f:
            f.write("dummy")

        result = runner.invoke(main, ["test.wav"])

        assert result.exit_code == 0
        assert "Hello" in result.output


def test_main_template_string(mock_transcriber: MagicMock) -> None:
    instance = mock_transcriber.return_value

    segment = MagicMock()
    segment.start = 0.0
    segment.end = 1.0
    segment.text = "Hello"

    info = MagicMock()
    info.language = "en"
    info.language_probability = 1.0
    info.duration = 1.0

    def segment_gen() -> Generator[Any, None, None]:
        yield segment

    instance.transcribe.return_value = (segment_gen(), info)

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("test.wav", "w") as f:
            f.write("dummy")

        result = runner.invoke(
            main, ["test.wav", "--template-string", "custom: {{ segments[0].text }}"]
        )

        assert result.exit_code == 0
        assert "custom: Hello" in result.output
