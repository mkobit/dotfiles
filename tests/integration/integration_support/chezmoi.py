"""Build chezmoi commands for deployed and isolated test environments."""

import asyncio
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path
from subprocess import CompletedProcess

from chezmoi_cli import ChezmoiCli


def chezmoi_argv(
    *args: str,
    source: Path,
    destination: Path | str | None = None,
    config: Path | str | None = None,
    cache: Path | str | None = None,
    state: Path | None = None,
) -> Sequence[str]:
    return list(
        ChezmoiCli(
            source=source,
            destination=destination,
            config=config,
            cache=cache,
            persistent_state=state,
        )
        .raw(*args)
        .argv
    )


async def run_chezmoi(argv: Sequence[str]) -> CompletedProcess[str]:
    """Run a chezmoi command and capture its exit status and output."""
    process = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
    finally:
        if process.returncode is None:
            with suppress(ProcessLookupError):
                process.kill()
            await process.communicate()
    return CompletedProcess(
        argv,
        await process.wait(),
        stdout.decode(errors="replace"),
        stderr.decode(errors="replace"),
    )
