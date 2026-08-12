import os
from pathlib import Path
from typing import Annotated

import typer

from sandboxr.backend.bwrap import build_args, default_mask_paths
from sandboxr.cli._common import (
    _apply_timeout,
    _fail,
    _refuse_if_nested,
    _require_bwrap,
    _sandbox_spec,
)

app = typer.Typer()

_CTX = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
    "allow_interspersed_args": False,
}


@app.command(context_settings=_CTX)
def shell(
    tty: Annotated[
        bool,
        typer.Option("--tty/--no-tty", "-t", help="Allocate a pseudo-TTY."),
    ] = True,
    show_command: Annotated[
        bool,
        typer.Option("--show-command", help="Print bwrap invocation instead of running."),
    ] = False,
    project_write: Annotated[
        bool,
        typer.Option(
            "--project-write/--no-project-write", help="Mount project directory read-write."
        ),
    ] = True,
    network: Annotated[
        str,
        typer.Option("--network", help="Network mode: shared|none."),
    ] = "shared",
    ssh_agent: Annotated[
        bool,
        typer.Option("--ssh-agent/--no-ssh-agent", help="Forward host SSH agent socket."),
    ] = True,
    gpg_agent: Annotated[
        bool,
        typer.Option("--gpg-agent/--no-gpg-agent", help="Forward host GPG agent socket."),
    ] = False,
    extra_ro: Annotated[
        list[str] | None,
        typer.Option("--ro", help="Bind path read-only (repeatable)."),
    ] = None,
    extra_rw: Annotated[
        list[str] | None,
        typer.Option("--rw", help="Bind path read-write (repeatable)."),
    ] = None,
    timeout: Annotated[
        float | None,
        typer.Option("--timeout", help="Kill the sandboxed invocation after N seconds (exit 124)."),
    ] = None,
) -> None:
    """Drop into a sandboxed interactive shell.

    Defaults to --tty on (unlike `run`). Uses $SHELL or /bin/bash.
    """
    _refuse_if_nested()
    if timeout is not None and timeout <= 0:
        raise _fail("--timeout must be positive")
    shell_cmd = os.environ.get("SHELL", "/bin/bash")
    cwd = Path.cwd()
    _require_bwrap()
    spec = _sandbox_spec(
        cwd,
        project_write=project_write,
        network=network,
        ssh_agent=ssh_agent,
        gpg_agent=gpg_agent,
        extra_ro=extra_ro or [],
        extra_rw=extra_rw or [],
        tty=tty,
    )
    bwrap_cmd = build_args(spec, os.environ, default_mask_paths(os.getuid()))
    args = _apply_timeout([*bwrap_cmd, shell_cmd], timeout)
    if show_command:
        typer.echo(" ".join(args))
        return
    os.execvp(args[0], args)
