"""Entry point for skill drift check: bazel run //tools/agents:check."""

import sys
from pathlib import Path

import click

from tools.agents.skills_cli.core import check_all


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
    """Check that committed skill copies match their source."""
    results, ok = check_all(workspace, verbose=verbose)

    if not ok:
        drift_count = sum(1 for r in results if r.drifted)
        print()
        print(
            f"Skill copies are out of date ({drift_count} drifted). "
            "Run: bazel run //tools/agents:sync"
        )
        sys.exit(1)

    print("All skill copies are up to date.")


if __name__ == "__main__":
    main()
