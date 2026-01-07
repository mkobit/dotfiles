import click
import asyncio
import os
import json
from .client import ObsidianClient

def async_command(f):
    from functools import update_wrapper
    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(ctx, *args, **kwargs))
    return update_wrapper(wrapper, f)

@click.group()
@click.option('--token', envvar='OBSIDIAN_API_TOKEN', help='Obsidian Local REST API Token')
@click.option('--port', default=27124, help='Obsidian Local REST API Port')
@click.pass_context
def cli(ctx, token, port):
    if not token:
        click.echo("Error: Token is required. Set OBSIDIAN_API_TOKEN or pass --token.", err=True)
        ctx.exit(1)
    ctx.obj = ObsidianClient(token=token, port=port)

@cli.command()
@click.argument('path')
@async_command
@click.pass_context
async def read(ctx, path):
    """Read a file from the vault."""
    client = ctx.obj
    try:
        content = await client.get_file(path)
        click.echo(content)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.argument('path')
@click.argument('content')
@async_command
@click.pass_context
async def write(ctx, path, content):
    """Write content to a file in the vault."""
    client = ctx.obj
    try:
        await client.create_file(path, content)
        click.echo(f"Wrote to {path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.argument('path')
@async_command
@click.pass_context
async def delete(ctx, path):
    """Delete a file from the vault."""
    client = ctx.obj
    try:
        await client.delete_file(path)
        click.echo(f"Deleted {path}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.argument('folder', default='/', required=False)
@async_command
@click.pass_context
async def list(ctx, folder):
    """List files in the vault."""
    client = ctx.obj
    try:
        results = await client.list_files(folder)
        click.echo(json.dumps(results, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.argument('query')
@async_command
@click.pass_context
async def search(ctx, query):
    """Search the vault."""
    client = ctx.obj
    try:
        results = await client.search(query)
        click.echo(json.dumps(results, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == '__main__':
    cli()
