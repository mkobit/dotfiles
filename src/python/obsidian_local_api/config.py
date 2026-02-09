import os
import sys
import tomllib
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, model_validator


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
            except Exception as e:
                print(
                    f"Warning: Failed to read token from {secret_path}: {e}",
                    file=sys.stderr,
                )
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
            candidates.append(
                Path(xdg_config_home) / "obsidian-local-api" / "config.toml"
            )
        else:
            candidates.append(
                Path.home() / ".config" / "obsidian-local-api" / "config.toml"
            )

    selected_path = next((p for p in candidates if p.exists()), None)

    if debug:
        for p in candidates:
            status = "FOUND" if p.exists() else "MISSING"
            print(f"[DEBUG] Config candidate: {p} ({status})", file=sys.stderr)
        print(f"[DEBUG] Selected config: {selected_path}", file=sys.stderr)

    if not selected_path:
        return ObsidianConfig()

    try:
        with open(selected_path, "rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse config file {selected_path}: {e}") from e

    return ObsidianConfig(**data)
