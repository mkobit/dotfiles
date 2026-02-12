import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.python.obsidian_local_api.config import load_config


def test_load_config_defaults() -> None:
    # Ensure no config files exist in search path
    # We patch Path.exists to return False so it doesn't pick up any real files
    with patch("src.python.obsidian_local_api.config.Path.exists", return_value=False):
        cfg = load_config()
        assert cfg.token is None
        assert cfg.port == 27124
        assert cfg.host == "127.0.0.1"


def test_load_config_explicit_path(tmp_path: Path) -> None:
    token_file = tmp_path / "my.token"
    token_file.write_text("mytoken")

    config_file = tmp_path / "custom_config.toml"
    config_file.write_text(
        f'token_path = "{token_file}"\nport = 8080\nhost = "0.0.0.0"'
    )

    cfg = load_config(str(config_file))
    assert cfg.token == "mytoken"
    assert cfg.port == 8080
    assert cfg.host == "0.0.0.0"


def test_load_config_explicit_path_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_config("/non/existent/path.toml")


def test_load_config_local_cwd(tmp_path: Path) -> None:
    # Create a local config file in a temp directory and switch to it
    orig_cwd = os.getcwd()
    os.chdir(tmp_path)

    token_file = tmp_path / "local.token"
    token_file.write_text("local_token")

    try:
        (tmp_path / "obsidian-local-api.toml").write_text(
            f'token_path = "{token_file}"'
        )
        cfg = load_config()
        assert cfg.token == "local_token"
    finally:
        os.chdir(orig_cwd)


def test_load_config_token_path(tmp_path: Path) -> None:
    secret_file = tmp_path / "secret_token"
    secret_file.write_text("secret_value")

    config_file = tmp_path / "config.toml"
    # Write config pointing to secret file
    config_file.write_text(f'token_path = "{secret_file}"')

    cfg = load_config(str(config_file))
    assert cfg.token == "secret_value"
    assert cfg.token_path == str(secret_file)


def test_load_config_local_hidden(tmp_path: Path) -> None:
    # Test loading from .obsidian-local-api.toml
    orig_cwd = os.getcwd()
    os.chdir(tmp_path)

    token_file = tmp_path / "hidden.token"
    token_file.write_text("hidden_token")

    try:
        (tmp_path / ".obsidian-local-api.toml").write_text(
            f'token_path = "{token_file}"'
        )
        cfg = load_config()
        assert cfg.token == "hidden_token"
    finally:
        os.chdir(orig_cwd)


def test_load_config_local_dot_config(tmp_path: Path) -> None:
    # Test loading from .config/obsidian-local-api.toml
    orig_cwd = os.getcwd()
    os.chdir(tmp_path)
    config_dir = tmp_path / ".config"
    config_dir.mkdir()

    token_file = tmp_path / "dot_config.token"
    token_file.write_text("dot_config_token")

    try:
        (config_dir / "obsidian-local-api.toml").write_text(
            f'token_path = "{token_file}"'
        )
        cfg = load_config()
        assert cfg.token == "dot_config_token"
    finally:
        os.chdir(orig_cwd)


def test_load_config_xdg(tmp_path: Path) -> None:
    # Setup XDG Config Home structure
    xdg_home = tmp_path / "xdg_config"
    xdg_home.mkdir()
    obsidian_conf_dir = xdg_home / "obsidian-local-api"
    obsidian_conf_dir.mkdir(parents=True)

    token_file = tmp_path / "xdg.token"
    token_file.write_text("xdg_token")

    (obsidian_conf_dir / "config.toml").write_text(f'token_path = "{token_file}"')

    # Create a separate empty CWD
    cwd_dir = tmp_path / "cwd"
    cwd_dir.mkdir()

    orig_cwd = os.getcwd()
    os.chdir(cwd_dir)
    try:
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(xdg_home)}):
            cfg = load_config()
            assert cfg.token == "xdg_token"
    finally:
        os.chdir(orig_cwd)
