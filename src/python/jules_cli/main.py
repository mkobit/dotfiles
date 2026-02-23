import asyncio
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import click

from src.python.jules_cli.client import JulesClient
from src.python.jules_cli.config import load_config
from src.python.jules_cli.models import (
    AutomationMode,
    CreateSessionRequest,
    GitHubRepoContext,
    SourceContext,
)


@click.group()
@click.option("--debug/--no-debug", default=False, help="Enable debug logging.")
@click.option("--api-key", help="Jules API key (overrides config).")
@click.pass_context
def cli(ctx: click.Context, debug: bool, api_key: str | None) -> None:
    """Jules CLI tool for interacting with the Jules API.

    This tool allows you to create and manage coding sessions with the Jules agent.
    For more information about the Jules API, visit:
    https://developers.google.com/jules/api

    Configuration:
    The tool looks for a configuration file at `~/.config/jules/config.toml`.

    Example Configuration (`~/.config/jules/config.toml`):

    \b
        # Path to the file containing the API key
        api_key_path = "~/.config/jules/api_key"
    """
    ctx.ensure_object(dict)
    ctx.obj["api_key"] = api_key
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)


def get_api_key(api_key_override: str | None = None) -> str:
    """
    Retrieves the Jules API key.
    Checks override first, then config, then legacy XDG config location (~/.config/jules/api_key).
    """
    if api_key_override:
        return api_key_override

    try:
        config = load_config()
        if config.api_key:
            return config.api_key
    except Exception as e:
        # If loading fails (e.g., config file malformed), log warning but proceed to legacy check
        logging.warning("Failed to load config: %s", e)

    # Legacy check XDG config
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    legacy_file = Path(xdg_config_home) / "jules" / "api_key"

    if legacy_file.exists():
        return legacy_file.read_text().strip()

    click.echo(f"Error: API key not found in config or {legacy_file}.", err=True)
    sys.exit(1)


def run_fzf(items: list[str]) -> str | None:
    """Runs fzf with the given items and returns the selected item."""
    if not shutil.which("fzf"):
        click.echo("Error: fzf is not installed.", err=True)
        sys.exit(1)

    input_str = "\n".join(items)
    result = subprocess.run(
        ["fzf", "--height=40%", "--layout=reverse", "--border"],
        input=input_str,
        text=True,
        stdout=subprocess.PIPE,
        stderr=None,
    )

    if result.returncode == 0 and result.stdout:
        return result.stdout.strip()
    return None


async def interactive_session_loop(client: JulesClient, session_id: str) -> None:
    """Interactive loop for a specific session."""
    while True:
        click.clear()
        try:
            activities = [
                activity async for activity in client.list_activities(session_id)
            ]
        except Exception as e:
            click.echo(f"Error fetching activities: {e}")
            click.pause()
            break

        # Display activities
        click.echo(f"Session: {session_id}")
        click.echo("-" * 40)

        for activity in activities:
            if activity.originator == "user":
                click.secho("User: ", fg="green", bold=True, nl=False)
                click.echo(f"(Action: {activity.name})")  # Placeholder
            else:
                click.secho("Agent: ", fg="blue", bold=True, nl=False)
                if activity.progress_updated:
                    click.echo(f"{activity.progress_updated.title}")
                    if activity.progress_updated.description:
                        click.echo(f"  {activity.progress_updated.description}")
                elif activity.plan_generated:
                    click.echo("Generated Plan:")
                    for step in activity.plan_generated.plan.steps:
                        click.echo(f"  {step.index}. {step.title}")
                else:
                    click.echo("(Other activity)")

            click.echo("")

        # Options
        click.echo("-" * 40)
        click.echo("[r]eply, [a]pprove plan, [R]efresh, [b]ack")

        char = click.getchar()
        if char == "b":
            break
        elif char == "R":
            continue
        elif char == "r":
            msg = click.prompt("Message")
            await client.send_message(session_id, msg)
        elif char == "a":
            confirm = click.confirm("Approve latest plan?")
            if confirm:
                await client.approve_plan(session_id)


