"""agent-run: launch AI agent CLIs inside an outer sandbox.

The tool-native permission system is the UX boundary in HITL — run the CLI
directly for that. This wrapper is for no-human-in-the-loop runs: outer
bwrap (Linux/WSL) or sandbox-exec (macOS, future) + credential absence is
the actual security boundary. Each adapter flips the tool's bypass flag
because the outer sandbox enforces — nothing inside it is trusted.
"""

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import typer

from agent_sandbox.backend import BwrapBackend, SandboxBackend, select_backend
from agent_sandbox.bwrap import CACHE_REL, SandboxSpec, default_mask_paths
from agent_sandbox.config import (
    ConfigError,
    Profile,
    SandboxConfig,
    load_config,
    resolve_profile,
)

app = typer.Typer(help="Run AI agent CLIs in an outer sandbox per ~/.config/ai-policy/sandbox.json.")

TOKEN_PATH = Path.home() / ".local" / "state" / "ai-policy" / "tokens" / "readonly.token"
CLAUDE_SETTINGS = Path.home() / ".config" / "ai-policy" / "claude" / "autonomous-settings.json"
AGY_SETTINGS = Path.home() / ".config" / "ai-policy" / "agy" / "autonomous-settings.json"
OPENCODE_CONFIG = Path.home() / ".config" / "ai-policy" / "opencode" / "autonomous.json"

_RUN_CONTEXT_SETTINGS = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
    "allow_interspersed_args": False,
}


def _fail(message: str) -> typer.Exit:
    typer.secho(f"agent-run: {message}", fg=typer.colors.RED, err=True)
    return typer.Exit(1)


