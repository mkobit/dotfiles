import os
import sys
import tomllib
from pathlib import Path
from typing import Any, Self, Union

from pydantic import BaseModel, ValidationError, model_validator


class ObsidianConfig(BaseModel):
    """Configuration for Obsidian Local API."""

    token_path: str | None = None
    port: int = 27124
    host: str = "127.0.0.1"

    @classmethod
    def safe_validate(
        cls, *, token_path: str | None = None, port: int = 27124, host: str = "127.0.0.1"
    ) -> Union[Self, Exception]:
        """Safely validate and return an instance or the exception."""
        try:
            return cls(token_path=token_path, port=port, host=host)
        except (ValidationError, ValueError) as e:
            return e

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


def load_config(config_path: str | None = None, debug: bool = False) -> ObsidianConfig:
    candidates: list[Path] = []

    if config_path:
        p = Path(config_path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        candidates.append(p)
    else:
        candidates.append(Path("obsidian-local-api.toml"))
        candidates.append(Path(".obsidian-local-api.toml"))
        candidates.append(Path(".config") / "obsidian-local-api.toml")

        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            candidates.append(Path(xdg_config_home) / "obsidian-local-api" / "config.toml")
        else:
            candidates.append(Path.home() / ".config" / "obsidian-local-api" / "config.toml")

    selected_config: ObsidianConfig | None = None

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

        result = ObsidianConfig.safe_validate(**data)
        if isinstance(result, Exception):
            if debug:
                print(f"[DEBUG] Validation failed for {path}: {result}", file=sys.stderr)
            continue

        if debug:
            print(f"[DEBUG] Loaded valid config from: {path}", file=sys.stderr)

        selected_config = result
        break

    if selected_config:
        return selected_config

    return ObsidianConfig()
