import os
import sys
import tomllib
from pathlib import Path
from typing import Any, Self, Union

from pydantic import BaseModel, ValidationError, model_validator


class JulesConfig(BaseModel):
    """Configuration for Jules CLI."""

    api_key_path: str | None = None

    @classmethod
    def safe_validate(cls, **kwargs: Any) -> Union[Self, Exception]:
        """Safely validate and return an instance or the exception."""
        try:
            return cls(**kwargs)
        except (ValidationError, ValueError) as e:
            return e

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

    selected_config: JulesConfig | None = None

    for path in candidates:
        if not path.exists():
            if debug:
                print(f"[DEBUG] Config candidate missing: {path}", file=sys.stderr)
            continue

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            if debug:
                print(f"[DEBUG] Failed to parse config {path}: {e}", file=sys.stderr)
            continue

        result = JulesConfig.safe_validate(**data)
        if isinstance(result, Exception):
            if debug:
                print(
                    f"[DEBUG] Validation failed for {path}: {result}", file=sys.stderr
                )
            continue

        if debug:
            print(f"[DEBUG] Loaded valid config from: {path}", file=sys.stderr)

        selected_config = result
        break

    if selected_config:
        return selected_config

    return JulesConfig()
