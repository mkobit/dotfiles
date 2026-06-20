"""Shared CLI helpers: spec building, socket resolution, guard checks."""

import os
import shutil
import stat
import subprocess
from pathlib import Path

import typer

from agent_sandbox.backend.bwrap import CACHE_REL
from agent_sandbox.backend.protocol import SandboxBackend, select_backend
from agent_sandbox.profile.loader import load_config, resolve_profile
from agent_sandbox.profile.schema import ConfigError, Profile, SandboxConfig
from agent_sandbox.sandbox.spec import SandboxSpec

TOKEN_PATH = Path.home() / ".local" / "state" / "ai-policy" / "tokens" / "readonly.token"


def _fail(message: str) -> typer.Exit:
    typer.secho(f"agent-run: {message}", fg=typer.colors.RED, err=True)
    return typer.Exit(1)


def _refuse_if_nested() -> None:
    if os.environ.get("AGENT_RUN_IN_SANDBOX") == "1":
        raise _fail(
            "refusing nested agent-run invocation: already inside a sandbox "
            "(AGENT_RUN_IN_SANDBOX=1). Exit the sandbox shell and rerun on the host."
        )


def _require_bwrap() -> None:
    if shutil.which("bwrap") is None:
        raise _fail(
            "bwrap not found; install via the run_once_install-sandbox-deps chezmoi script"
        )


def _git(cwd: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


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


def _ssh_agent_sock() -> Path | None:
    """Return the host SSH agent socket path, or None if unavailable."""
    sock = os.environ.get("SSH_AUTH_SOCK")
    if not sock:
        return None
    path = Path(sock)
    return path if path.exists() else None


def _gpg_agent_sock() -> Path | None:
    """Return the host GPG agent socket path via gpgconf, or None if unavailable."""
    try:
        result = subprocess.run(
            ["gpgconf", "--list-dirs", "agent-socket"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    path = Path(result.stdout.strip())
    return path if path.exists() else None


def _resolve(
    profile_flag: str | None, cwd: Path
) -> tuple[SandboxConfig, Profile, SandboxBackend]:
    import sys

    try:
        config = load_config()
        profile = resolve_profile(config, profile_flag, os.environ.get("AGENT_RUN_PROFILE"))
        backend = select_backend(profile.backend, platform=sys.platform)
    except (ConfigError, ValueError) as exc:
        raise _fail(str(exc)) from exc
    return config, profile, backend


def _sandbox_spec(profile: Profile, cwd: Path, *, tty: bool) -> SandboxSpec:
    home = Path.home()
    project_root = _project_root(cwd)
    if project_root == home or project_root in home.parents:
        raise _fail(
            f"refusing to sandbox {project_root}: it contains the whole home directory; "
            "run from a project checkout"
        )
    (home / CACHE_REL).mkdir(parents=True, exist_ok=True)
    extra_env: dict[str, str] = {}
    token = _readonly_token()
    if token:
        extra_env["GH_TOKEN"] = token
    ssh_sock = _ssh_agent_sock() if profile.ssh_agent else None
    gpg_sock = _gpg_agent_sock() if profile.gpg_agent else None
    return SandboxSpec(
        home=home,
        project_root=project_root,
        project_write=profile.project_write,
        profile_name=profile.name,
        cwd=cwd,
        git_common_dir=_git_common_dir(cwd, project_root),
        extra_env=extra_env,
        tty=tty,
        network=profile.network,
        ssh_agent_sock=ssh_sock,
        gpg_agent_sock=gpg_sock,
        extra_ro=tuple(Path(p).expanduser() for p in profile.extra_ro),
        extra_rw=tuple(Path(p).expanduser() for p in profile.extra_rw),
    )
