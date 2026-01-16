import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path

import click

from src.python.jules_cli.client import JulesClient
from src.python.jules_cli.models import (
    AutomationMode,
    CreateSessionRequest,
    GitHubRepoContext,
    SourceContext,
)


@click.group()
def cli() -> None:
    """Jules CLI tool for interacting with the Jules API."""
    pass


def get_api_key() -> str:
    """
    Retrieves the Jules API key.
    Checks XDG config location (~/.config/jules/api_key) only.
    """
    # Check XDG config
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    config_file = Path(xdg_config_home) / "jules" / "api_key"

    if config_file.exists():
        return config_file.read_text().strip()

    click.echo(f"Error: JULES_API_KEY not found in {config_file}.", err=True)
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


async def main_menu() -> None:
    api_key = get_api_key()
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
def interact() -> None:
    """Interactive mode to view and manage sessions."""
    asyncio.run(main_menu())


@cli.command(name="list")
def list_sessions() -> None:
    """List recent sessions."""

    async def _list() -> None:
        api_key = get_api_key()
        async with JulesClient(api_key) as client:
            async for s in client.list_sessions():
                click.echo(f"{s.id}: {s.title}")

    asyncio.run(_list())


@cli.command()
@click.argument("session_id")
def show(session_id: str) -> None:
    """Show details for a session."""

    async def _show() -> None:
        api_key = get_api_key()
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
def create(
    prompt: str,
    source: str,
    branch: str,
    title: str | None,
    auto_pr: bool,
    approve: bool,
    interactive: bool,
) -> None:
    """Create a new session."""

    async def _create() -> None:
        api_key = get_api_key()

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
