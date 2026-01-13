import asyncio
import json
import os
from typing import Any

import click
from dotenv import dotenv_values
from pydantic import BaseModel

from src.python.obsidian_local_api.client import ObsidianClient


def async_command(f: Any) -> Any:
    from functools import update_wrapper

    @click.pass_context
    def wrapper(ctx: Any, *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(ctx, *args, **kwargs))

    return update_wrapper(wrapper, f)


def get_token(token_file: str | None = None) -> str | None:
    """Retrieve the Obsidian API token from specific file or config."""
    # Priority 1: Direct File
    if token_file:
        if not os.path.exists(token_file):
            raise FileNotFoundError(f"Token file not found: {token_file}")
        try:
            with open(token_file) as f:
                return f.read().strip()
        except OSError as e:
            raise OSError(f"Could not read token file {token_file}: {e}") from e

    # Priority 2: .env file (looking for OBSIDIAN_API_TOKEN inside)
    # We search in current directory and parents manually or rely on dotenv
    # python-dotenv load_dotenv loads into environ, but we want to avoid implicit env.
    # dotenv_values returns a dict without touching environ.
    env_config = dotenv_values(".env")
    if "OBSIDIAN_API_TOKEN" in env_config:
        return str(env_config["OBSIDIAN_API_TOKEN"])

    # Priority 3: XDG Config File (~/.config/obsidian-local-api/token)
    xdg_config_home = os.environ.get(
        "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
    )
    config_file = os.path.join(xdg_config_home, "obsidian-local-api", "token")
    if os.path.exists(config_file):
        try:
            with open(config_file) as f:
                return f.read().strip()
        except OSError:
            pass

    return None

def serialize(obj: Any) -> str:
    if isinstance(obj, list):
        return str(json.dumps(
            [
                item.model_dump() if isinstance(item, BaseModel) else item
                for item in obj
            ],
            indent=2,
        ))
    if isinstance(obj, BaseModel):
        return str(obj.model_dump_json(indent=2))
    # json.dumps returns a string, but mypy thinks it might return Any
    # if it can't infer input
    return str(json.dumps(obj, indent=2))


@click.group()
@click.option(
    '--token',
    help='Obsidian Local REST API token. Direct string.'
)
@click.option(
    '--token-file',
    help='Path to file containing the token.'
)
@click.option('--port', default=27124, help='Obsidian Local REST API port.')
@click.pass_context
def cli(ctx: Any, token: str | None, token_file: str | None, port: int) -> None:
    """Interact with Obsidian via the Local REST API.

    Authentication token is resolved in the following order:
    1. --token argument
    2. --token-file argument
    3. OBSIDIAN_API_TOKEN in .env file
    4. ~/.config/obsidian-local-api/token
    """
    if not token:
        token = get_token(token_file)

    if not token:
        click.echo(
            "Error: Token is required. Pass --token, --token-file, "
            "provide a .env file with OBSIDIAN_API_TOKEN, or create "
            "~/.config/obsidian-local-api/token",
            err=True
        )
        ctx.exit(1)

    assert token is not None
    ctx.obj = ObsidianClient(token=token, port=port)


@cli.command()
@click.argument('path')
@async_command
@click.pass_context
async def read(ctx: Any, path: str) -> None:
    """Read a file from the vault."""
    client = ctx.obj
    try:
        content = await client.get_file(path)
        click.echo(content)
    except Exception as e:
        raise click.ClickException(str(e)) from e


@cli.command()
@click.argument('path')
@click.argument('content')
@async_command
@click.pass_context
async def write(ctx: Any, path: str, content: str) -> None:
    """Write content to a file in the vault."""
    client = ctx.obj
    try:
        await client.create_file(path, content)
        click.echo(f"Wrote to {path}")
    except Exception as e:
        raise click.ClickException(str(e)) from e


@cli.command()
@click.argument('path')
@async_command
@click.pass_context
async def delete(ctx: Any, path: str) -> None:
    """Delete a file from the vault."""
    client = ctx.obj
    try:
        await client.delete_file(path)
        click.echo(f"Deleted {path}")
    except Exception as e:
        raise click.ClickException(str(e)) from e


@cli.command(name='list')
@click.argument('folder', default='/', required=False)
@async_command
@click.pass_context
async def list_files(ctx: Any, folder: str) -> None:
    """List files in the vault."""
    client = ctx.obj
    try:
        results = await client.list_files(folder)
        click.echo(serialize(results))
    except Exception as e:
        raise click.ClickException(str(e)) from e


@cli.command()
@click.argument('query')
@async_command
@click.pass_context
async def search(ctx: Any, query: str) -> None:
    """Search the vault."""
    client = ctx.obj
    try:
        results = await client.search(query)
        click.echo(serialize(results))
    except Exception as e:
        raise click.ClickException(str(e)) from e


@cli.command()
@async_command
@click.pass_context
async def active(ctx: Any) -> None:
    """Get the active file."""
    client = ctx.obj
    try:
        results = await client.get_active_file()
        if results:
            click.echo(serialize(results))
        else:
            click.echo("No active file")
    except Exception as e:
        raise click.ClickException(str(e)) from e


@cli.command()
@async_command
@click.pass_context
async def commands(ctx: Any) -> None:
    """List available commands."""
    client = ctx.obj
    try:
        results = await client.list_commands()
        click.echo(serialize(results))
    except Exception as e:
        raise click.ClickException(str(e)) from e


@cli.command()
@click.argument('command_id')
@async_command
@click.pass_context
async def run_command(ctx: Any, command_id: str) -> None:
    """Run a command."""
    client = ctx.obj
    try:
        await client.execute_command(command_id)
        click.echo(f"Executed command: {command_id}")
    except Exception as e:
        raise click.ClickException(str(e)) from e


if __name__ == '__main__':
    cli()
