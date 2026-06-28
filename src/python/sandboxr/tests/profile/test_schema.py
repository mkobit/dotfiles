import tomllib

import pytest
from pydantic import ValidationError

from sandboxr.profile.loader import load_config, resolve_profile
from sandboxr.profile.schema import ConfigError, Profile, SandboxConfig

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


def write_config(tmp_path, text):
    path = tmp_path / "sandbox.toml"
    path.write_text(text)
    return path


def test_load_excludes_disabled_profiles(tmp_path):
    config = load_config(write_config(tmp_path, BASE_TOML))
    assert set(config.profiles) == {"autonomous", "readonly"}
    assert config.profiles["readonly"].project_write is False
    assert config.profiles["autonomous"].backend == "auto"


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.toml")


def test_load_invalid_toml_raises(tmp_path):
    path = write_config(tmp_path, "this = is not [ valid toml")
    with pytest.raises(ConfigError, match="unreadable"):
        load_config(path)


def test_load_unknown_backend_raises(tmp_path):
    path = write_config(
        tmp_path,
        (
            'default_profile = "x"\n'
            "[profiles.x]\n"
            "enabled = true\n"
            'backend = "docker"\n'
            "project_write = true\n"
        ),
    )
    with pytest.raises(ConfigError, match="invalid sandbox config"):
        load_config(path)


def test_load_unknown_profile_key_raises(tmp_path):
    path = write_config(
        tmp_path,
        (
            'default_profile = "x"\n'
            "[profiles.x]\n"
            "enabled = true\n"
            'backend = "auto"\n'
            "project_write = true\n"
            'surprise = "nope"\n'
        ),
    )
    with pytest.raises(ConfigError, match="invalid sandbox config"):
        load_config(path)


def test_load_no_profiles_raises(tmp_path):
    with pytest.raises(ConfigError, match="no enabled profiles"):
        load_config(write_config(tmp_path, 'default_profile = "x"\n'))


def test_profile_is_frozen():
    p = Profile(name="autonomous", backend="auto", project_write=True, network="shared")
    with pytest.raises(ValidationError):
        p.project_write = False  # type: ignore[misc]


def test_profile_ssh_agent_defaults_false():
    p = Profile(name="test", backend="auto", project_write=True, network="shared")
    assert p.ssh_agent is False
    assert p.gpg_agent is False


def test_profile_extra_ro_rw_default_empty():
    p = Profile(name="test", backend="auto", project_write=True, network="shared")
    assert p.extra_ro == ()
    assert p.extra_rw == ()


@pytest.fixture
def config(tmp_path):
    return load_config(write_config(tmp_path, BASE_TOML))


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


def test_resolve_missing_default_raises(tmp_path):
    config = load_config(
        write_config(
            tmp_path,
            (
                'default_profile = "ghost"\n'
                "[profiles.readonly]\n"
                "enabled = true\n"
                'backend = "auto"\n'
                "project_write = false\n"
            ),
        ),
    )
    with pytest.raises(ConfigError, match="default_profile"):
        resolve_profile(config, None, None)


def test_round_trip_with_tomllib(tmp_path):
    rendered = tomllib.loads(BASE_TOML)
    assert rendered["profiles"]["autonomous"]["backend"] == "auto"
    config = SandboxConfig.model_validate(rendered)
    assert config.profiles["autonomous"].network == "shared"
