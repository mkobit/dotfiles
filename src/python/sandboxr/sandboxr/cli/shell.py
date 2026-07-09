import os
from pathlib import Path
from typing import Annotated

import typer

from sandboxr.backend.bwrap import BwrapBackend, default_mask_paths
from sandboxr.cli._common import (
    _apply_timeout,
    _fail,
    _refuse_if_nested,
    _require_bwrap,
    _resolve,
    _sandbox_spec,
)
from sandboxr.profile.loader import merge_cli_overrides

app = typer.Typer()

_CTX = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
    "allow_interspersed_args": False,
}


@app.command(context_settings=_CTX)
def shell(
    profile: Annotated[str | None, typer.Option("--profile", help="Named sandbox profile.")] = None,
    tty: Annotated[
        bool,
        typer.Option("--tty/--no-tty", "-t", help="Allocate a pseudo-TTY."),
    ] = True,
    show_command: Annotated[
        bool,
        typer.Option("--show-command", help="Print bwrap invocation instead of running."),
    ] = False,
    project_write: Annotated[
        bool | None,
        typer.Option("--project-write/--no-project-write"),
    ] = None,
    network: Annotated[
        str | None,
        typer.Option("--network", help="Network mode: shared|none."),
    ] = None,
    ssh_agent: Annotated[
        bool | None,
        typer.Option("--ssh-agent/--no-ssh-agent", help="Forward host SSH agent socket."),
    ] = None,
    gpg_agent: Annotated[
        bool | None,
        typer.Option("--gpg-agent/--no-gpg-agent", help="Forward host GPG agent socket."),
    ] = None,
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

    Examples:
      sandboxr shell                           # sandboxed bash, default profile
      sandboxr shell --profile untrusted       # untrusted profile
      sandboxr shell --ssh-agent               # with host SSH agent forwarded
      sandboxr shell --ro ~/.npmrc             # expose ~/.npmrc read-only
    """
    _refuse_if_nested()
    if timeout is not None and timeout <= 0:
        raise _fail("--timeout must be positive")
    shell_cmd = os.environ.get("SHELL", "/bin/bash")
    cwd = Path.cwd()
    _, active, backend = _resolve(profile, cwd)
    active = merge_cli_overrides(
        active,
        project_write=project_write,
        network=network,
        ssh_agent=ssh_agent,
        gpg_agent=gpg_agent,
        extra_ro=extra_ro or [],
        extra_rw=extra_rw or [],
        timeout_seconds=timeout,
    )
    if isinstance(backend, BwrapBackend):
        _require_bwrap()
    spec = _sandbox_spec(active, cwd, tty=tty)
    args = _apply_timeout(
        [*backend.build_args(spec, os.environ, default_mask_paths(os.getuid())), shell_cmd],
        active.timeout_seconds,
    )
    if show_command:
        typer.echo(" ".join(args))
        return
    os.execvp(args[0], args)
