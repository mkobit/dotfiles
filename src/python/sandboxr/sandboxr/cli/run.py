import dataclasses
import os
from pathlib import Path
from typing import Annotated

import typer

from sandboxr.backend.bwrap import build_args, default_mask_paths
from sandboxr.cli._common import (
    _apply_timeout,
    _fail,
    _log_invocation,
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


@dataclasses.dataclass(frozen=True)
class _Profile:
    """One field per overridable flag; None means "this profile doesn't touch it"."""

    ssh_agent: bool | None = None
    gpg_agent: bool | None = None
    network: str | None = None
    gh_config: bool | None = None


# Named bundles of the flags below -- pure in-code sugar, not a config file.
# No resolution order, no env var, nothing to go read elsewhere: --profile
# just pre-sets fields on top of the granular flags' own defaults. A profile
# only overrides the fields it sets -- anything it leaves None still falls
# through to the granular flag, so e.g. `--profile push --network shared`
# already composes push with web access without needing two profiles. Add
# an entry here to add a profile; nothing else needs to change. gh_config
# triggers the read-only ~/.config/gh bind below, since it isn't a plain
# SandboxSpec field.
_PROFILES: dict[str, _Profile] = {
    "local-commit": _Profile(ssh_agent=False, gpg_agent=False),
    "push": _Profile(ssh_agent=True),
    "web-access": _Profile(network="shared"),
    "pr": _Profile(ssh_agent=True, gh_config=True),
}


def _resolve_profile(name: str | None) -> _Profile:
    if name is None:
        return _Profile()
    if name not in _PROFILES:
        raise _fail(f"unknown profile {name!r}; available: {', '.join(sorted(_PROFILES))}")
    return _PROFILES[name]


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
    profile: Annotated[
        str | None,
        typer.Option(
            "--profile",
            help=f"Named flag bundle. Composes with granular flags for any field it "
            f"doesn't set. Available: {', '.join(sorted(_PROFILES))}.",
        ),
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
    """Run a command in the sandbox: sandboxr run [FLAGS] -- COMMAND [ARGS...]"""
    _refuse_if_nested()
    if timeout is not None and timeout <= 0:
        raise _fail("--timeout must be positive")
    command = [arg for arg in ctx.args if arg != "--"]
    if not command:
        raise _fail("no command given; usage: sandboxr run [FLAGS] -- COMMAND [ARGS...]")
    cwd = Path.cwd()
    _require_bwrap()
    overrides = _resolve_profile(profile)
    ssh_agent = overrides.ssh_agent if overrides.ssh_agent is not None else ssh_agent
    gpg_agent = overrides.gpg_agent if overrides.gpg_agent is not None else gpg_agent
    network = overrides.network if overrides.network is not None else network
    resolved_extra_ro = list(extra_ro or [])
    if overrides.gh_config:
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
    adapted_cmd, tool_env = adapt_command(command, os.environ)
    if tool_env:
        spec = dataclasses.replace(spec, extra_env={**spec.extra_env, **tool_env})
    bwrap_cmd = build_args(spec, os.environ, default_mask_paths(os.getuid()))
    args = _apply_timeout([*bwrap_cmd, *adapted_cmd], timeout)
    _log_invocation(args, action="run")
    if show_command:
        typer.echo(" ".join(args))
        return
    os.execvp(args[0], args)
