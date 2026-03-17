"""Entry point for skill sync: bazel run //tools/agents:sync."""

import sys
from pathlib import Path

import click

from tools.agents.skills_cli.core import sync_all


@click.command()
@click.option(
    "--workspace",
    envvar="BUILD_WORKSPACE_DIRECTORY",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Workspace root (set automatically by bazel run).",
)
@click.option("--verbose/--quiet", default=True, help="Print progress messages.")
def main(workspace: Path, verbose: bool) -> None:
    """Sync portable skills to chezmoi tool directories."""
    results, ok = sync_all(workspace, verbose=verbose)
    if not ok:
        sys.exit(1)

    synced = [r for r in results if r.action != "up_to_date"]
    if not synced:
        print("All skill copies already up to date.")
    else:
        print(f"Synced {len(synced)} skill(s).")


if __name__ == "__main__":
    main()
