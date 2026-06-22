from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    ssh_agent: bool = False
    gpg_agent: bool = False
    extra_ro: tuple[str, ...] = Field(default=())
    extra_rw: tuple[str, ...] = Field(default=())
    # Paths under $HOME to re-expose rw after the tmpfs default-deny.
    # Empty for most profiles; broad for the `chezmoi` profile that needs
    # to test deploying templates by running `chezmoi apply`.
    home_rw: tuple[str, ...] = Field(default=())
    # Paths to tmpfs-mask after home_rw, for credential dirs nested inside
    # an otherwise rw-exposed parent (e.g., ~/.config/gh when ~/.config is
    # bound rw). Paths not under any home_rw entry are already masked by
    # the home tmpfs and don't need to be listed here.
    home_mask: tuple[str, ...] = Field(default=())


class SandboxConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    default_profile: str = "autonomous"
    profiles: dict[str, Profile] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _inject_names_and_drop_disabled(cls, data: Any) -> Any:
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
