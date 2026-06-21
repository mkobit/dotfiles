import tomllib
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from agent_sandbox.profile.schema import ConfigError, Profile, SandboxConfig

CONFIG_PATH = Path.home() / ".config" / "ai-policy" / "sandbox.toml"


def load_config(path: Path | None = None) -> SandboxConfig:
    config_path = path if path is not None else CONFIG_PATH
    try:
        raw = tomllib.loads(config_path.read_text())
    except FileNotFoundError as exc:
        raise ConfigError(
            f"sandbox config not found: {config_path} (run `chezmoi apply` to deploy it)"
        ) from exc
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
                raise ConfigError(
                    f"unknown profile {candidate!r} from {source}; "
                    f"available: {sorted(config.profiles)}"
                )
            return profile
    profile = config.profiles.get(config.default_profile)
    if profile is None:
        raise ConfigError(f"default_profile {config.default_profile!r} is not an enabled profile")
    return profile


def merge_cli_overrides(
    profile: Profile,
    *,
    project_write: bool | None = None,
    network: str | None = None,
    ssh_agent: bool | None = None,
    gpg_agent: bool | None = None,
    extra_ro: Sequence[str] = (),
    extra_rw: Sequence[str] = (),
) -> Profile:
    """Return a new Profile with CLI flag values applied on top of the base profile.

    None values are ignored (not overridden). extra_ro/extra_rw are appended
    to any paths already declared in the profile.
    """
    overrides: dict[str, object] = {
        k: v
        for k, v in {
            "project_write": project_write,
            "network": network,
            "ssh_agent": ssh_agent,
            "gpg_agent": gpg_agent,
        }.items()
        if v is not None
    }
    if extra_ro:
        overrides["extra_ro"] = (*profile.extra_ro, *extra_ro)
    if extra_rw:
        overrides["extra_rw"] = (*profile.extra_rw, *extra_rw)
    return profile.model_copy(update=overrides) if overrides else profile
