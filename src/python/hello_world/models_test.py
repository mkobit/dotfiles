"""Tests for hello_world models."""

import pytest
from pydantic import ValidationError

from src.python.hello_world.models import AppConfig, Greeting, LogLevel


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_log_level_values(self) -> None:
        """Test that all expected log levels exist."""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.ERROR.value == "error"


class TestGreeting:
    """Tests for Greeting model."""

    def test_greeting_with_defaults(self) -> None:
        """Test greeting creation with default values."""
        greeting = Greeting(name="World")
        assert greeting.name == "World"
        assert greeting.message == "Hello"
        assert greeting.times == 1

    def test_greeting_format(self) -> None:
        """Test greeting format method."""
        greeting = Greeting(name="Alice", message="Hi")
        assert greeting.format() == "Hi, Alice!"

    def test_greeting_custom_values(self) -> None:
        """Test greeting with all custom values."""
        greeting = Greeting(name="Bob", message="Greetings", times=5)
        assert greeting.name == "Bob"
        assert greeting.message == "Greetings"
        assert greeting.times == 5

    def test_greeting_empty_name_fails(self) -> None:
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError):
            Greeting(name="")

    def test_greeting_times_too_low_fails(self) -> None:
        """Test that times < 1 raises validation error."""
        with pytest.raises(ValidationError):
            Greeting(name="Test", times=0)

    def test_greeting_times_too_high_fails(self) -> None:
        """Test that times > 100 raises validation error."""
        with pytest.raises(ValidationError):
            Greeting(name="Test", times=101)


class TestAppConfig:
    """Tests for AppConfig model."""

    def test_config_defaults(self) -> None:
        """Test config with default values."""
        config = AppConfig()
        assert config.log_level == LogLevel.INFO
        assert config.output_file is None
        assert config.verbose is False

    def test_config_custom_values(self) -> None:
        """Test config with custom values."""
        config = AppConfig(
            log_level=LogLevel.DEBUG,
            output_file="/tmp/test.txt",
            verbose=True,
        )
        assert config.log_level == LogLevel.DEBUG
        assert config.output_file == "/tmp/test.txt"
        assert config.verbose is True

    def test_config_log_level_from_string(self) -> None:
        """Test that string log level is coerced to enum."""
        # Pydantic handles coercion, so we cast to LogLevel to satisfy mypy
        config = AppConfig(log_level=LogLevel("warning"))
        assert config.log_level == LogLevel.WARNING
