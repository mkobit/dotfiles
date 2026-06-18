"""Sandbox profile resolution for agent-run.

The config is rendered by chezmoi from .chezmoidata/ai/sandbox.toml to
~/.config/ai-policy/sandbox.toml. Schema deliberately small: profiles are
just bind-table decisions. No bash rules, no per-repo overrides — a
malicious repo must not be able to upgrade its own capabilities, so
profile resolution never reads from the project tree.
"""

import tomllib
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

CONFIG_PATH = Path.home() / ".config" / "ai-policy" / "sandbox.toml"

Backend = Literal["auto", "bwrap", "seatbelt"]
Network = Literal["shared", "none"]


class ConfigError(Exception):
    pass


class Profile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    backend: Backend = "auto"
    project_write: bool = False
    network: Network = "shared"
    # Paths under $HOME to re-expose rw after the tmpfs default-deny.
    # Empty for most profiles; broad for the `chezmoi` profile that needs
    # to test deploying templates by running `chezmoi apply`.
    home_rw: tuple[str, ...] = ()
    # Paths to tmpfs-mask after home_rw, for credential dirs nested inside
    # an otherwise rw-exposed parent (e.g., ~/.config/gh when ~/.config is
    # bound rw). Paths not under any home_rw entry are already masked by
    # the home tmpfs and don't need to be listed here.
    home_mask: tuple[str, ...] = ()


class SandboxConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    default_profile: str = "autonomous"
    profiles: dict[str, Profile] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _project_profile_names_and_filter_disabled(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        raw_profiles = data.get("profiles") or {}
        if not isinstance(raw_profiles, dict):
            return data
        projected = {
            name: {k: v for k, v in (entry or {}).items() if k != "enabled"} | {"name": name}
            for name, entry in raw_profiles.items()
            if not isinstance(entry, dict) or entry.get("enabled") is not False
        }
        return {**data, "profiles": projected}


def load_config(path: Path | None = None) -> SandboxConfig:
    config_path = path if path is not None else CONFIG_PATH
    try:
        raw = tomllib.loads(config_path.read_text())
    except FileNotFoundError as exc:
        raise ConfigError(f"sandbox config not found: {config_path} (run `chezmoi apply` to deploy it)") from exc
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"unreadable sandbox config {config_path}: {exc}") from exc
    try:
        config = SandboxConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"invalid sandbox config {config_path}: {exc}") from exc
    if not config.profiles:
        raise ConfigError(f"no enabled profiles in {config_path}")
    return config


def resolve_profile(
    config: SandboxConfig,
    cli_profile: str | None,
    env_profile: str | None,
) -> Profile:
    """Resolve active profile: CLI flag > $AGENT_RUN_PROFILE > config default."""
    for source, candidate in (("--profile", cli_profile), ("AGENT_RUN_PROFILE", env_profile)):
        if candidate:
            profile = config.profiles.get(candidate)
            if profile is None:
                raise ConfigError(f"unknown profile {candidate!r} from {source}; available: {sorted(config.profiles)}")
            return profile
    profile = config.profiles.get(config.default_profile)
    if profile is None:
        raise ConfigError(f"default_profile {config.default_profile!r} is not an enabled profile")
    return profile
