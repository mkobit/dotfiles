"""Pydantic models for hello_world CLI tool.

Demonstrates using pydantic for data validation and structured configuration.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Supported log levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Greeting(BaseModel):
    """A greeting message with structured data."""

    name: str = Field(..., min_length=1, description="Name to greet")
    message: str = Field(default="Hello", description="Greeting message")
    times: int = Field(default=1, ge=1, le=100, description="Number of times to greet")

    def format(self) -> str:
        """Format the greeting as a string."""
        return f"{self.message}, {self.name}!"


class AppConfig(BaseModel):
    """Application configuration with validation."""

    log_level: LogLevel = Field(default=LogLevel.INFO)
    output_file: Optional[str] = Field(default=None)
    verbose: bool = Field(default=False)

    class Config:
        """Pydantic model configuration."""

        use_enum_values = True
