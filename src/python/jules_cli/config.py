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


def load_config(config_path: str | None = None, debug: bool = False) -> JulesConfig:
    candidates: list[Path] = []

    if config_path:
        # If explicit path provided, check ONLY that path
        p = Path(config_path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        candidates.append(p)
    else:
        # CWD first
        candidates.append(Path("jules.toml"))

        # XDG Standard
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            candidates.append(Path(xdg_config_home) / "jules" / "config.toml")
        else:
            candidates.append(Path.home() / ".config" / "jules" / "config.toml")

    def try_load(path: Path) -> JulesConfig | None:
        if not path.exists():
            if debug:
                print(f"[DEBUG] Config candidate missing: {path}", file=sys.stderr)
            return None
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            cfg = JulesConfig(**data)
            if debug:
                print(f"[DEBUG] Loaded valid config from: {path}", file=sys.stderr)
            return cfg
        except Exception as e:
            if debug:
                print(f"[DEBUG] Failed to load config {path}: {e}", file=sys.stderr)
            return None

    # Functional first-match pattern
    config = next((cfg for cfg in map(try_load, candidates) if cfg), None)

    if config:
        return config

    return JulesConfig()
