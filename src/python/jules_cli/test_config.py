import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.python.jules_cli.config import load_config


def test_load_config_defaults() -> None:
    # Ensure no config files exist in search path
    with patch("src.python.jules_cli.config.Path.exists", return_value=False):
        cfg = load_config()
        assert cfg.api_key is None
        assert cfg.api_key_path is None


def test_load_config_explicit_path(tmp_path: Path) -> None:
    config_file = tmp_path / "custom_config.toml"
    config_file.write_text('api_key = "mykey"')

    cfg = load_config(str(config_file))
    assert cfg.api_key == "mykey"


def test_load_config_explicit_path_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_config("/non/existent/path.toml")


def test_load_config_xdg(tmp_path: Path) -> None:
    # Setup XDG Config Home structure
    xdg_home = tmp_path / "xdg_config"
    xdg_home.mkdir()
    jules_conf_dir = xdg_home / "jules"
    jules_conf_dir.mkdir(parents=True)
    (jules_conf_dir / "config.toml").write_text('api_key = "xdg_key"')

    # Create a separate empty CWD
    cwd_dir = tmp_path / "cwd"
    cwd_dir.mkdir()

    orig_cwd = os.getcwd()
    os.chdir(cwd_dir)
    try:
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(xdg_home)}):
            cfg = load_config()
            assert cfg.api_key == "xdg_key"
    finally:
        os.chdir(orig_cwd)


def test_load_config_api_key_path(tmp_path: Path) -> None:
    secret_file = tmp_path / "secret_key"
    secret_file.write_text("secret_value")

    config_file = tmp_path / "config.toml"
    # Write config pointing to secret file
    config_file.write_text(f'api_key_path = "{secret_file}"')

    cfg = load_config(str(config_file))
    assert cfg.api_key == "secret_value"
    assert cfg.api_key_path == str(secret_file)
