import dataclasses
import os
from pathlib import Path
from typing import Annotated

import typer

from sandboxr.backend.bwrap import build_args, default_mask_paths
from sandboxr.cli._common import (
    _apply_timeout,
    _echo_command,
    _fail,
    _refuse_if_nested,
    _require_bwrap,
    _sandbox_spec,
)
from sandboxr.sandbox.tool import adapt_command

_CTX = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
    "allow_interspersed_args": False,
}

app = typer.Typer()


@app.command(context_settings=_CTX)
def run(
    ctx: typer.Context,
    tty: Annotated[
        bool,
        typer.Option(
            "--tty/--no-tty",
            "-t",
            help="Allocate a pseudo-TTY (weakens isolation: enables TIOCSTI injection).",
        ),
    ] = False,
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
    skip_permissions: Annotated[
        bool,
        typer.Option(
            "--skip-permissions/--no-skip-permissions",
            help="Bypass the tool's own permission prompts (default). Disable to keep them "
            "active — e.g. staged approval on git push/gh pr create/merge — while still "
            "sandboxed.",
        ),
    ] = True,
    local_commit: Annotated[
        bool | None,
        typer.Option(
            "--local-commit/--no-local-commit",
            help="Shorthand: no push/sign capability at all "
            "(forces --no-ssh-agent --no-gpg-agent).",
        ),
    ] = None,
    web_access: Annotated[
        bool | None,
        typer.Option("--web-access/--no-web-access", help="Shorthand for --network shared/none."),
    ] = None,
    push: Annotated[
        bool | None,
        typer.Option("--push/--no-push", help="Shorthand for --ssh-agent/--no-ssh-agent."),
    ] = None,
    pr: Annotated[
        bool,
        typer.Option(
            "--pr/--no-pr",
            help="Push capability plus read-only access to your real gh credentials "
            "(~/.config/gh), so `gh pr create` works. Not a scoped credential — the agent "
            "gets whatever access your own `gh auth login` session has.",
        ),
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
    """Run a command in the sandbox: sandboxr run [FLAGS] -- COMMAND [ARGS...]"""
    _refuse_if_nested()
    if timeout is not None and timeout <= 0:
        raise _fail("--timeout must be positive")
    command = [arg for arg in ctx.args if arg != "--"]
    if not command:
        raise _fail("no command given; usage: sandboxr run [FLAGS] -- COMMAND [ARGS...]")
    cwd = Path.cwd()
    _require_bwrap()
    if local_commit:
        ssh_agent = False
        gpg_agent = False
    if push is not None:
        ssh_agent = push
    if pr:
        ssh_agent = True
    if web_access is not None:
        network = "shared" if web_access else "none"
    resolved_extra_ro = list(extra_ro or [])
    if pr:
        # Real gh session, not a scoped credential: no short-lived or
        # per-usage token issuance exists yet. Read-only only protects the
        # file from tampering inside the sandbox -- it does not limit what
        # the token itself can do once `gh` reads it.
        resolved_extra_ro.append(str(Path.home() / ".config" / "gh"))
    spec = _sandbox_spec(
        cwd,
        project_write=project_write,
        network=network,
        ssh_agent=ssh_agent,
        gpg_agent=gpg_agent,
        extra_ro=resolved_extra_ro,
        extra_rw=extra_rw or [],
        tty=tty,
    )
    adapted_cmd, tool_env = adapt_command(command, os.environ, skip_permissions=skip_permissions)
    if tool_env:
        spec = dataclasses.replace(spec, extra_env={**spec.extra_env, **tool_env})
    bwrap_cmd = build_args(spec, os.environ, default_mask_paths(os.getuid()))
    args = _apply_timeout([*bwrap_cmd, *adapted_cmd], timeout)
    _echo_command(args)
    if show_command:
        typer.echo(" ".join(args))
        return
    os.execvp(args[0], args)
