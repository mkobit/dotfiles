import dataclasses
import os
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from sandboxr.backend.bwrap import build_args, default_mask_paths
from sandboxr.cli._common import (
    _echo_command,
    _refuse_if_nested,
    _require_bwrap,
    _sandbox_spec,
)
from sandboxr.sandbox.spec import SandboxSpec

app = typer.Typer()

PROBE_SCRIPT = r"""
set -u
fails=0
pass() { printf 'PASS: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1"; fails=$((fails+1)); }
hidden() { if [ -e "$2" ]; then fail "$1 visible at $2"; else pass "$1 hidden"; fi; }
hidden "ssh keys" "$HOME/.ssh"
hidden "gpg keys" "$HOME/.gnupg"
hidden "gh credentials" "$HOME/.config/gh"
hidden "ai-policy token store" "$HOME/.local/state/ai-policy"
command -v git >/dev/null 2>&1 && pass "git on PATH" || fail "git missing"
command -v rg >/dev/null 2>&1 && pass "rg on PATH" || fail "rg missing"
if [ "$(git config --global commit.gpgsign 2>/dev/null)" = "false" ]; then
  pass "commit signing disabled"
else
  fail "commit signing not disabled"
fi
if touch /agent-sandbox-probe 2>/dev/null; then
  rm -f /agent-sandbox-probe
  fail "root filesystem writable"
else
  pass "root filesystem read-only"
fi
probe_file="$PROBE_PROJECT/.agent-sandbox-probe.$$"
if touch "$probe_file" 2>/dev/null; then rm -f "$probe_file"; writable=1; else writable=0; fi
if [ "$writable" = "$PROBE_PROJECT_WRITE" ]; then
  pass "project write=$writable as expected"
else
  fail "project write=$writable expected=$PROBE_PROJECT_WRITE"
fi
if [ "$PROBE_EXPECT_SSH_AGENT" = "1" ]; then
  if [ -n "${SSH_AUTH_SOCK:-}" ] && [ -S "$SSH_AUTH_SOCK" ]; then
    pass "SSH agent socket forwarded"
  else
    fail "SSH agent socket missing or not a socket"
  fi
fi
if command -v gh >/dev/null 2>&1; then
  if [ "$PROBE_EXPECT_GH" = "1" ]; then
    if gh auth status >/dev/null 2>&1; then
      pass "gh authenticated via injected token"
    else
      fail "gh token injected but unauthenticated"
    fi
  else
    if gh auth status >/dev/null 2>&1; then
      fail "gh authenticated without injected token"
    else
      pass "gh unauthenticated"
    fi
  fi
fi
if command -v curl >/dev/null 2>&1; then
  if [ "$PROBE_NETWORK" = "none" ]; then
    if curl -fsS -m 2 "https://api.github.com/zen" >/dev/null 2>&1; then
      fail "network reachable on air-gapped profile"
    else
      pass "network unreachable (air-gapped)"
    fi
  else
    ollama_url="${OLLAMA_HOST:-localhost:11434}"
    case "$ollama_url" in http://*|https://*) ;; *) ollama_url="http://$ollama_url" ;; esac
    if curl -fsS -m 2 "${ollama_url}/api/version" >/dev/null 2>&1; then
      pass "ollama reachable"
    else
      printf 'WARN: %s\n' "ollama not reachable"
    fi
  fi
fi
printf 'failures: %d\n' "$fails"
exit "$fails"
"""


def _probe_env(spec: SandboxSpec) -> dict[str, str]:
    return {
        "PROBE_PROJECT": str(spec.project_root),
        "PROBE_PROJECT_WRITE": "1" if spec.project_write else "0",
        "PROBE_EXPECT_GH": "1" if "GH_TOKEN" in spec.extra_env else "0",
        "PROBE_EXPECT_SSH_AGENT": "1" if spec.ssh_agent_sock is not None else "0",
        "PROBE_NETWORK": spec.network,
    }


@app.command()
def doctor(
    project_write: Annotated[bool, typer.Option("--project-write/--no-project-write")] = True,
    network: Annotated[
        str,
        typer.Option("--network", help="Network mode: shared|none."),
    ] = "shared",
    ssh_agent: Annotated[bool, typer.Option("--ssh-agent/--no-ssh-agent")] = True,
    gpg_agent: Annotated[bool, typer.Option("--gpg-agent/--no-gpg-agent")] = False,
) -> None:
    """Verify sandbox guarantees by probing from inside it."""
    _refuse_if_nested()
    cwd = Path.cwd()
    _require_bwrap()
    spec = _sandbox_spec(
        cwd,
        project_write=project_write,
        network=network,
        ssh_agent=ssh_agent,
        gpg_agent=gpg_agent,
        tty=False,
    )
    spec = dataclasses.replace(spec, extra_env={**spec.extra_env, **_probe_env(spec)})
    bwrap_cmd = build_args(spec, os.environ, default_mask_paths(os.getuid()))
    _echo_command(bwrap_cmd)
    args = [*bwrap_cmd, "bash", "-c", PROBE_SCRIPT]
    result = subprocess.run(args, check=False)
    if result.returncode == 0:
        typer.secho("sandboxr doctor: all probes passed", fg=typer.colors.GREEN)
    raise typer.Exit(result.returncode)
