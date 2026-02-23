
import os
from unittest.mock import patch, MagicMock, AsyncMock
from src.python.jules_cli.main import get_api_key, cli
from src.python.jules_cli.config import JulesConfig
import click
from click.testing import CliRunner
import pytest
from typing import AsyncGenerator
from pathlib import Path

def test_get_api_key_ignores_env_var() -> None:
    with patch.dict(os.environ, {"JULES_API_KEY": "env_key"}):
        # Mock load_config to return empty config
        with patch("src.python.jules_cli.main.load_config", return_value=JulesConfig()):
            # Mock legacy file check to return False
            with patch("pathlib.Path.exists", return_value=False):
                with pytest.raises(SystemExit):
                    get_api_key()

def test_get_api_key_from_config() -> None:
    mock_config = MagicMock()
    mock_config.api_key = "config_key"
    with patch("src.python.jules_cli.main.load_config", return_value=mock_config):
        assert get_api_key() == "config_key"

def test_get_api_key_override() -> None:
    # Even if config fails, override should win
    with patch("src.python.jules_cli.main.load_config", side_effect=Exception("No config")):
        assert get_api_key("override_key") == "override_key"

def test_cli_help_example_toml() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert 'api_key_path = "~/.config/jules/api_key"' in result.output
    assert "JULES_API_KEY" not in result.output

def test_list_sessions_cli_override() -> None:
    runner = CliRunner()
    with patch("src.python.jules_cli.main.JulesClient") as MockClient:
        # Mock context manager
        instance = MockClient.return_value
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)

        # Mock list_sessions to return empty generator
        async def mock_list() -> AsyncGenerator[None, None]:
            if False: yield
        instance.list_sessions.return_value = mock_list()

        result = runner.invoke(cli, ["--api-key", "cli_override_key", "list"])

        if result.exit_code != 0:
            print(result.output)

        assert result.exit_code == 0
        MockClient.assert_called_with(api_key="cli_override_key")

def test_integration_env_var_ignored(tmp_path: Path) -> None:
    # This test verifies that get_api_key truly ignores JULES_API_KEY
    # when using real logic (no mocking of load_config internals).

    # Setup environment
    env = {
        "JULES_API_KEY": "evil_env_key",
        "XDG_CONFIG_HOME": str(tmp_path),
    }

    # Ensure no config files exist in tmp_path (it's empty)
    # Ensure no jules.toml in CWD
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        with patch.dict(os.environ, env):
            # Also need to make sure legacy check fails.
            # legacy check: $XDG_CONFIG_HOME/jules/api_key
            # tmp_path is empty, so it should fail.

            # We must NOT mock load_config here.

            with pytest.raises(SystemExit):
                get_api_key()
    finally:
        os.chdir(cwd)
