from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Backend = Literal["auto", "bwrap", "srt"]
Network = Literal["shared", "none", "allowlist"]


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
    # Domain allowlist for network="allowlist" (srt backend only). Required
    # non-empty when network="allowlist"; must be empty otherwise.
    allowed_domains: tuple[str, ...] = Field(default=())
    # Wall-clock bound on the whole sandboxed invocation (outer bwrap/srt
    # process included). None = unbounded. Turns a silent hang into a fast,
    # visible exit-124 instead of leaving it to the caller to notice.
    timeout_seconds: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _check_allowed_domains(self) -> Profile:
        if self.network == "allowlist" and not self.allowed_domains:
            msg = "allowed_domains must be non-empty when network='allowlist'"
            raise ValueError(msg)
        if self.network != "allowlist" and self.allowed_domains:
            msg = "allowed_domains is only valid when network='allowlist'"
            raise ValueError(msg)
        return self


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
