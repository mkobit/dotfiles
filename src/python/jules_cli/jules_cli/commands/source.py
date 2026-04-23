import asyncio
import json

import typer

from jules_cli.client import JulesClient
from jules_cli.models import JulesContext
from jules_cli.utils import get_api_key

source_app = typer.Typer(add_completion=False, help="Manage sources.")

__all__ = ["source_app"]


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
