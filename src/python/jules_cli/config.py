import os
import sys
import tomllib
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, model_validator


class JulesConfig(BaseModel):
    """Configuration for Jules CLI."""

    api_key_path: str | None = None

    @model_validator(mode="after")
    def validate_api_key_path(self) -> Self:
        """Validate that api_key_path exists if provided."""
        if self.api_key_path:
            secret_path = Path(self.api_key_path).expanduser()
            if not secret_path.exists():
                raise ValueError(f"api_key_path does not exist: {secret_path}")
        return self

    @property
    def api_key(self) -> str | None:
        """Retrieve the API key from the configured path."""
        if self.api_key_path:
            secret_path = Path(self.api_key_path).expanduser()
            try:
                if secret_path.exists():
                    return secret_path.read_text().strip()
            except Exception as e:
                # Log or re-raise? Accessing a property shouldn't typically crash unpredictably,
                # but if the config is invalid, we want to know.
                print(
                    f"Warning: Failed to read api_key from {secret_path}: {e}",
                    file=sys.stderr,
                )
                return None
        return None


def load_config(config_path: str | None = None) -> JulesConfig:
    """Load configuration from file.

    Search order:
    1. Provided config_path
    2. ./jules.toml
    3. $XDG_CONFIG_HOME/jules/config.toml (defaults to ~/.config/jules/config.toml)
    """
    candidates: list[Path] = []

    # 1. Explicit path
    if config_path:
        # If explicit path provided, check ONLY that path
        p = Path(config_path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        candidates.append(p)
    else:
        # 2. CWD
        candidates.append(Path("jules.toml"))

        # 3. XDG Config
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            candidates.append(Path(xdg_config_home) / "jules" / "config.toml")
        else:
            # Default fallback
            candidates.append(Path.home() / ".config" / "jules" / "config.toml")

    # Debug logging
    debug = os.environ.get("JULES_DEBUG", "").lower() in ("1", "true", "yes", "on")

    selected_path: Path | None = None
    data: dict[str, Any] = {}

    for path in candidates:
        if debug:
            print(f"[DEBUG] Checking config path: {path}", file=sys.stderr)

        if path.exists():
            selected_path = path
            if debug:
                print(f"[DEBUG] Found config at: {path}", file=sys.stderr)
            break

    if selected_path:
        try:
            with open(selected_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            if debug:
                print(
                    f"[DEBUG] Failed to parse config {selected_path}: {e}",
                    file=sys.stderr,
                )
            raise ValueError(f"Failed to parse config file {selected_path}: {e}") from e

    return JulesConfig(**data)
