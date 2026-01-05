import asyncio
import click
import shutil
import subprocess
import os
import sys
from src.python.jules_cli.client import JulesClient
from src.python.jules_cli.models import Session, Activity

@click.group()
def cli():
    """Jules CLI tool for interacting with the Jules API."""
    pass

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
        stderr=None
    )

    if result.returncode == 0 and result.stdout:
        return result.stdout.strip()
    return None

async def interactive_session_loop(client: JulesClient, session_id: str):
    """Interactive loop for a specific session."""
    while True:
        click.clear()
        try:
            activities = []
            async for activity in client.list_activities(session_id):
                activities.append(activity)
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
    api_key = os.environ.get("JULES_API_KEY")
    if not api_key:
        click.echo("JULES_API_KEY environment variable is not set.", err=True)
        sys.exit(1)

    try:
        async with JulesClient(api_key=api_key) as client:
            while True:
                click.clear()
                click.echo("Fetching sessions...")
                sessions = []
                try:
                    async for session in client.list_sessions():
                        sessions.append(session)
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

                session_id = selected.split(" | ")[0]
                await interactive_session_loop(client, session_id)

    except ValueError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

@cli.command()
def interact():
    """Interactive mode to view and manage sessions."""
    asyncio.run(main_menu())

if __name__ == "__main__":
    cli()
