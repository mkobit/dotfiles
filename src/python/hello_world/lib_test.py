"""Tests for hello_world library functions."""

import io
import sys
from pathlib import Path

import pytest

from src.python.hello_world.lib import Logger, generate_greetings, write_output
from src.python.hello_world.models import AppConfig, Greeting, LogLevel


class TestLogger:
    """Tests for Logger class."""

    def test_logger_info_level(self) -> None:
        """Test logger at INFO level."""
        output = io.StringIO()
        config = AppConfig(log_level=LogLevel.INFO)
        logger = Logger(config, output)

        logger.debug("debug msg")
        logger.info("info msg")
        logger.warning("warning msg")
        logger.error("error msg")

        result = output.getvalue()
        assert "debug msg" not in result  # Should be filtered
        assert "[INFO] info msg" in result
        assert "[WARNING] warning msg" in result
        assert "[ERROR] error msg" in result

    def test_logger_debug_level(self) -> None:
        """Test logger at DEBUG level shows all messages."""
        output = io.StringIO()
        config = AppConfig(log_level=LogLevel.DEBUG)
        logger = Logger(config, output)

        logger.debug("debug msg")
        logger.info("info msg")

        result = output.getvalue()
        assert "[DEBUG] debug msg" in result
        assert "[INFO] info msg" in result

    def test_logger_error_level(self) -> None:
        """Test logger at ERROR level filters most messages."""
        output = io.StringIO()
        config = AppConfig(log_level=LogLevel.ERROR)
        logger = Logger(config, output)

        logger.debug("debug msg")
        logger.info("info msg")
        logger.warning("warning msg")
        logger.error("error msg")

        result = output.getvalue()
        assert "debug msg" not in result
        assert "info msg" not in result
        assert "warning msg" not in result
        assert "[ERROR] error msg" in result


class TestGenerateGreetings:
    """Tests for generate_greetings function."""

    def test_single_greeting(self) -> None:
        """Test generating a single greeting."""
        output = io.StringIO()
        config = AppConfig(log_level=LogLevel.ERROR)  # Suppress logs in test
        logger = Logger(config, output)
        greeting = Greeting(name="World")

        result = generate_greetings(greeting, logger)

        assert result == ["Hello, World!"]

    def test_multiple_greetings(self) -> None:
        """Test generating multiple greetings."""
        output = io.StringIO()
        config = AppConfig(log_level=LogLevel.ERROR)
        logger = Logger(config, output)
        greeting = Greeting(name="Alice", message="Hi", times=3)

        result = generate_greetings(greeting, logger)

        assert result == ["Hi, Alice!", "Hi, Alice!", "Hi, Alice!"]
        assert len(result) == 3


class TestWriteOutput:
    """Tests for write_output function."""

    def test_write_to_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test writing to stdout."""
        output = io.StringIO()
        config = AppConfig(log_level=LogLevel.ERROR)
        logger = Logger(config, output)
        greetings = ["Hello, World!"]

        write_output(greetings, config, logger)

        captured = capsys.readouterr()
        assert "Hello, World!" in captured.out

    def test_write_to_file(self, tmp_path: Path) -> None:
        """Test writing to file."""
        output_file = tmp_path / "test_output.txt"
        output = io.StringIO()
        config = AppConfig(log_level=LogLevel.ERROR, output_file=str(output_file))
        logger = Logger(config, output)
        greetings = ["Hello, World!", "Hello, Again!"]

        write_output(greetings, config, logger)

        content = output_file.read_text()
        assert "Hello, World!" in content
        assert "Hello, Again!" in content


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
