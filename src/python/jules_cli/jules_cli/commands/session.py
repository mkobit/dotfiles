import asyncio
import json
import sys

import typer

from jules_cli.client import JulesClient
from jules_cli.models import (
    AutomationMode,
    CreateSessionRequest,
    GitHubRepoContext,
    JulesContext,
    SourceContext,
)
from jules_cli.utils import get_api_key, interactive_session_loop, main_menu

session_app = typer.Typer(add_completion=False, help="Manage sessions.")

__all__ = ["session_app"]


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
    auto_pr: bool = typer.Option(True, "--auto-pr/--no-auto-pr", help="Automatically create a PR."),
    approve: bool = typer.Option(True, "--approve/--no-approve", help="Require manual plan approval."),
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
            require_plan_approval=approve,
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
