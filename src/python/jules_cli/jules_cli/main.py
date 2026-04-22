import logging

import typer

from jules_cli.commands.activity import activity_app
from jules_cli.commands.session import session_app
from jules_cli.commands.source import source_app
from jules_cli.models import JulesContext

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

cli.add_typer(session_app, name="session")
cli.add_typer(activity_app, name="activity")
cli.add_typer(source_app, name="source")


@cli.callback()
def main_callback(
    ctx: typer.Context,
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging."),
    api_key: str | None = typer.Option(None, "--api-key", help="Jules API key (overrides config)."),
) -> None:
    """Jules CLI."""
    # Set up logging
    log_level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Store common arguments in context
    ctx.obj = JulesContext(api_key=api_key, debug=debug)


if __name__ == "__main__":
    cli()