async def main_menu(api_key_override: str | None = None) -> None:
    api_key = get_api_key(api_key_override)
    try:
        async with JulesClient(api_key=api_key) as client:
            while True:
                click.clear()
                click.echo("Fetching sessions...")

                try:
                    sessions = [session async for session in client.list_sessions()]
                except Exception as e:
                    click.echo(f"Error fetching sessions: {e}")
                    sys.exit(1)

                if not sessions:
                    click.echo("No sessions found.")
                    return

                # Format for fzf
                # "ID | Title"
                # But session.name is like "sessions/123", session.id is "123"
                items = [f"{s.name} | {s.title}" for s in sessions]

                selected = run_fzf(items)
                if not selected:
                    break

                # Safer splitting using next/default
                parts = selected.split(" | ")
                session_id = next(iter(parts), None)

                if session_id:
                    await interactive_session_loop(client, session_id)

    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def interact(ctx: click.Context) -> None:
    """Interactive mode to view and manage sessions.

    Launches an interactive TUI (using fzf) to browse sessions and interact with them.

    Example:
    $ jules interact
    """
    asyncio.run(main_menu(ctx.obj.get("api_key")))


@cli.command(name="list")
@click.pass_context
def list_sessions(ctx: click.Context) -> None:
    """List recent sessions.

    Displays a list of recent Jules sessions with their IDs and titles.

    Example:
    $ jules list
    """

    async def _list() -> None:
        api_key = get_api_key(ctx.obj.get("api_key"))
        async with JulesClient(api_key) as client:
            async for s in client.list_sessions():
                click.echo(f"{s.id}: {s.title}")

    asyncio.run(_list())


@cli.command()
@click.argument("session_id")
@click.pass_context
def show(ctx: click.Context, session_id: str) -> None:
    """Show details for a session.

    Displays detailed information about a specific session, including its prompt,
    source, and recent activity.

    Arguments:
        SESSION_ID: The unique identifier of the session (e.g., 'sessions/12345').

    Example:
    $ jules show sessions/12345
    """

    async def _show() -> None:
        api_key = get_api_key(ctx.obj.get("api_key"))
        async with JulesClient(api_key) as client:
            try:
                # Fetch session info
                session = await client.get_session(session_id)
                click.echo(f"Title: {session.title}")
                click.echo(f"Prompt: {session.prompt}")
                click.echo(f"Source: {session.source_context.source}")
                click.echo("-" * 20)
                async for act in client.list_activities(session_id):
                    click.echo(f"{act.originator}: {act.name}")
            except Exception as e:
                click.echo(f"Error: {e}", err=True)

    asyncio.run(_show())


@cli.command()
@click.option("--prompt", required=True, help="The initial prompt for the session.")
@click.option("--source", required=True, help="The source (e.g., owner/repo).")
@click.option("--branch", default="main", help="Starting branch (default: main).")
@click.option("--title", help="Title for the session.")
@click.option(
    "--auto-pr/--no-auto-pr", default=False, help="Automatically create a PR."
)
@click.option(
    "--approve/--no-approve", default=False, help="Require manual plan approval."
)
@click.option(
    "--interactive/--no-interactive",
    "-i",
    default=False,
    help="Enter interactive mode after creating the session.",
)
@click.pass_context
def create(
    ctx: click.Context,
    prompt: str,
    source: str,
    branch: str,
    title: str | None,
    auto_pr: bool,
    approve: bool,
    interactive: bool,
) -> None:
    """Create a new session.

    Starts a new coding session with Jules.

    Examples:
    \b
    # Create a basic session
    $ jules create --prompt "Fix bug in main.py" --source owner/repo

    \b
    # Create a session on a specific branch with a title
    $ jules create --prompt "Refactor auth" --source github/owner/repo --branch dev --title "Auth Refactor"

    \b
    # Create an interactive session
    $ jules create --prompt "Add new feature" --source owner/repo -i
    """

    async def _create() -> None:
        api_key = get_api_key(ctx.obj.get("api_key"))

        # Format source string
        if not source.startswith("sources/"):
            # Assume github/owner/repo or owner/repo
            if source.startswith("github/"):
                full_source = f"sources/{source}"
            else:
                full_source = f"sources/github/{source}"
        else:
            full_source = source

        source_context = SourceContext(
            source=full_source,
            github_repo_context=GitHubRepoContext(starting_branch=branch),
        )

        req = CreateSessionRequest(
            prompt=prompt,
            source_context=source_context,
            automation_mode=AutomationMode.AUTO_CREATE_PR if auto_pr else None,
            title=title,
            require_plan_approval=approve,
        )

        async with JulesClient(api_key) as client:
            try:
                session = await client.create_session(req)
                click.echo(f"Session created: {session.name}")
                click.echo(f"Title: {session.title}")
                click.echo(f"ID: {session.id}")

                if interactive:
                    await interactive_session_loop(client, session.id)

            except Exception as e:
                click.echo(f"Error creating session: {e}", err=True)
                sys.exit(1)

    asyncio.run(_create())


if __name__ == "__main__":
    cli()
