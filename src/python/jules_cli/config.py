import os
import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class JulesConfig(BaseModel):
    """Configuration for Jules CLI."""

    api_key: str | None = None
    api_key_path: str | None = None


def load_config(config_path: str | None = None) -> JulesConfig:
    """Load configuration from file.

    Search order:
    1. Provided config_path
    2. ./jules.toml
    3. ~/.config/jules/config.toml (or XDG_CONFIG_HOME)
    """
    file_path: Path | None = None

    if config_path:
        file_path = Path(config_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
    else:
        # Check current directory
        cwd_config = Path("jules.toml")
        if cwd_config.exists():
            file_path = cwd_config
        else:
            # Check XDG config
            xdg_config = os.environ.get(
                "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
            )
            default_path = Path(xdg_config) / "jules" / "config.toml"
            if default_path.exists():
                file_path = default_path

    data: dict[str, Any] = {}
    if file_path:
        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse config file {file_path}: {e}") from e

    config = JulesConfig(**data)

    # Resolve api_key from path if needed
    if config.api_key_path:
        secret_path = Path(config.api_key_path).expanduser()
        if secret_path.exists():
            config.api_key = secret_path.read_text().strip()

    return config
