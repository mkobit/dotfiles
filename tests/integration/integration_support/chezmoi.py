"""Build chezmoi commands for deployed and isolated test environments."""

import asyncio
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path


def chezmoi_argv(
    *args: str,
    source: Path,
    destination: Path | str | None = None,
    config: Path | str | None = None,
    cache: Path | str | None = None,
    state: Path | None = None,
) -> Sequence[str]:
    options = (
        ("--cache", cache),
        ("--config", config),
        ("--destination", destination),
        ("--persistent-state", state),
    )
    flags = [part for flag, value in options if value is not None for part in (flag, str(value))]
    return ["chezmoi", "--source", str(source), *flags, *args]


async def run_chezmoi_async(argv: Sequence[str]) -> str:
    """Run a chezmoi command and return its standard output."""
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
    assert process.returncode == 0, stderr.decode()
    return stdout.decode()
