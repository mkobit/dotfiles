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
    config_file = tmp_path / "custom_config.toml"
    config_file.write_text('token = "mytoken"\nport = 8080\nhost = "0.0.0.0"')

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
    try:
        (tmp_path / "obsidian-local-api.toml").write_text('token = "local_token"')
        cfg = load_config()
        assert cfg.token == "local_token"
    finally:
        os.chdir(orig_cwd)


def test_load_config_xdg(tmp_path: Path) -> None:
    # Setup XDG Config Home structure
    xdg_home = tmp_path / "xdg_config"
    xdg_home.mkdir()
    obsidian_conf_dir = xdg_home / "obsidian-local-api"
    obsidian_conf_dir.mkdir(parents=True)
    (obsidian_conf_dir / "config.toml").write_text('token = "xdg_token"')

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
