import json

import pytest

from agent_sandbox.config import ConfigError, load_config, resolve_profile

BASE = {
    "default_profile": "autonomous",
    "profiles": {
        "autonomous": {"enabled": True, "backend": "auto", "project_write": True, "network": "shared"},
        "readonly": {"enabled": True, "backend": "auto", "project_write": False, "network": "shared"},
        "disabled": {"enabled": False, "backend": "auto", "project_write": True, "network": "shared"},
    },
}


def write_config(tmp_path, data):
    path = tmp_path / "sandbox.json"
    path.write_text(json.dumps(data))
    return path


def test_load_excludes_disabled_profiles(tmp_path):
    config = load_config(write_config(tmp_path, BASE))
    assert set(config.profiles) == {"autonomous", "readonly"}
    assert config.profiles["readonly"].project_write is False
    assert config.profiles["autonomous"].backend == "auto"


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.json")


def test_load_invalid_json_raises(tmp_path):
    path = tmp_path / "sandbox.json"
    path.write_text("{nope")
    with pytest.raises(ConfigError, match="unreadable"):
        load_config(path)


def test_load_no_profiles_raises(tmp_path):
    with pytest.raises(ConfigError, match="no enabled profiles"):
        load_config(write_config(tmp_path, {"profiles": {}}))


@pytest.fixture
def config(tmp_path):
    return load_config(write_config(tmp_path, BASE))


def test_resolve_cli_flag_wins(config):
    assert resolve_profile(config, "readonly", "autonomous").name == "readonly"


def test_resolve_env_used_when_no_flag(config):
    assert resolve_profile(config, None, "readonly").name == "readonly"


def test_resolve_falls_back_to_default(config):
    assert resolve_profile(config, None, None).name == "autonomous"


def test_resolve_unknown_cli_profile_raises(config):
    with pytest.raises(ConfigError, match="unknown profile"):
        resolve_profile(config, "yolo", None)


def test_resolve_unknown_env_profile_raises(config):
    with pytest.raises(ConfigError, match="unknown profile"):
        resolve_profile(config, None, "yolo")


def test_resolve_missing_default_raises(tmp_path):
    config = load_config(
        write_config(
            tmp_path,
            {
                "default_profile": "ghost",
                "profiles": {"readonly": {"enabled": True, "backend": "auto", "project_write": False}},
            },
        )
    )
    with pytest.raises(ConfigError, match="default_profile"):
        resolve_profile(config, None, None)
