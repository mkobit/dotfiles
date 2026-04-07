import os
from unittest.mock import patch, MagicMock, AsyncMock
from jules_cli.main import get_api_key, cli
from jules_cli.config import JulesConfig
from jules_cli.models import JulesContext
import click
from click.testing import CliRunner
import pytest
import json
from typing import Any, AsyncGenerator
from pathlib import Path
from jules_cli.models import Session, SourceContext


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
    with patch(
        "src.python.jules_cli.main.load_config", side_effect=Exception("No config")
    ):
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
            if False:
                yield

        instance.list_sessions.return_value = mock_list()

        result = runner.invoke(
            cli, ["--api-key", "cli_override_key", "session", "list"]
        )

        if result.exit_code != 0:
            print(result.output)

        assert result.exit_code == 0
        MockClient.assert_called_with(api_key="cli_override_key")


def test_list_sessions_json() -> None:
    runner = CliRunner()
    with patch("src.python.jules_cli.main.JulesClient") as MockClient:
        instance = MockClient.return_value
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)

        async def mock_list() -> AsyncGenerator[Session, None]:
            yield Session(
                name="sessions/1",
                id="1",
                title="Test Session",
                source_context=SourceContext(source="test/repo"),
                prompt="test prompt",
            )

        instance.list_sessions.return_value = mock_list()

        result = runner.invoke(cli, ["--api-key", "key", "session", "list", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["id"] == "1"
        assert data[0]["title"] == "Test Session"


def test_show_session_json() -> None:
    runner = CliRunner()
    with patch("src.python.jules_cli.main.JulesClient") as MockClient:
        instance = MockClient.return_value
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)

        mock_session = Session(
            name="sessions/1",
            id="1",
            title="Test Session",
            source_context=SourceContext(source="test/repo"),
            prompt="test prompt",
        )
        instance.get_session = AsyncMock(return_value=mock_session)

        async def mock_activities() -> AsyncGenerator[Any, None]:
            if False:
                yield

        instance.list_activities.return_value = mock_activities()

        result = runner.invoke(
            cli, ["--api-key", "key", "session", "show", "sessions/1", "--json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "1"
        assert data["title"] == "Test Session"
        assert data["activities"] == []


def test_create_session_json() -> None:
    runner = CliRunner()
    with patch("src.python.jules_cli.main.JulesClient") as MockClient:
        instance = MockClient.return_value
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)

        mock_session = Session(
            name="sessions/1",
            id="1",
            title="Test Session",
            source_context=SourceContext(source="test/repo"),
            prompt="test prompt",
        )
        instance.create_session = AsyncMock(return_value=mock_session)

        result = runner.invoke(
            cli,
            [
                "--api-key",
                "key",
                "session",
                "create",
                "--prompt",
                "test",
                "--source",
                "test/repo",
                "--json",
            ],
        )

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "1"
        assert data["title"] == "Test Session"


def test_message_session_with_message() -> None:
    runner = CliRunner()
    with patch("src.python.jules_cli.main.JulesClient") as MockClient:
        instance = MockClient.return_value
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)
        instance.send_message = AsyncMock(return_value={"status": "ok"})

        result = runner.invoke(
            cli,
            ["--api-key", "key", "session", "message", "sessions/1", "-m", "hello"],
        )

        assert result.exit_code == 0
        instance.send_message.assert_called_once_with("sessions/1", "hello")
        assert "Message sent to session sessions/1" in result.output


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


def test_cli_context_type() -> None:
    runner = CliRunner()

    @click.command()
    @click.pass_context
    def debug_cmd(ctx: click.Context) -> None:
        assert isinstance(ctx.obj, JulesContext)
        click.echo(f"Key: {ctx.obj.api_key}")

    # Temporarily attach command to cli for testing
    # We shouldn't modify the global cli object ideally, but for testing it's okay
    # provided we are careful. Click groups are mutable.
    cli.add_command(debug_cmd, name="debug_ctx")

    result = runner.invoke(cli, ["--api-key", "my_key", "debug_ctx"])
    assert result.exit_code == 0
    assert "Key: my_key" in result.output


def test_approve_session_cli() -> None:
    runner = CliRunner()
    with patch("src.python.jules_cli.main.JulesClient") as MockClient:
        instance = MockClient.return_value
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)
        instance.approve_plan = AsyncMock(return_value={"status": "approved"})

        result = runner.invoke(
            cli,
            ["--api-key", "key", "session", "approve", "sessions/1"],
        )

        assert result.exit_code == 0
        instance.approve_plan.assert_called_once_with("sessions/1")
        assert "Plan approved for session sessions/1" in result.output


def test_approve_session_cli_json() -> None:
    runner = CliRunner()
    with patch("src.python.jules_cli.main.JulesClient") as MockClient:
        instance = MockClient.return_value
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)
        instance.approve_plan = AsyncMock(return_value={"status": "approved"})

        result = runner.invoke(
            cli,
            ["--api-key", "key", "session", "approve", "sessions/1", "--json"],
        )

        assert result.exit_code == 0
        instance.approve_plan.assert_called_once_with("sessions/1")
        data = json.loads(result.output)
        assert data["status"] == "approved"
