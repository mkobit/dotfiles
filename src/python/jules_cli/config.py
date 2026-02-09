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
            except Exception as e:
                print(
                    f"Warning: Failed to read api_key from {secret_path}: {e}",
                    file=sys.stderr,
                )
        return None


def load_config(config_path: str | None = None, debug: bool = False) -> JulesConfig:
    candidates: list[Path] = []

    if config_path:
        p = Path(config_path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        candidates.append(p)
    else:
        candidates.append(Path("jules.toml"))

        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            candidates.append(Path(xdg_config_home) / "jules" / "config.toml")
        else:
            candidates.append(Path.home() / ".config" / "jules" / "config.toml")

    selected_path = next((p for p in candidates if p.exists()), None)

    if debug:
        for p in candidates:
            status = "FOUND" if p.exists() else "MISSING"
            print(f"[DEBUG] Config candidate: {p} ({status})", file=sys.stderr)
        print(f"[DEBUG] Selected config: {selected_path}", file=sys.stderr)

    if not selected_path:
        return JulesConfig()

    try:
        with open(selected_path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse config file {selected_path}: {e}") from e

    return JulesConfig(**data)
