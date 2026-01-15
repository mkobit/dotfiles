import asyncio
import json
import os
from typing import Any

import click

from src.python.obsidian_local_api.client import ObsidianClient
from src.python.obsidian_local_api.config import load_config


def async_command(f: Any) -> Any:
    from functools import update_wrapper

    @click.pass_context
    def wrapper(ctx: Any, *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(ctx, *args, **kwargs))

    return update_wrapper(wrapper, f)


@click.group()
@click.option(
    '--token',
    help='Obsidian Local REST API Token. Can also be set in config file.'
)
@click.option('--port', type=int, default=None, help='Obsidian Local REST API Port (default 27124)')
@click.option('--host', default=None, help='Obsidian Local REST API Host (default 127.0.0.1)')
@click.option('--config', default=None, help='Path to configuration file')
@click.pass_context
def cli(
    ctx: Any,
    token: str | None,
    port: int | None,
    host: str | None,
    config: str | None
) -> None:
    # Load config
    try:
        cfg = load_config(config)
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        ctx.exit(1)

    # Resolve values (CLI args > Config file > Defaults)
    final_token = token if token else cfg.token
    final_port = port if port is not None else cfg.port
    final_host = host if host else cfg.host

    if not final_token:
        click.echo(
            "Error: Token is required. Pass --token, or set 'token' in "
            "config file (./obsidian-local-api.toml or "
            "~/.config/obsidian-local-api/config.toml)",
            err=True
        )
        ctx.exit(1)

    ctx.obj = ObsidianClient(token=final_token, port=final_port, host=final_host)


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
