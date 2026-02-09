import os
import sys
import tomllib
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel, model_validator


class ObsidianConfig(BaseModel):
    """Configuration for Obsidian Local API."""

    token: str | None = None
    token_path: str | None = None
    port: int = 27124
    host: str = "127.0.0.1"

    @model_validator(mode="after")
    def resolve_token(self) -> Self:
        """Resolve token from token_path if not provided."""
        if not self.token and self.token_path:
            secret_path = Path(self.token_path).expanduser()
            if secret_path.exists():
                try:
                    self.token = secret_path.read_text().strip()
                except Exception as e:
                    raise ValueError(
                        f"Failed to read token from {secret_path}: {e}"
                    ) from e
        return self


def load_config(config_path: str | None = None) -> ObsidianConfig:
    """Load configuration from file.

    Search order:
    1. Provided config_path
    2. ./obsidian-local-api.toml
    3. ./.obsidian-local-api.toml
    4. $XDG_CONFIG_HOME/obsidian-local-api/config.toml (defaults to ~/.config/obsidian-local-api/config.toml)
    """
    candidates: list[Path] = []

    # 1. Explicit path
    if config_path:
        p = Path(config_path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        candidates.append(p)
    else:
        # 2. CWD
        candidates.append(Path("obsidian-local-api.toml"))
        candidates.append(Path(".obsidian-local-api.toml"))
        # Also check .config/obsidian-local-api.toml (legacy local check mentioned in docs/cli?)
        # The previous impl checked .config/obsidian-local-api.toml in CWD too.
        candidates.append(Path(".config") / "obsidian-local-api.toml")

        # 3. XDG Config
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            candidates.append(
                Path(xdg_config_home) / "obsidian-local-api" / "config.toml"
            )
        else:
            # Default fallback
            candidates.append(
                Path.home() / ".config" / "obsidian-local-api" / "config.toml"
            )

    # Debug logging
    debug = os.environ.get("OBSIDIAN_DEBUG", "").lower() in ("1", "true", "yes", "on")

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

    return ObsidianConfig(**data)
