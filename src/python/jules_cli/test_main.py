import json
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner
from whenever import Instant

from jules_cli.config import JulesConfig
from jules_cli.main import cli, get_api_key
from jules_cli.models import Activity, GitHubRepo, JulesContext, Session, Source, SourceContext


def test_get_api_key_ignores_env_var() -> None:
    with (
        patch.dict(os.environ, {"JULES_API_KEY": "env_key"}),
        patch("jules_cli.main.load_config", return_value=JulesConfig()),
        patch("pathlib.Path.exists", return_value=False),
        pytest.raises(SystemExit),
    ):
        get_api_key()


def test_get_api_key_from_config() -> None:
    mock_config = MagicMock()
    mock_config.api_key = "config_key"
    with patch("jules_cli.main.load_config", return_value=mock_config):
        assert get_api_key() == "config_key"


def test_get_api_key_override() -> None:
    # Even if config fails, override should win
    with patch("jules_cli.main.load_config", side_effect=Exception("No config")):
        assert get_api_key("override_key") == "override_key"


def test_cli_help_example_toml() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert 'api_key_path = "~/.config/jules/api_key"' in result.output
    assert "JULES_API_KEY" not in result.output


def test_list_sessions_cli_override() -> None:
    runner = CliRunner()
    with patch("jules_cli.main.JulesClient") as mock_client:
        # Mock context manager
        instance = mock_client.return_value
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)

        # Mock list_sessions to return empty generator
        async def mock_list() -> AsyncGenerator[None, None]:
            if False:
                yield

        instance.list_sessions.return_value = mock_list()

        result = runner.invoke(cli, ["--api-key", "cli_override_key", "session", "list"])

        if result.exit_code != 0:
            print(result.output)

        assert result.exit_code == 0
        mock_client.assert_called_with(api_key="cli_override_key")


def test_list_sessions_json() -> None:
    runner = CliRunner()
    with patch("jules_cli.main.JulesClient") as mock_client:
        instance = mock_client.return_value
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
    with patch("jules_cli.main.JulesClient") as mock_client:
        instance = mock_client.return_value
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

        result = runner.invoke(cli, ["--api-key", "key", "session", "show", "sessions/1", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "1"
        assert data["title"] == "Test Session"
        assert data["activities"] == []


def test_create_session_json() -> None:
    runner = CliRunner()
    with patch("jules_cli.main.JulesClient") as mock_client:
        instance = mock_client.return_value
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
    with patch("jules_cli.main.JulesClient") as mock_client:
        instance = mock_client.return_value
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
        with (
            patch.dict(os.environ, env),
            pytest.raises(SystemExit),
        ):
            # Also need to make sure legacy check fails.
            # legacy check: $XDG_CONFIG_HOME/jules/api_key
            # tmp_path is empty, so it should fail.

            # We must NOT mock load_config here.
            get_api_key()
    finally:
        os.chdir(cwd)


def test_cli_context_type() -> None:
    runner = CliRunner()

    @cli.command(name="debug_ctx")
    def debug_cmd(ctx: typer.Context) -> None:
        assert isinstance(ctx.obj, JulesContext)
        typer.echo(f"Key: {ctx.obj.api_key}")

    # Temporarily attach command to cli for testing
    # We shouldn't modify the global cli object ideally, but for testing it's okay
    # provided we are careful. Click groups are mutable.

    result = runner.invoke(cli, ["--api-key", "my_key", "debug_ctx"])
    assert result.exit_code == 0
    assert "Key: my_key" in result.output


def test_approve_session_cli() -> None:
    runner = CliRunner()
    with patch("jules_cli.main.JulesClient") as mock_client:
        instance = mock_client.return_value
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
    with patch("jules_cli.main.JulesClient") as mock_client:
        instance = mock_client.return_value
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


def test_activity_show_cli() -> None:
    runner = CliRunner()
    with patch("jules_cli.main.JulesClient") as mock_client:
        instance = mock_client.return_value
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)

        mock_activity = Activity(
            name="sessions/1/activities/1", id="1", originator="agent", create_time=Instant.from_utc(2023, 1, 1)
        )
        instance.get_activity = AsyncMock(return_value=mock_activity)

        result = runner.invoke(cli, ["--api-key", "key", "activity", "show", "sessions/1/activities/1"])

        assert result.exit_code == 0
        instance.get_activity.assert_called_once_with("sessions/1/activities/1")
        assert "Activity: sessions/1/activities/1" in result.output
        assert "Originator: agent" in result.output


def test_activity_list_cli() -> None:
    runner = CliRunner()
    with patch("jules_cli.main.JulesClient") as mock_client:
        instance = mock_client.return_value
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)

        async def mock_activities() -> AsyncGenerator[Activity, None]:
            yield Activity(
                name="sessions/1/activities/1", id="1", originator="agent", create_time=Instant.from_utc(2023, 1, 1)
            )

        instance.list_activities.return_value = mock_activities()

        result = runner.invoke(cli, ["--api-key", "key", "activity", "list", "sessions/1"])

        assert result.exit_code == 0
        assert "sessions/1/activities/1: agent" in result.output


def test_source_show_cli() -> None:
    runner = CliRunner()
    with patch("jules_cli.main.JulesClient") as mock_client:
        instance = mock_client.return_value
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)

        mock_source = Source(name="sources/1", id="1", github_repo=GitHubRepo(owner="owner", repo="repo"))
        instance.get_source = AsyncMock(return_value=mock_source)

        result = runner.invoke(cli, ["--api-key", "key", "source", "show", "sources/1"])

        assert result.exit_code == 0
        instance.get_source.assert_called_once_with("sources/1")
        assert "Source: sources/1" in result.output
        assert "GitHub Repo: owner/repo" in result.output


def test_source_list_cli() -> None:
    runner = CliRunner()
    with patch("jules_cli.main.JulesClient") as mock_client:
        instance = mock_client.return_value
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)

        async def mock_sources() -> AsyncGenerator[Source, None]:
            yield Source(name="sources/1", id="1")

        instance.list_sources.return_value = mock_sources()

        result = runner.invoke(cli, ["--api-key", "key", "source", "list"])

        assert result.exit_code == 0
        assert "sources/1" in result.output
