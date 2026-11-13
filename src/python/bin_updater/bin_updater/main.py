from os import environ
from pathlib import Path
from typing import Annotated

import typer

from bin_updater.catalog import NonGitHubReleaseError, discover_catalogs, load_catalog
from bin_updater.client import HttpxReleaseClient
from bin_updater.service import ToolUpdateResult, run_updates

app = typer.Typer(help="Automate chezmoi binary tools upgrades")


def _print_result(result: ToolUpdateResult) -> None:
    if result.error is not None:
        typer.echo(f"Error upgrading {result.tool_name}: {result.error}", err=True)
    elif result.changed:
        typer.echo(f"Upgraded {result.tool_name}: {result.old_version} -> {result.new_version}")
    else:
        typer.echo(f"{result.tool_name} is up to date ({result.old_version})")


@app.command()
def main(
    tool: Annotated[str | None, typer.Option("--tool", "-t", help="Tool name or path to TOML")] = None,
    all_tools: Annotated[bool, typer.Option("--all", "-a", help="Update all binary tools")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Simulate updates without writing changes")] = False,
    token: Annotated[str | None, typer.Option("--token", help="GitHub API token")] = None,
    catalog_dir: Annotated[Path, typer.Option("--catalog-dir", help="Directory containing tool catalogs")] = Path(
        "src/chezmoi/.chezmoidata/bin"
    ),
) -> None:
    """Automate chezmoi binary tools upgrades."""
    if not all_tools and tool is None:
        typer.echo("Error: specify either --tool <name> or --all", err=True)
        raise typer.Exit(code=1)

    auth_token = token or environ.get("GITHUB_TOKEN")

    if tool is not None:
        path = Path(tool) if Path(tool).suffix == ".toml" else catalog_dir / f"{tool}.toml"
        if not path.is_file():
            typer.echo(f"Error: Catalog file not found: {path}", err=True)
            raise typer.Exit(code=1)
        try:
            catalogs = [load_catalog(path)]
        except NonGitHubReleaseError as exc:
            typer.echo(f"Skipping {path.stem}: {exc}")
            raise typer.Exit(code=0) from None
    else:
        catalogs = discover_catalogs(catalog_dir)

    with HttpxReleaseClient(token=auth_token) as client:
        results = run_updates(catalogs, client, dry_run=dry_run)
    for result in results:
        _print_result(result)

    if any(r.error is not None for r in results):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
