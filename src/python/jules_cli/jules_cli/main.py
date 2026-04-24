import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import typer

from jules_cli.client import JulesClient
from jules_cli.config import load_config
from jules_cli.models import (
    AutomationMode,
    CreateSessionRequest,
    GitHubRepoContext,
    JulesContext,
    SourceContext,
)

cli = typer.Typer(
    add_completion=False,
    name="jules",
    help="""Jules CLI tool for interacting with the Jules API.

    This tool allows you to create and manage coding sessions with the Jules agent.
    For more information about the Jules API, visit:
    https://developers.google.com/jules/api/reference/rest

    Configuration:
    The tool looks for a configuration file at `~/.config/jules/config.toml`.

    Example Configuration (`~/.config/jules/config.toml`):

    \b
        # Path to the file containing the API key
        api_key_path = "~/.config/jules/api_key"
    """,
)

session_app = typer.Typer(add_completion=False, help="Manage sessions.")
cli.add_typer(session_app, name="session")


@cli.callback()
def main_callback(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
    api_key: str | None = typer.Option(None, "--api-key", help="Jules API key (overrides config)."),
) -> None:
    ctx.obj = JulesContext(api_key=api_key)
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)


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


@session_app.command()
def interact(ctx: typer.Context) -> None:
    """Interactive mode to view and manage sessions.

    Launches an interactive TUI (using fzf) to browse sessions and interact with them.

    Example:
    $ jules session interact
    """
    jules_ctx: JulesContext = ctx.obj
    asyncio.run(main_menu(jules_ctx.api_key))


@session_app.command(name="list")
def list_sessions(
    ctx: typer.Context, as_json: bool = typer.Option(False, "--json", help="Output in JSON format.")
) -> None:
    """List recent sessions.

    Displays a list of recent Jules sessions with their IDs, titles, states, and URLs.

    Example:
    $ jules session list
    """

    async def _list() -> None:
        jules_ctx: JulesContext = ctx.obj
        api_key = get_api_key(jules_ctx.api_key)
        async with JulesClient(api_key=api_key) as client:
            if as_json:
                sessions = [s.model_dump(mode="json", by_alias=True) async for s in client.list_sessions()]
                typer.echo(json.dumps(sessions, indent=2))
            else:
                async for s in client.list_sessions():
                    typer.echo(f"{s.id}: {s.title}")

    asyncio.run(_list())


@session_app.command()
def show(
    ctx: typer.Context,
    session_id: str = typer.Argument(..., help="The unique identifier of the session (e.g., 'sessions/12345')."),
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """Show details for a session.

    Displays detailed information about a specific session, including its state,
    URL, prompt, source, and recent activity.

    Arguments:
        SESSION_ID: The unique identifier of the session (e.g., 'sessions/12345').

    Example:
    $ jules session show sessions/12345
    """

    async def _show() -> None:
        jules_ctx: JulesContext = ctx.obj
        api_key = get_api_key(jules_ctx.api_key)
        async with JulesClient(api_key=api_key) as client:
            try:
                # Fetch session info
                session = await client.get_session(session_id)
                if as_json:
                    activities = [
                        a.model_dump(mode="json", by_alias=True) async for a in client.list_activities(session_id)
                    ]
                    session_dict = session.model_dump(mode="json", by_alias=True)
                    session_dict["activities"] = activities
                    typer.echo(json.dumps(session_dict, indent=2))
                else:
                    typer.echo(f"Title: {session.title}")
                    typer.echo(f"State: {session.state.value if session.state else 'Unknown'}")
                    if session.url:
                        typer.echo(f"URL: {session.url}")
                    typer.echo(f"Prompt: {session.prompt}")
                    typer.echo(f"Source: {session.source_context.source}")
                    typer.echo("-" * 20)
                    async for act in client.list_activities(session_id):
                        typer.echo(f"{act.originator}: {act.name}")
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)

    asyncio.run(_show())


