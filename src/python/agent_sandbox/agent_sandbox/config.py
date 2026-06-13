"""Sandbox profile resolution for agent-run.

The config is rendered by chezmoi from .chezmoidata/ai/sandbox.toml. Schema
deliberately small: profiles are just bind-table decisions. No bash rules,
no per-repo overrides — a malicious repo must not be able to upgrade its
own capabilities, so profile resolution never reads from the project tree.
"""

import json
from dataclasses import dataclass
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "ai-policy" / "sandbox.json"


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Profile:
    name: str
    backend: str
    project_write: bool
    network: str


@dataclass(frozen=True)
class SandboxConfig:
    default_profile: str
    profiles: dict[str, Profile]


def load_config(path: Path | None = None) -> SandboxConfig:
    config_path = path if path is not None else CONFIG_PATH
    try:
        raw = json.loads(config_path.read_text())
    except FileNotFoundError as exc:
        raise ConfigError(f"sandbox config not found: {config_path} (run `chezmoi apply` to deploy it)") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"unreadable sandbox config {config_path}: {exc}") from exc
    profiles = {
        name: Profile(
            name=name,
            backend=data.get("backend", "auto"),
            project_write=bool(data.get("project_write", False)),
            network=data.get("network", "shared"),
        )
        for name, data in raw.get("profiles", {}).items()
        if data.get("enabled") is not False
    }
    if not profiles:
        raise ConfigError(f"no enabled profiles in {config_path}")
    return SandboxConfig(
        default_profile=raw.get("default_profile", "autonomous"),
        profiles=profiles,
    )


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
