import pytest

from sandboxr.profile.loader import load_config, merge_cli_overrides
from sandboxr.profile.schema import SandboxConfig

BASE_TOML = """
default_profile = "autonomous"

[profiles.autonomous]
enabled = true
backend = "auto"
project_write = true
network = "shared"
ssh_agent = false
gpg_agent = false

[profiles.readonly]
enabled = true
backend = "auto"
project_write = false
network = "shared"
ssh_agent = false
gpg_agent = false

[profiles.disabled]
enabled = false
backend = "auto"
project_write = true
network = "shared"
"""

BASE_TOML_WITH_EXTRA_RO = """
default_profile = "autonomous"

[profiles.autonomous]
enabled = true
backend = "auto"
project_write = true
network = "shared"
ssh_agent = false
gpg_agent = false
extra_ro = ["/base/path"]

[profiles.readonly]
enabled = true
backend = "auto"
project_write = false
network = "shared"
ssh_agent = false
gpg_agent = false
"""


def write_config(tmp_path, text):
    path = tmp_path / "sandbox.toml"
    path.write_text(text)
    return path


@pytest.fixture
def config(tmp_path):
    return load_config(write_config(tmp_path, BASE_TOML))


def test_merge_no_overrides_returns_same_profile(config: SandboxConfig) -> None:
    profile = config.profiles["autonomous"]
    result = merge_cli_overrides(profile)
    assert result == profile


def test_merge_project_write_override(config: SandboxConfig) -> None:
    profile = config.profiles["autonomous"]
    result = merge_cli_overrides(profile, project_write=False)
    assert result.project_write is False
    assert result.name == profile.name


def test_merge_network_override(config: SandboxConfig) -> None:
    profile = config.profiles["autonomous"]
    result = merge_cli_overrides(profile, network="none")
    assert result.network == "none"


def test_merge_ssh_agent_override(config: SandboxConfig) -> None:
    profile = config.profiles["autonomous"]
    result = merge_cli_overrides(profile, ssh_agent=True)
    assert result.ssh_agent is True


def test_merge_gpg_agent_override(config: SandboxConfig) -> None:
    profile = config.profiles["autonomous"]
    result = merge_cli_overrides(profile, gpg_agent=True)
    assert result.gpg_agent is True


def test_merge_extra_ro_appends_to_profile(tmp_path) -> None:
    cfg = load_config(write_config(tmp_path, BASE_TOML_WITH_EXTRA_RO))
    profile = cfg.profiles["autonomous"]
    result = merge_cli_overrides(profile, extra_ro=["/cli/path"])
    assert "/base/path" in result.extra_ro
    assert "/cli/path" in result.extra_ro


def test_merge_extra_rw_appends_to_profile(config: SandboxConfig) -> None:
    profile = config.profiles["autonomous"]
    result = merge_cli_overrides(profile, extra_rw=["/tmp/state"])
    assert "/tmp/state" in result.extra_rw


def test_merge_allowed_domains_appends_to_profile(tmp_path) -> None:
    toml = """
default_profile = "allowlisted"

[profiles.allowlisted]
enabled = true
backend = "srt"
project_write = true
network = "allowlist"
allowed_domains = ["base.example.com"]
"""
    cfg = load_config(write_config(tmp_path, toml))
    profile = cfg.profiles["allowlisted"]
    result = merge_cli_overrides(profile, allowed_domains=["cli.example.com"])
    assert "base.example.com" in result.allowed_domains
    assert "cli.example.com" in result.allowed_domains


def test_merge_none_values_not_applied(config: SandboxConfig) -> None:
    profile = config.profiles["autonomous"]
    result = merge_cli_overrides(profile, project_write=None, network=None)
    assert result.project_write == profile.project_write
    assert result.network == profile.network


def test_merge_timeout_seconds_override(config: SandboxConfig) -> None:
    profile = config.profiles["autonomous"]
    result = merge_cli_overrides(profile, timeout_seconds=300)
    assert result.timeout_seconds == 300


def test_merge_timeout_seconds_none_not_applied(config: SandboxConfig) -> None:
    profile = config.profiles["autonomous"]
    result = merge_cli_overrides(profile, timeout_seconds=None)
    assert result.timeout_seconds == profile.timeout_seconds
