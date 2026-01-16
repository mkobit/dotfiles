import asyncio
import json
from pathlib import Path
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


def load_config_callback(ctx: Any, param: Any, value: str | None) -> str | None:
    try:
        cfg = load_config(value)
        # Convert config model to dict, filtering out None values
        config_dict = {k: v for k, v in cfg.model_dump().items() if v is not None}
        ctx.default_map = config_dict
    except Exception as e:
        raise click.ClickException(f"Error loading config: {e}") from e
    return value


@click.group()
@click.option(
    "--config",
    default=None,
    help="Path to configuration file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    callback=load_config_callback,
    is_eager=True,
    expose_value=False,
)
@click.option(
    "--token", help="Obsidian Local REST API Token. Can also be set in config file."
)
@click.option("--port", type=int, default=27124, help="Obsidian Local REST API Port")
@click.option("--host", default="127.0.0.1", help="Obsidian Local REST API Host")
@click.pass_context
def cli(ctx: Any, token: str | None, port: int, host: str) -> None:
    if not token:
        click.echo(
            "Error: Token is required. Pass --token, or set 'token' in "
            "config file (./obsidian-local-api.toml or "
            "~/.config/obsidian-local-api/config.toml)",
            err=True,
        )
        ctx.exit(1)

    # We know token is not None here because of the check above
    assert token is not None
    ctx.obj = ObsidianClient(token=token, port=port, host=host)


@cli.command()
@click.argument("path")
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
@click.argument("path")
@click.argument("content")
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
@click.argument("path")
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


@cli.command(name="list")
@click.argument("folder", default="/", required=False)
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
@click.argument("query")
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
@click.argument("command_id")
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


if __name__ == "__main__":
    cli()
