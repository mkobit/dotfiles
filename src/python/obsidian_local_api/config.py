import logging
import os
import tomllib
from pathlib import Path
from typing import Self

from pydantic import BaseModel, model_validator

logger = logging.getLogger(__name__)


class ObsidianConfig(BaseModel):
    """Configuration for Obsidian Local API."""

    token_path: str | None = None
    port: int = 27124
    host: str = "127.0.0.1"

    @model_validator(mode="after")
    def validate_token_path(self) -> Self:
        if self.token_path:
            secret_path = Path(self.token_path).expanduser()
            if not secret_path.exists():
                raise ValueError(f"token_path does not exist: {secret_path}")
        return self

    @property
    def token(self) -> str | None:
        if self.token_path:
            secret_path = Path(self.token_path).expanduser()
            try:
                if secret_path.exists():
                    return secret_path.read_text().strip()
            except Exception:
                return None
        return None


def load_config(config_path: str | None = None) -> ObsidianConfig:
    if config_path:
        p = Path(config_path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        candidates = [p]
    else:
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        candidates = [
            Path("obsidian-local-api.toml"),
            Path(".obsidian-local-api.toml"),
            Path(".config") / "obsidian-local-api.toml",
            (Path(xdg_config) / "obsidian-local-api" / "config.toml")
            if xdg_config
            else (Path.home() / ".config" / "obsidian-local-api" / "config.toml"),
        ]

    def try_load(path: Path) -> ObsidianConfig | None:
        if not path.exists():
            logger.debug("Config candidate missing: %s", path)
            return None
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            cfg = ObsidianConfig(**data)
            logger.debug("Loaded valid config from: %s", path)
            return cfg
        except Exception as e:
            logger.debug("Failed to load config %s: %s", path, e)
            return None

    return (
        next((cfg for cfg in map(try_load, candidates) if cfg), None)
        or ObsidianConfig()
    )
