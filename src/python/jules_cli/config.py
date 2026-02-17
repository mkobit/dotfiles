import logging
import os
import tomllib
from pathlib import Path
from typing import Self

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

    @property
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
            (Path(xdg_config) / "jules" / "config.toml")
            if xdg_config
            else (Path.home() / ".config" / "jules" / "config.toml"),
        ]

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

    return (
        next((cfg for cfg in map(try_load, candidates) if cfg), None) or JulesConfig()
    )
