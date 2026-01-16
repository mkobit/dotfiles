import os
import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class ObsidianConfig(BaseModel):
    """Configuration for Obsidian Local API."""

    token: str | None = None
    port: int = 27124
    host: str = "127.0.0.1"


def load_config(config_path: str | None = None) -> ObsidianConfig:
    """Load configuration from file.

    Search order:
    1. Provided config_path
    2. ./obsidian-local-api.toml
    3. ~/.config/obsidian-local-api/config.toml
    """
    file_path: Path | None = None

    if config_path:
        file_path = Path(config_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
    else:
        # Check current directory
        local_path = Path("obsidian-local-api.toml")
        if local_path.exists():
            file_path = local_path
        else:
            # Check XDG config
            xdg_config = os.environ.get(
                "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
            )
            default_path = Path(xdg_config) / "obsidian-local-api" / "config.toml"
            if default_path.exists():
                file_path = default_path

    data: dict[str, Any] = {}
    if file_path:
        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse config file {file_path}: {e}") from e

    return ObsidianConfig(**data)
