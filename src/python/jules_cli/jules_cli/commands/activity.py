import asyncio
import json

import typer

from jules_cli.client import JulesClient
from jules_cli.models import JulesContext
from jules_cli.utils import get_api_key

activity_app = typer.Typer(add_completion=False, help="Manage activities.")

__all__ = ["activity_app"]


@activity_app.command(name="show")
def show_activity(
    ctx: typer.Context,
    activity_name: str = typer.Argument(
        ..., help="The unique identifier of the activity (e.g., 'sessions/123/activities/456')."
    ),
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """Show details for a specific activity.

    Example:
    $ jules activity show sessions/123/activities/456
    """

    async def _show() -> None:
        jules_ctx: JulesContext = ctx.obj
        api_key = get_api_key(jules_ctx.api_key)
        async with JulesClient(api_key=api_key) as client:
            try:
                activity = await client.get_activity(activity_name)
                if as_json:
                    typer.echo(json.dumps(activity.model_dump(mode="json", by_alias=True), indent=2))
                else:
                    typer.echo(f"Activity: {activity.name}")
                    typer.echo(f"Originator: {activity.originator}")
                    typer.echo(f"Created: {activity.create_time}")
                    if activity.description:
                        typer.echo(f"Description: {activity.description}")
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)

    asyncio.run(_show())


@activity_app.command(name="list")
def list_activities(
    ctx: typer.Context,
    session_id: str = typer.Argument(..., help="The session ID to list activities for (e.g., 'sessions/123')."),
    as_json: bool = typer.Option(False, "--json", help="Output in JSON format."),
) -> None:
    """List activities for a specific session.

    Example:
    $ jules activity list sessions/123
    """

    async def _list() -> None:
        jules_ctx: JulesContext = ctx.obj
        api_key = get_api_key(jules_ctx.api_key)
        async with JulesClient(api_key=api_key) as client:
            if as_json:
                activities = [
                    a.model_dump(mode="json", by_alias=True) async for a in client.list_activities(session_id)
                ]
                typer.echo(json.dumps(activities, indent=2))
            else:
                async for act in client.list_activities(session_id):
                    typer.echo(f"{act.name}: {act.originator} - {act.description or 'No description'}")

    asyncio.run(_list())