def _git(cwd: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except OSError, subprocess.SubprocessError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _project_root(cwd: Path) -> Path:
    top = _git(cwd, "rev-parse", "--show-toplevel")
    return Path(top) if top else cwd


def _git_common_dir(cwd: Path, project_root: Path) -> Path | None:
    common = _git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not common:
        return None
    common_path = Path(common)
    if common_path == project_root or project_root in common_path.parents:
        return None
    return common_path


def _readonly_token() -> str | None:
    try:
        mode = TOKEN_PATH.stat().st_mode
    except OSError:
        return None
    if stat.S_IMODE(mode) & 0o077:
        typer.secho(
            f"agent-run: ignoring {TOKEN_PATH}: permissions too open (chmod 600 to use)",
            fg=typer.colors.YELLOW,
            err=True,
        )
        return None
    token = TOKEN_PATH.read_text().strip()
    return token or None


def _adapt_command(command: list[str], extra_env: dict[str, str]) -> list[str]:
    """Engage each tool's no-prompt mode. The outer sandbox is the boundary;
    the tool's own approvals would only add friction now.
    """
    tool = Path(command[0]).name
    if tool == "claude":
        adapted = list(command)
        if "--settings" not in adapted and CLAUDE_SETTINGS.exists():
            adapted += ["--settings", str(CLAUDE_SETTINGS)]
        if "--dangerously-skip-permissions" not in adapted:
            adapted.append("--dangerously-skip-permissions")
        return adapted
    if tool == "agy":
        adapted = list(command)
        if "--settings" not in adapted and AGY_SETTINGS.exists():
            adapted += ["--settings", str(AGY_SETTINGS)]
        if "--dangerously-skip-permissions" not in adapted:
            adapted.append("--dangerously-skip-permissions")
        # Do NOT pass --sandbox: combining it with --dangerously-skip-permissions
        # auto-approves bypassing the sandbox itself (antigravity-cli #36).
        return adapted
    if tool == "opencode":
        extra_env.setdefault("OPENCODE_CONFIG", str(OPENCODE_CONFIG))
        # Deliberately do NOT set OPENCODE_HARDENED_MODE=1: that engages
        # opencode's own bwrap inside our bwrap and creates nested namespaces.
    return command


def _resolve(profile_flag: str | None, cwd: Path) -> tuple[SandboxConfig, Profile, SandboxBackend]:
    try:
        config = load_config()
        profile = resolve_profile(config, profile_flag, os.environ.get("AGENT_RUN_PROFILE"))
        backend = select_backend(profile.backend, platform=sys.platform)
    except (ConfigError, ValueError) as exc:
        raise _fail(str(exc)) from exc
    return config, profile, backend


def _sandbox_spec(profile: Profile, cwd: Path, keep_tty: bool) -> SandboxSpec:
    home = Path.home()
    project_root = _project_root(cwd)
    if project_root == home or project_root in home.parents:
        raise _fail(
            f"refusing to sandbox {project_root}: it contains the whole home directory; run from a project checkout"
        )
    (home / CACHE_REL).mkdir(parents=True, exist_ok=True)
    extra_env: dict[str, str] = {}
    token = _readonly_token()
    if token:
        extra_env["GH_TOKEN"] = token
    return SandboxSpec(
        home=home,
        project_root=project_root,
        project_write=profile.project_write,
        profile_name=profile.name,
        cwd=cwd,
        git_common_dir=_git_common_dir(cwd, project_root),
        extra_env=extra_env,
        keep_tty=keep_tty,
    )


def _require_bwrap() -> None:
    if shutil.which("bwrap") is None:
        raise _fail("bwrap not found; it is installed by the run_once_install-sandbox-deps chezmoi script")


@app.command(context_settings=_RUN_CONTEXT_SETTINGS)
def run(
    ctx: typer.Context,
    profile: str | None = typer.Option(None, "--profile", help="Sandbox profile (default: configured default)."),
    keep_tty: bool = typer.Option(
        False,
        "--keep-tty",
        help="Keep the controlling terminal for interactive TUIs (weakens isolation: TIOCSTI injection).",
    ),
    show_command: bool = typer.Option(False, "--show-command", help="Print the sandbox invocation instead of running."),
) -> None:
    """Run a command in the sandbox: agent-run run --profile autonomous -- claude -p 'fix tests'."""
    command = [arg for arg in ctx.args if arg != "--"]
    if not command:
        raise _fail("no command given; usage: agent-run run [--profile NAME] -- COMMAND [ARGS...]")
    cwd = Path.cwd()
    _, active, backend = _resolve(profile, cwd)
    if isinstance(backend, BwrapBackend):
        _require_bwrap()
    spec = _sandbox_spec(active, cwd, keep_tty)
    command = _adapt_command(command, spec.extra_env)
    args = [*backend.build_args(spec, os.environ, default_mask_paths(os.getuid())), *command]
    if show_command:
        typer.echo(" ".join(args))
        return
    os.execvp(args[0], args)  # noqa: S606


@app.command()
def doctor(
    profile: str = typer.Option("autonomous", "--profile", help="Profile to verify."),
) -> None:
    """Verify the sandbox guarantees by probing from inside it."""
    cwd = Path.cwd()
    _, active, backend = _resolve(profile, cwd)
    if isinstance(backend, BwrapBackend):
        _require_bwrap()
    spec = _sandbox_spec(active, cwd, keep_tty=False)
    spec.extra_env["PROBE_PROJECT"] = str(spec.project_root)
    spec.extra_env["PROBE_PROJECT_WRITE"] = "1" if spec.project_write else "0"
    spec.extra_env["PROBE_EXPECT_GH"] = "1" if "GH_TOKEN" in spec.extra_env else "0"
    args = [
        *backend.build_args(spec, os.environ, default_mask_paths(os.getuid())),
        "bash",
        "-c",
        PROBE_SCRIPT,
    ]
    result = subprocess.run(args, check=False)
    if result.returncode == 0:
        typer.secho("agent-run doctor: all probes passed", fg=typer.colors.GREEN)
    raise typer.Exit(result.returncode)


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
[ "$(git config --global commit.gpgsign 2>/dev/null)" = "false" ] && pass "commit signing disabled" || fail "commit signing not disabled"
if touch /agent-sandbox-probe 2>/dev/null; then rm -f /agent-sandbox-probe; fail "root filesystem writable"; else pass "root filesystem read-only"; fi
probe_file="$PROBE_PROJECT/.agent-sandbox-probe.$$"
if touch "$probe_file" 2>/dev/null; then rm -f "$probe_file"; writable=1; else writable=0; fi
if [ "$writable" = "$PROBE_PROJECT_WRITE" ]; then pass "project write=$writable as expected"; else fail "project write=$writable expected=$PROBE_PROJECT_WRITE"; fi
if command -v gh >/dev/null 2>&1; then
  if [ "$PROBE_EXPECT_GH" = "1" ]; then
    gh auth status >/dev/null 2>&1 && pass "gh authenticated via injected token" || fail "gh token injected but unauthenticated"
  else
    gh auth status >/dev/null 2>&1 && fail "gh authenticated without injected token" || pass "gh unauthenticated"
  fi
fi
if command -v curl >/dev/null 2>&1; then
  curl -fsS -m 2 "http://${OLLAMA_HOST:-localhost:11434}/api/version" >/dev/null 2>&1 && pass "ollama reachable" || printf 'WARN: %s\n' "ollama not reachable"
fi
printf 'failures: %d\n' "$fails"
exit "$fails"
"""


def main() -> None:
    app()


if __name__ == "__main__":
    sys.exit(main())
