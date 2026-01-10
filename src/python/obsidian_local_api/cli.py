import asyncio
import json
import os
from typing import Any

import click

from src.python.obsidian_local_api.client import ObsidianClient


def async_command(f: Any) -> Any:
    from functools import update_wrapper

    @click.pass_context
    def wrapper(ctx: Any, *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(ctx, *args, **kwargs))

    return update_wrapper(wrapper, f)


def get_token() -> str | None:
    """Retrieve the Obsidian API token from environment or config."""
    # Priority 1: Environment Variable (Direct Token)
    token = os.environ.get("OBSIDIAN_API_TOKEN")
    if token:
        return token

    # Priority 2: Environment Variable (Token File)
    token_file = os.environ.get("OBSIDIAN_API_TOKEN_FILE")
    if token_file and os.path.exists(token_file):
        try:
            with open(token_file) as f:
                return f.read().strip()
        except OSError:
            pass

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


@click.group()
@click.option(
    '--token',
    help='Obsidian Local REST API Token. Defaults to OBSIDIAN_API_TOKEN '
         'env var, OBSIDIAN_API_TOKEN_FILE env var, '
         'or ~/.config/obsidian-local-api/token'
)
@click.option('--port', default=27124, help='Obsidian Local REST API Port')
@click.pass_context
def cli(ctx: Any, token: str | None, port: int) -> None:
    if not token:
        token = get_token()

    if not token:
        click.echo(
            "Error: Token is required. Set OBSIDIAN_API_TOKEN, pass --token, "
            "set OBSIDIAN_API_TOKEN_FILE, or create "
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
        click.echo(json.dumps(results, indent=2))
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
        click.echo(json.dumps(results, indent=2))
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
        click.echo(json.dumps(results, indent=2))
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
        click.echo(json.dumps(results, indent=2))
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
