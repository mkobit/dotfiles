import tomllib

import pytest
from pydantic import ValidationError

from sandboxr.profile.loader import load_config, resolve_profile
from sandboxr.profile.schema import ConfigError, Profile, SandboxConfig


def test_load_excludes_disabled_profiles(config: SandboxConfig):
    assert set(config.profiles) == {"autonomous", "readonly"}
    assert config.profiles["readonly"].project_write is False
    assert config.profiles["autonomous"].backend == "auto"


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.toml")


def test_load_invalid_toml_raises(write_config):
    path = write_config("this = is not [ valid toml")
    with pytest.raises(ConfigError, match="unreadable"):
        load_config(path)


def test_load_unknown_backend_raises(write_config):
    path = write_config(
        'default_profile = "x"\n'
        "[profiles.x]\n"
        "enabled = true\n"
        'backend = "docker"\n'
        "project_write = true\n"
    )
    with pytest.raises(ConfigError, match="invalid sandbox config"):
        load_config(path)


def test_load_unknown_profile_key_raises(write_config):
    path = write_config(
        'default_profile = "x"\n'
        "[profiles.x]\n"
        "enabled = true\n"
        'backend = "auto"\n'
        "project_write = true\n"
        'surprise = "nope"\n'
    )
    with pytest.raises(ConfigError, match="invalid sandbox config"):
        load_config(path)


def test_load_no_profiles_raises(write_config):
    with pytest.raises(ConfigError, match="no enabled profiles"):
        load_config(write_config('default_profile = "x"\n'))


def test_profile_is_frozen():
    p = Profile(name="autonomous", backend="auto", project_write=True, network="shared")
    with pytest.raises(ValidationError):
        p.project_write = False  # type: ignore[misc]  # ty: ignore[invalid-assignment]


def test_profile_ssh_agent_defaults_false():
    p = Profile(name="test", backend="auto", project_write=True, network="shared")
    assert p.ssh_agent is False
    assert p.gpg_agent is False


def test_profile_extra_ro_rw_default_empty():
    p = Profile(name="test", backend="auto", project_write=True, network="shared")
    assert p.extra_ro == ()
    assert p.extra_rw == ()


def test_profile_allowlist_requires_domains():
    with pytest.raises(ValidationError, match="allowed_domains"):
        Profile(name="test", backend="srt", project_write=True, network="allowlist")


def test_profile_non_allowlist_rejects_domains():
    with pytest.raises(ValidationError, match="allowed_domains"):
        Profile(
            name="test",
            backend="auto",
            project_write=True,
            network="shared",
            allowed_domains=("api.example.com",),
        )


def test_profile_allowlist_with_domains_is_valid():
    p = Profile(
        name="test",
        backend="srt",
        project_write=True,
        network="allowlist",
        allowed_domains=("api.example.com",),
    )
    assert p.allowed_domains == ("api.example.com",)


def test_profile_timeout_seconds_defaults_none():
    p = Profile(name="test", backend="auto", project_write=True, network="shared")
    assert p.timeout_seconds is None


def test_profile_timeout_seconds_rejects_non_positive():
    with pytest.raises(ValidationError, match="timeout_seconds"):
        Profile(
            name="test",
            backend="auto",
            project_write=True,
            network="shared",
            timeout_seconds=0,
        )


def test_resolve_cli_flag_wins(config: SandboxConfig):
    assert resolve_profile(config, "readonly", "autonomous").name == "readonly"


def test_resolve_env_used_when_no_flag(config: SandboxConfig):
    assert resolve_profile(config, None, "readonly").name == "readonly"


def test_resolve_falls_back_to_default(config: SandboxConfig):
    assert resolve_profile(config, None, None).name == "autonomous"


def test_resolve_unknown_cli_profile_raises(config: SandboxConfig):
    with pytest.raises(ConfigError, match="unknown profile"):
        resolve_profile(config, "yolo", None)


def test_resolve_unknown_env_profile_raises(config: SandboxConfig):
    with pytest.raises(ConfigError, match="unknown profile"):
        resolve_profile(config, None, "yolo")


def test_resolve_missing_default_raises(write_config):
    config = load_config(
        write_config(
            'default_profile = "ghost"\n'
            "[profiles.readonly]\n"
            "enabled = true\n"
            'backend = "auto"\n'
            "project_write = false\n"
        ),
    )
    with pytest.raises(ConfigError, match="default_profile"):
        resolve_profile(config, None, None)


def test_round_trip_with_tomllib(base_toml):
    rendered = tomllib.loads(base_toml)
    assert rendered["profiles"]["autonomous"]["backend"] == "auto"
    config = SandboxConfig.model_validate(rendered)
    assert config.profiles["autonomous"].network == "shared"
