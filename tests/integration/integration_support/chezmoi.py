"""Build chezmoi commands for deployed and isolated test environments."""

from pathlib import Path


def chezmoi_argv(
    *args: str,
    source: Path,
    destination: Path | str | None = None,
    config: Path | str | None = None,
    cache: Path | str | None = None,
    state: Path | None = None,
) -> list[str]:
    command = ["chezmoi", "--source", str(source)]
    for flag, value in (
        ("--cache", cache),
        ("--config", config),
        ("--destination", destination),
        ("--persistent-state", state),
    ):
        if value is not None:
            command.extend((flag, str(value)))
    command.extend(args)
    return command
