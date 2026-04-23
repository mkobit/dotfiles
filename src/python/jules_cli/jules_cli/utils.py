import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import typer

from jules_cli.client import JulesClient
from jules_cli.config import load_config


def get_api_key(api_key_override: str | None = None) -> str:
    """
    Retrieves the Jules API key.
    Checks override first, then config, then legacy XDG config location
    (~/.config/jules/api_key).
    """
    if api_key_override:
        return api_key_override

    try:
        config = load_config()
        if config.api_key:
            return config.api_key
    except Exception as e:
        # If loading fails (e.g., config file malformed), log warning and proceed
        logging.warning("Failed to load config: %s", e)

    # Legacy check XDG config
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    legacy_file = Path(xdg_config_home) / "jules" / "api_key"

    if legacy_file.exists():
        return legacy_file.read_text().strip()

    typer.echo(f"Error: API key not found in config or {legacy_file}.", err=True)
    sys.exit(1)


def run_fzf(items: list[str]) -> str | None:
    """Runs fzf with the given items and returns the selected item."""
    if not shutil.which("fzf"):
        typer.echo("Error: fzf is not installed.", err=True)
        sys.exit(1)

    input_str = "\n".join(items)
    result = subprocess.run(
        ["fzf", "--height=40%", "--layout=reverse", "--border"],
        input=input_str,
        text=True,
        stdout=subprocess.PIPE,
        stderr=None,
        check=False,
    )

    if result.returncode == 0 and result.stdout:
        return result.stdout.strip()
    return None


async def interactive_session_loop(  # noqa: C901
    client: JulesClient, session_id: str
) -> None:
    """Interactive loop for a specific session."""
    while True:
        typer.clear()
        try:
            activities = [activity async for activity in client.list_activities(session_id)]
        except Exception as e:
            typer.echo(f"Error fetching activities: {e}")
            typer.pause()
            break

        # Display activities
        typer.echo(f"Session: {session_id}")
        typer.echo("-" * 40)

        for activity in activities:
            if activity.originator == "user":
                typer.secho("User: ", fg="green", bold=True, nl=False)
                if activity.user_messaged:
                    typer.echo(f"{activity.user_messaged.user_message}")
                else:
                    typer.echo(f"(Action: {activity.name})")
            else:
                typer.secho("Agent: ", fg="blue", bold=True, nl=False)
                if activity.agent_messaged:
                    typer.echo(f"{activity.agent_messaged.agent_message}")
                elif activity.progress_updated:
                    typer.echo(f"{activity.progress_updated.title}")
                    if activity.progress_updated.description:
                        typer.echo(f"  {activity.progress_updated.description}")
                elif activity.plan_generated:
                    typer.echo("Generated Plan:")
                    for step in activity.plan_generated.plan.steps:
                        typer.echo(f"  {step.index}. {step.title}")
                elif activity.session_failed:
                    typer.secho(f"Session Failed: {activity.session_failed.reason}", fg="red")
                else:
                    typer.echo("(Other activity)")

            typer.echo("")

        # Options
        typer.echo("-" * 40)
        typer.echo("[r]eply, [a]pprove plan, [R]efresh, [b]ack")

        char = typer.getchar()
        if char == "b":
            break
        if char == "R":
            continue
        if char == "r":
            msg = typer.prompt("Message")
            await client.send_message(session_id, msg)
        elif char == "a":
            confirm = typer.confirm("Approve latest plan?")
            if confirm:
                await client.approve_plan(session_id)


async def main_menu(api_key_override: str | None = None) -> None:
    api_key = get_api_key(api_key_override)
    try:
        async with JulesClient(api_key=api_key) as client:
            while True:
                typer.clear()
                typer.echo("Fetching sessions...")

                try:
                    sessions = [session async for session in client.list_sessions()]
                except Exception as e:
                    typer.echo(f"Error fetching sessions: {e}")
                    sys.exit(1)

                if not sessions:
                    typer.echo("No sessions found.")
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
        typer.echo(str(e), err=True)
        sys.exit(1)
