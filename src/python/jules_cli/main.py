import asyncio
import click
import shutil
import subprocess
import os
import sys
from typing import Optional
from src.python.jules_cli.client import JulesClient
from src.python.jules_cli.models import Session, Activity

@click.group()
def cli():
    """Jules CLI tool for interacting with the Jules API."""
    pass

def run_fzf(items: list[str]) -> Optional[str]:
    """Runs fzf with the given items and returns the selected item."""
    if not shutil.which("fzf"):
        click.echo("Error: fzf is not installed.", err=True)
        sys.exit(1)

    # Use subprocess to run fzf
    # stderr=None is crucial for fzf to render correctly on the terminal
    process = subprocess.Popen(
        ["fzf", "--height=40%", "--layout=reverse", "--border"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
        text=True
    )

    input_str = "\n".join(items)
    stdout, _ = process.communicate(input=input_str)

    if process.returncode == 0 and stdout:
        return stdout.strip()
    return None

async def interactive_session_loop(client: JulesClient, session_id: str):
    """Interactive loop for a specific session."""
    while True:
        click.clear()
        try:
            activities = await client.list_activities(session_id)
        except Exception as e:
            click.echo(f"Error fetching activities: {e}")
            click.pause()
            break

        # Display activities
        click.echo(f"Session: {session_id}")
        click.echo("-" * 40)

        for activity in activities:
            if activity.originator == "user":
                click.secho(f"User: ", fg="green", bold=True, nl=False)
                # Try to find what user said. The API structure for User message isn't explicit in Activity fields
                # except maybe imply it's missing or look at previous message?
                # Actually, in the example, User activity has 'planApproved'.
                # But for messages, it might be different.
                # Wait, the example didn't show a simple user message activity.
                # Assuming standard chat log.
                click.echo(f"(Action: {activity.name})") # Placeholder
            else:
                click.secho(f"Agent: ", fg="blue", bold=True, nl=False)
                if activity.progressUpdated:
                    click.echo(f"{activity.progressUpdated.title}")
                    if activity.progressUpdated.description:
                         click.echo(f"  {activity.progressUpdated.description}")
                elif activity.planGenerated:
                    click.echo("Generated Plan:")
                    for step in activity.planGenerated.plan.steps:
                        click.echo(f"  {step.index}. {step.title}")
                else:
                    click.echo("(Other activity)")

            click.echo("")

        # Options
        click.echo("-" * 40)
        click.echo("[r]eply, [a]pprove plan, [R]efresh, [b]ack")

        char = click.getchar()
        if char == 'b':
            break
        elif char == 'R':
            continue
        elif char == 'r':
            msg = click.prompt("Message")
            await client.send_message(session_id, msg)
        elif char == 'a':
            confirm = click.confirm("Approve latest plan?")
            if confirm:
                await client.approve_plan(session_id)

async def main_menu():
    try:
        async with JulesClient() as client:
            while True:
                click.clear()
                click.echo("Fetching sessions...")
                try:
                    sessions = await client.list_sessions()
                except Exception as e:
                    click.echo(f"Error fetching sessions: {e}")
                    # If API key is wrong or connection fails
                    if "JULES_API_KEY" not in os.environ:
                         click.echo("Make sure JULES_API_KEY is set.")
                    sys.exit(1)

                if not sessions:
                    click.echo("No sessions found.")
                    return

                # Format for fzf
                # "ID | Title"
                # But session.name is like "sessions/123", session.id is "123"
                items = [f"{s.id} | {s.title}" for s in sessions]

                selected = run_fzf(items)
                if not selected:
                    break

                session_id = selected.split(" | ")[0]
                await interactive_session_loop(client, session_id)

    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

@cli.command()
def interact():
    """Interactive mode to view and manage sessions."""
    asyncio.run(main_menu())

@cli.command()
@click.argument("message")
@click.option("--session", required=True, help="Session ID")
def send(message, session):
    """Send a message to a session."""
    async def _send():
        async with JulesClient() as client:
            await client.send_message(session, message)
            click.echo("Message sent.")
    asyncio.run(_send())

@cli.command()
@click.option("--page-size", default=10, help="Number of sessions to list")
def list_sessions(page_size):
    """List recent sessions."""
    async def _list():
        async with JulesClient() as client:
            sessions = await client.list_sessions(page_size=page_size)
            for s in sessions:
                click.echo(f"{s.id}: {s.title}")
    asyncio.run(_list())

if __name__ == "__main__":
    cli()
