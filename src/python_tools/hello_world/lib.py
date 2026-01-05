"""Library functions for hello_world CLI tool.

Contains the core business logic separated from the CLI interface.
"""

import sys
from typing import TextIO

from src.python_tools.hello_world.models import AppConfig, Greeting, LogLevel


class Logger:
    """Simple logger demonstrating structured logging."""

    LEVEL_PRIORITY = {
        LogLevel.DEBUG: 0,
        LogLevel.INFO: 1,
        LogLevel.WARNING: 2,
        LogLevel.ERROR: 3,
    }

    def __init__(self, config: AppConfig, output: TextIO = sys.stderr) -> None:
        """Initialize logger with configuration."""
        self.config = config
        self.output = output

    def _should_log(self, level: LogLevel) -> bool:
        """Check if message at level should be logged."""
        return self.LEVEL_PRIORITY[level] >= self.LEVEL_PRIORITY[self.config.log_level]

    def _log(self, level: LogLevel, message: str) -> None:
        """Log a message at the specified level."""
        if self._should_log(level):
            prefix = f"[{level.value.upper()}]"
            self.output.write(f"{prefix} {message}\n")

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self._log(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        """Log an info message."""
        self._log(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self._log(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        """Log an error message."""
        self._log(LogLevel.ERROR, message)


def generate_greetings(greeting: Greeting, logger: Logger) -> list[str]:
    """Generate a list of greeting strings.

    Args:
        greeting: The greeting configuration
        logger: Logger for output

    Returns:
        List of formatted greeting strings
    """
    logger.debug(f"Generating {greeting.times} greeting(s) for {greeting.name}")

    greetings = []
    for i in range(greeting.times):
        formatted = greeting.format()
        greetings.append(formatted)
        logger.debug(f"Generated greeting {i + 1}: {formatted}")

    logger.info(f"Generated {len(greetings)} greeting(s)")
    return greetings


def write_output(greetings: list[str], config: AppConfig, logger: Logger) -> None:
    """Write greetings to output destination.

    Args:
        greetings: List of greeting strings to write
        config: Application configuration
        logger: Logger for output
    """
    if config.output_file:
        logger.info(f"Writing to file: {config.output_file}")
        with open(config.output_file, "w") as f:
            for greeting in greetings:
                f.write(greeting + "\n")
        logger.info(f"Wrote {len(greetings)} greeting(s) to {config.output_file}")
    else:
        logger.debug("Writing to stdout")
        for greeting in greetings:
            print(greeting)