@session_app.command()
def message(
    ctx: typer.Context,
    session_id: str = typer.Argument(..., help="The unique identifier of the session (e.g., 'sessions/12345')."),
    message: str | None = typer.Option(
        None, "--message", "-m", help="The message to send to the session (use '-' for stdin)."
    ),
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """Send a follow-up message to an existing session.

    Sends a message to the specified Jules session. You can provide the message
    directly via `--message`. If it's not provided or is set to '-', the message
    will be read from stdin.

    Arguments:
        SESSION_ID: The unique identifier of the session (e.g., 'sessions/12345').

    Examples:
    \b
    # Send a short message
    $ jules session message sessions/12345 -m "Fix the tests"

    \b
    # Read message from a file
    $ jules session message sessions/12345 < msg.txt

    \b
    # Read message from stdin
    $ echo "Please refactor this" | jules session message sessions/12345
    """

    async def _message() -> None:
        jules_ctx: JulesContext = ctx.obj
        api_key = get_api_key(jules_ctx.api_key)

        # Determine message content
        content = None
        if message and message != "-":
            content = message
        # Read from stdin if `-m -` was used or no message was provided
        elif not sys.stdin.isatty():
            content = sys.stdin.read()
        elif message == "-":
            # Fallback if user explicitly passed `-` but it's a TTY (wait for EOF)
            content = sys.stdin.read()
        else:
            typer.echo(
                "Error: No message provided. Use --message or pipe to stdin.",
                err=True,
            )
            sys.exit(1)

        content = content.strip()
        if not content:
            typer.echo("Error: Message is empty.", err=True)
            sys.exit(1)

        async with JulesClient(api_key=api_key) as client:
            try:
                result = await client.send_message(session_id, content)
                if as_json:
                    typer.echo(json.dumps(result, indent=2))
                else:
                    typer.echo(f"Message sent to session {session_id}")
            except Exception as e:
                typer.echo(f"Error sending message: {e}", err=True)
                sys.exit(1)

    asyncio.run(_message())


@session_app.command()
def approve(
    ctx: typer.Context,
    session_id: str = typer.Argument(..., help="The unique identifier of the session (e.g., 'sessions/12345')."),
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """Approve a plan for a session.

    Approves the plan generated by the agent for the specified session,
    allowing it to proceed with execution.

    Arguments:
        SESSION_ID: The unique identifier of the session (e.g., 'sessions/12345').

    Example:
    $ jules session approve sessions/12345
    """

    async def _approve() -> None:
        jules_ctx: JulesContext = ctx.obj
        api_key = get_api_key(jules_ctx.api_key)

        async with JulesClient(api_key=api_key) as client:
            try:
                result = await client.approve_plan(session_id)
                if as_json:
                    typer.echo(json.dumps(result, indent=2))
                else:
                    typer.echo(f"Plan approved for session {session_id}")
            except Exception as e:
                typer.echo(f"Error approving plan: {e}", err=True)
                sys.exit(1)

    asyncio.run(_approve())


@session_app.command()
def create(
    ctx: typer.Context,
    prompt: str = typer.Option(..., "--prompt", help="The initial prompt for the session."),
    source: str = typer.Option(..., "--source", help="The source (e.g., owner/repo)."),
    branch: str = typer.Option("main", "--branch", help="Starting branch (default: main)."),
    title: str | None = typer.Option(None, "--title", help="Title for the session."),
    auto_pr: bool = typer.Option(
        True,
        "--auto-pr/--no-auto-pr",
        help=("Enables Jules to automatically create a pull request upon completion of the task. Enabled by default."),
    ),
    auto_approve: bool = typer.Option(
        True,
        "--auto-approve/--no-auto-approve",
        help=(
            "Enables Jules to automatically approve generated plans. Enabled by default. "
            "When disabled (--no-auto-approve), manual approval is required before Jules starts the task."
        ),
    ),
    interactive: bool = typer.Option(
        False, "--interactive/--no-interactive", "-i", help="Enter interactive mode after creating the session."
    ),
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """Create a new session.

    Starts a new coding session with Jules on the given source context.
    The session object will contain the assigned URL and initial state.

    Examples:
    \b
    # Create a basic session
    $ jules session create --prompt "Fix bug in main.py" --source owner/repo

    \b
    # Create a session on a specific branch with a title
    $ jules session create --prompt "Refactor auth" --source github/owner/repo \
        --branch dev --title "Auth Refactor"

    \b
    # Create an interactive session
    $ jules session create --prompt "Add new feature" --source owner/repo -i
    """

    async def _create() -> None:
        jules_ctx: JulesContext = ctx.obj
        api_key = get_api_key(jules_ctx.api_key)

        # Format source string
        if not source.startswith("sources/"):
            # Assume github/owner/repo or owner/repo
            full_source = f"sources/{source}" if source.startswith("github/") else f"sources/github/{source}"
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
            require_plan_approval=not auto_approve,
        )

        async with JulesClient(api_key=api_key) as client:
            try:
                session = await client.create_session(req)
                if as_json:
                    typer.echo(json.dumps(session.model_dump(mode="json", by_alias=True), indent=2))
                else:
                    typer.echo(f"Session created: {session.name}")
                    typer.echo(f"Title: {session.title}")
                    typer.echo(f"ID: {session.id}")
                    typer.echo(f"URL: https://jules.google.com/session/{session.id}")

                if interactive:
                    await interactive_session_loop(client, session.id)

            except Exception as e:
                typer.echo(f"Error creating session: {e}", err=True)
                sys.exit(1)

    asyncio.run(_create())


if __name__ == "__main__":
    cli()

activity_app = typer.Typer(add_completion=False, help="Manage activities.")
cli.add_typer(activity_app, name="activity")


@activity_app.command(name="show")
def show_activity(
    ctx: typer.Context,
    activity_name: str = typer.Argument(
        ..., help="The unique identifier of the activity (e.g., 'sessions/123/activities/456')."
    ),
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """Show details for a specific activity.

    Example:
    $ jules activity show sessions/123/activities/456
    """

    async def _show() -> None:
        jules_ctx: JulesContext = ctx.obj
        api_key = get_api_key(jules_ctx.api_key)
        async with JulesClient(api_key=api_key) as client:
            try:
                activity = await client.get_activity(activity_name)
                if as_json:
                    typer.echo(json.dumps(activity.model_dump(mode="json", by_alias=True), indent=2))
                else:
                    typer.echo(f"Activity: {activity.name}")
                    typer.echo(f"Originator: {activity.originator}")
                    typer.echo(f"Created: {activity.create_time}")
                    if activity.description:
                        typer.echo(f"Description: {activity.description}")
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)

    asyncio.run(_show())


@activity_app.command(name="list")
def list_activities(
    ctx: typer.Context,
    session_id: str = typer.Argument(..., help="The session ID to list activities for (e.g., 'sessions/123')."),
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """List activities for a specific session.

    Example:
    $ jules activity list sessions/123
    """

    async def _list() -> None:
        jules_ctx: JulesContext = ctx.obj
        api_key = get_api_key(jules_ctx.api_key)
        async with JulesClient(api_key=api_key) as client:
            if as_json:
                activities = [
                    a.model_dump(mode="json", by_alias=True) async for a in client.list_activities(session_id)
                ]
                typer.echo(json.dumps(activities, indent=2))
            else:
                async for act in client.list_activities(session_id):
                    typer.echo(f"{act.name}: {act.originator} - {act.description or 'No description'}")

    asyncio.run(_list())


source_app = typer.Typer(add_completion=False, help="Manage sources.")
cli.add_typer(source_app, name="source")


@source_app.command(name="show")
def show_source(
    ctx: typer.Context,
    source_name: str = typer.Argument(
        ..., help="The unique identifier of the source (e.g., 'sources/github/owner/repo')."
    ),
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """Show details for a specific source.

    Example:
    $ jules source show sources/github/owner/repo
    """

    async def _show() -> None:
        jules_ctx: JulesContext = ctx.obj
        api_key = get_api_key(jules_ctx.api_key)
        async with JulesClient(api_key=api_key) as client:
            try:
                source = await client.get_source(source_name)
                if as_json:
                    typer.echo(json.dumps(source.model_dump(mode="json", by_alias=True), indent=2))
                else:
                    typer.echo(f"Source: {source.name}")
                    typer.echo(f"ID: {source.id}")
                    if source.github_repo:
                        typer.echo(f"GitHub Repo: {source.github_repo.owner}/{source.github_repo.repo}")
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)

    asyncio.run(_show())


@source_app.command(name="list")
def list_sources(
    ctx: typer.Context,
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """List available sources.

    Example:
    $ jules source list
    """

    async def _list() -> None:
        jules_ctx: JulesContext = ctx.obj
        api_key = get_api_key(jules_ctx.api_key)
        async with JulesClient(api_key=api_key) as client:
            if as_json:
                sources = [s.model_dump(mode="json", by_alias=True) async for s in client.list_sources()]
                typer.echo(json.dumps(sources, indent=2))
            else:
                async for s in client.list_sources():
                    typer.echo(f"{s.name}")

    asyncio.run(_list())
