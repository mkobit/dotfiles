import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

import typer

from jules_cli.commands import activity_app, session_app, source_app
from jules_cli.config import load_config
from jules_cli.core import JulesContext

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


if __name__ == "__main__":
    cli()
