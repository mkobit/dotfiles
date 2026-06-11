import logging
import os
import sys
import tomllib
from functools import cached_property
from pathlib import Path
from typing import Self

import typer
from pydantic import BaseModel, model_validator

logger = logging.getLogger(__name__)


class JulesConfig(BaseModel):
    """Configuration for Jules CLI."""

    api_key_path: str | None = None

    @model_validator(mode="after")
    def validate_api_key_path(self) -> Self:
        if self.api_key_path:
            secret_path = Path(self.api_key_path).expanduser()
            if not secret_path.exists():
                raise ValueError(f"api_key_path does not exist: {secret_path}")
        return self

    @cached_property
    def api_key(self) -> str | None:
        if self.api_key_path:
            secret_path = Path(self.api_key_path).expanduser()
            try:
                if secret_path.exists():
                    return secret_path.read_text().strip()
            except Exception:
                return None
        return None


def load_config(config_path: str | None = None) -> JulesConfig:
    if config_path:
        p = Path(config_path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        candidates = [p]
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        candidates = [
            Path("jules.toml"),
        ]
        if xdg_config:
            candidates.append(Path(xdg_config) / "jules" / "config.toml")

        # Always check default XDG location (fallback)
        candidates.append(Path.home() / ".config" / "jules" / "config.toml")

    def try_load(path: Path) -> JulesConfig | None:
        if not path.exists():
            logger.debug("Config candidate missing: %s", path)
            return None
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            cfg = JulesConfig(**data)
            logger.debug("Loaded valid config from: %s", path)
            return cfg
        except Exception as e:
            logger.debug("Failed to load config %s: %s", path, e)
            return None

    return next((cfg for cfg in map(try_load, candidates) if cfg), None) or JulesConfig()


def get_api_key(api_key_override: str | None = None) -> str:
    """Retrieves the Jules API key.

    Checks override first, then config, then legacy XDG config location
    (~/.config/jules/api_key).
    """
    if api_key_override:
        return api_key_override

    try:
        config = load_config()
        if config.api_key:
            return config.api_key
    except Exception as e:
        # If loading fails (e.g., config file malformed), log warning and proceed
        logging.warning("Failed to load config: %s", e)

    # Legacy check XDG config
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    legacy_file = Path(xdg_config_home) / "jules" / "api_key"

    if legacy_file.exists():
        return legacy_file.read_text().strip()

    typer.echo(f"Error: API key not found in config or {legacy_file}.", err=True)
    sys.exit(1)
