import asyncio
import json
import sys

import typer

from jules_cli.client import JulesClient
from jules_cli.core import JulesContext
from jules_cli.session import AutomationMode, CreateSessionRequest, SessionState
from jules_cli.source import GitHubRepoContext, SourceContext

session_app = typer.Typer(add_completion=False, help="Manage sessions.")


def _get_api_key(ctx: typer.Context) -> str:
    from jules_cli.main import get_api_key

    jules_ctx: JulesContext = ctx.obj
    return get_api_key(jules_ctx.api_key)


async def interactive_session_loop(client: JulesClient, session_id: str) -> None:
    """Runs an interactive loop for a session."""
    typer.echo(f"Entering interactive mode for session {session_id}")
    typer.echo("Type your messages. Press Ctrl-D to exit.")
    typer.echo("---")

    while True:
        try:
            # Poll state
            try:
                session = await client.get_session(session_id)
                if session.state == SessionState.AWAITING_USER_FEEDBACK:
                    # In a real app, we might fetch the latest activity to see what they're asking.
                    # For now, just prompt the user.
                    pass
                elif session.state in (SessionState.COMPLETED, SessionState.FAILED):
                    typer.echo(f"\nSession finished with state: {session.state.name}")
                    break
            except Exception as e:
                typer.echo(f"Error polling session state: {e}", err=True)

            user_input = input("> ")
            if not user_input.strip():
                continue

            # Send message
            await client.send_message(session_id, user_input)
            typer.echo("Message sent. Waiting for agent...")
            await asyncio.sleep(2)  # Give the agent a moment before polling again

        except EOFError:
            typer.echo("\nExiting interactive mode.")
            break
        except KeyboardInterrupt:
            typer.echo("\nInterrupted.")
            break
        except Exception as e:
            typer.echo(f"\nError in interactive mode: {e}", err=True)
            break


@session_app.command(name="list")
def list_sessions(
    ctx: typer.Context,
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """List all available sessions."""

    async def _list() -> None:
        api_key = _get_api_key(ctx)
        async with JulesClient(api_key=api_key) as client:
            if as_json:
                sessions = [s.model_dump(mode="json", by_alias=True) async for s in client.list_sessions()]
                typer.echo(json.dumps(sessions, indent=2))
            else:
                async for session in client.list_sessions():
                    typer.echo(f"{session.name}: {session.title} - {session.state.name if session.state else 'N/A'}")

    asyncio.run(_list())


@session_app.command(name="show")
def show_session(
    ctx: typer.Context,
    session_id: str = typer.Argument(..., help="The unique identifier of the session (e.g., 'sessions/12345')."),
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """Show details for a specific session.

    Example:
    $ jules session show sessions/12345
    """

    async def _show() -> None:
        api_key = _get_api_key(ctx)
        async with JulesClient(api_key=api_key) as client:
            try:
                session = await client.get_session(session_id)
                if as_json:
                    typer.echo(json.dumps(session.model_dump(mode="json", by_alias=True), indent=2))
                else:
                    typer.echo(f"Session: {session.name}")
                    typer.echo(f"Title: {session.title}")
                    if session.state:
                        typer.echo(f"State: {session.state.name}")
                    typer.echo(f"Prompt: {session.prompt}")
                    if session.outputs:
                        for output in session.outputs:
                            if output.pull_request:
                                typer.echo(f"PR: {output.pull_request.url}")
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)

    asyncio.run(_show())


@session_app.command()
def message(
    ctx: typer.Context,
    session_id: str = typer.Argument(..., help="The unique identifier of the session (e.g., 'sessions/12345')."),
    content: str = typer.Argument(default="", help="The message content to send. If not provided, reads from stdin."),
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """Send a message to a session.

    If CONTENT is not provided as an argument, it reads from standard input (stdin).

    Arguments:
        SESSION_ID: The unique identifier of the session (e.g., 'sessions/12345').
        CONTENT: The message content to send. (Optional)

    Examples:
    $ jules session message sessions/12345 "How is the task progressing?"
    $ echo "Please add more tests." | jules session message sessions/12345
    """

    async def _message() -> None:
        api_key = _get_api_key(ctx)

        nonlocal content
        if not content and not sys.stdin.isatty():
            content = sys.stdin.read()
        if not content:
            typer.echo(
                "Error: No message content provided. Please provide it as an argument or pipe to stdin.",
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
        api_key = _get_api_key(ctx)

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
    r"""Create a new session.

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
        api_key = _get_api_key(ctx)

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
