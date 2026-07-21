"""srt (@anthropic-ai/sandbox-runtime) invocation builder.

Pure settings/argument construction, mirroring backend/bwrap.py's shape.
srt is the vendor enforcement runtime; this module only compiles a
SandboxSpec into srt's settings JSON and the srt invocation — no
enforcement logic lives here.
"""

import json
import shlex
import shutil
import subprocess
import time
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from sandboxr.backend.bwrap import (
    CACHE_REL,
    ENV_PASSTHROUGH,
    RO_HOME_PATHS,
    RW_HOME_PATHS,
    wsl_runtime_binds,
)
from sandboxr.sandbox.spec import SandboxSpec

# srt is installed as a mise global tool (no registry shorthand exists for
# it, so the tool key is the fully qualified npm backend spec — see
# .chezmoidata/bin/mise.toml). The install directory lives under
# ~/.local/share/mise/installs/, which RO_HOME_PATHS already exposes
# read-only, so no dedicated vendor path is needed here — just resolve it
# at runtime via `mise where` rather than hardcoding mise's install layout.
MISE_NPM_SPEC = "npm:@anthropic-ai/sandbox-runtime"
CLI_JS_RELATIVE_TO_INSTALL = Path("node_modules/@anthropic-ai/sandbox-runtime/dist/cli.js")

SETTINGS_DIR_REL = ".local/share/sandboxr/srt-settings"
SETTINGS_MAX_AGE_SECONDS = 3600

# srt backgrounds its own proxy-bridge listeners and execs the user command
# with no readiness sync (confirmed race: 5/5 failures with no delay vs.
# 5/5 successes with a 150ms delay). Grace sleep before exec, scoped to
# this backend only — not a fix to srt's own vendored code.
_GRACE_SLEEP_SECONDS = "0.2"


def build_settings(spec: SandboxSpec, mask_paths: Sequence[str] = ()) -> dict[str, Any]:
    if spec.network == "shared":
        msg = (
            "srt backend does not support network='shared' (no expressible "
            "'allow all' egress in srt's schema); use network='allowlist' "
            "or 'none', or select the bwrap backend"
        )
        raise ValueError(msg)
    home = spec.home
    # Agent sockets live under /run/user/<uid>, masked (denyRead) via
    # mask_paths on the same default_mask_paths() bwrap.py also uses -- must
    # be re-exposed here or the sockets become unreachable. bwrap's --bind
    # grants read+write, so both sockets go into allow_read and allow_write
    # to match; ~/.gnupg mirrors bwrap's --ro-bind (read-only keyring lookup,
    # the private key stays on the host).
    ssh_sock = (
        spec.ssh_agent_sock
        if spec.ssh_agent_sock is not None and spec.ssh_agent_sock.exists()
        else None
    )
    gpg_sock = (
        spec.gpg_agent_sock
        if spec.gpg_agent_sock is not None and spec.gpg_agent_sock.exists()
        else None
    )
    gnupg_dir = home / ".gnupg"
    deny_read = [str(home), *mask_paths, *(str(home / rel) for rel in spec.home_mask)]
    allow_read = [
        *(str(home / rel) for rel in RO_HOME_PATHS if (home / rel).exists()),
        # RW_HOME_PATHS mirrors bwrap's --bind, which grants read+write.
        *(str(home / rel) for rel in RW_HOME_PATHS if (home / rel).exists()),
        # /etc/resolv.conf is a symlink into /mnt/wsl/resolv.conf on WSL2;
        # mask_paths denyReads /mnt, so without this DNS resolution inside
        # the sandbox fails outright (confirmed empirically).
        *wsl_runtime_binds(),
        *(str(p) for p in spec.extra_ro),
        *(str(home / rel) for rel in spec.home_rw if (home / rel).exists()),
        str(spec.project_root),
        *([str(spec.git_common_dir)] if spec.git_common_dir is not None else []),
        *([str(ssh_sock)] if ssh_sock is not None else []),
        *([str(gpg_sock)] if gpg_sock is not None else []),
        *([str(gnupg_dir)] if gpg_sock is not None and gnupg_dir.exists() else []),
    ]
    allow_write = [
        *(str(home / rel) for rel in RW_HOME_PATHS if (home / rel).exists()),
        *(str(home / rel) for rel in spec.home_rw if (home / rel).exists()),
        *(str(p) for p in spec.extra_rw),
        str(home / CACHE_REL),
        *([str(spec.project_root)] if spec.project_write else []),
        *(
            [str(spec.git_common_dir)]
            if spec.project_write and spec.git_common_dir is not None
            else []
        ),
        *([str(ssh_sock)] if ssh_sock is not None else []),
        *([str(gpg_sock)] if gpg_sock is not None else []),
    ]
    deny_write = [str(home / rel) for rel in spec.home_mask]
    # Known limitation (verified live, 2026-07-09): on Linux, srt's
    # allowUnixSockets is a documented no-op -- its own linux-sandbox-utils.d.ts
    # states "allowUnixSockets configuration is not path-based on Linux (unlike
    # macOS) because seccomp-bpf cannot inspect user-space memory to read
    # socket paths". The compiled JS confirms: unless allowAllUnixSockets is
    # true, a blanket seccomp filter blocks every AF_UNIX socket() call
    # (reproduced directly: a bare `socket.socket(AF_UNIX, SOCK_STREAM)` raises
    # PermissionError before any connect() or path is involved). So even with
    # the allowRead/allowWrite re-expose above, ssh_agent/gpg_agent forwarding
    # does not actually work under the srt backend on Linux today -- only
    # allowAllUnixSockets:true (an unscoped grant, not specific to these
    # sockets) would make it connect, and that tradeoff hasn't been made.
    allow_unix_sockets = [
        str(sock) for sock in (spec.ssh_agent_sock, spec.gpg_agent_sock) if sock is not None
    ]
    allowed_domains = list(spec.allowed_domains) if spec.network == "allowlist" else []
    denied_domains = [] if spec.network == "allowlist" else ["*"]
    return {
        "network": {
            "allowedDomains": allowed_domains,
            "deniedDomains": denied_domains,
            **({"allowUnixSockets": allow_unix_sockets} if allow_unix_sockets else {}),
        },
        "filesystem": {
            "denyRead": deny_read,
            "allowRead": allow_read,
            "allowWrite": allow_write,
            "denyWrite": deny_write,
        },
    }


def _cleanup_stale_settings(settings_dir: Path) -> None:
    cutoff = time.time() - SETTINGS_MAX_AGE_SECONDS
    for entry in settings_dir.glob("*.json"):
        try:
            if entry.stat().st_mtime < cutoff:
                entry.unlink()
        except OSError:
            pass


def write_settings(settings: dict[str, Any], home: Path) -> Path:
    settings_dir = home / SETTINGS_DIR_REL
    settings_dir.mkdir(parents=True, exist_ok=True)
    _cleanup_stale_settings(settings_dir)
    path = settings_dir / f"{uuid.uuid4()}.json"
    path.write_text(json.dumps(settings))
    path.chmod(0o600)
    return path


def _mise_install_dir(mise_path: str) -> Path | None:
    try:
        result = subprocess.run(
            [mise_path, "where", MISE_NPM_SPEC],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):  # fmt: skip
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return Path(result.stdout.strip())


def resolve_cli_js(mise_path: str) -> Path | None:
    install_dir = _mise_install_dir(mise_path)
    if install_dir is None:
        return None
    cli_js = install_dir / CLI_JS_RELATIVE_TO_INSTALL
    return cli_js if cli_js.exists() else None


def _build_env(spec: SandboxSpec, environ: Mapping[str, str]) -> dict[str, str]:
    # Neither srt's settings.json nor its own internal bwrap wrapping clears
    # the environment (confirmed via debug capture: srt's bwrap invocation
    # has no --clearenv, only --setenv additions on top of whatever it
    # inherits) — sandboxr must curate it itself here, mirroring bwrap.py's
    # _build_env_args, or the full host environment leaks into the sandbox.
    home = spec.home
    env: dict[str, str] = {
        "HOME": str(home),
        "PATH": environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "AGENT_RUN_PROFILE": spec.profile_name,
        "AGENT_RUN_IN_SANDBOX": "1",
        "GIT_CONFIG_GLOBAL": str(home / ".config/ai-policy/git/sandbox.gitconfig"),
        **spec.extra_env,
    }
    for key in ENV_PASSTHROUGH:
        value = environ.get(key)
        if value is not None:
            env[key] = value
    if spec.ssh_agent_sock is not None and spec.ssh_agent_sock.exists():
        env["SSH_AUTH_SOCK"] = str(spec.ssh_agent_sock)
    if spec.gpg_agent_sock is not None and spec.gpg_agent_sock.exists():
        env["GNUPGHOME"] = str(home / ".gnupg")
    return env


def build_args(
    spec: SandboxSpec,
    environ: Mapping[str, str],
    mask_paths: Sequence[str] = (),
) -> list[str]:
    node_path = shutil.which("node", path=environ.get("PATH"))
    if node_path is None:
        msg = "node not found on PATH; required for the srt backend"
        raise RuntimeError(msg)
    mise_path = shutil.which("mise", path=environ.get("PATH"))
    if mise_path is None:
        msg = "mise not found on PATH; required to locate the srt install"
        raise RuntimeError(msg)
    cli_js = resolve_cli_js(mise_path)
    if cli_js is None:
        msg = f"srt not provisioned via mise ({MISE_NPM_SPEC}); run `chezmoi apply`"
        raise RuntimeError(msg)
    settings = build_settings(spec, mask_paths)
    settings_path = write_settings(settings, spec.home)
    env = _build_env(spec, environ)
    env_prefix = ["env", "-i", *(f"{key}={env[key]}" for key in sorted(env))]
    return [*env_prefix, node_path, str(cli_js), "-s", str(settings_path)]


def wrap_command(cmd: Sequence[str]) -> Sequence[str]:
    # srt silently drops every positional arg that follows a `bash -c
    # <script>` command in its spawn -- confirmed empirically (0.0.63):
    # `bash -c 'echo got:$0' myarg0` execs with $0 defaulting to the resolved
    # bash binary path, not "myarg0" -- so a trailing "$@"-style wrapper
    # (`bash -c '...; exec "$@"' -- <cmd>`) always execs against an empty
    # argument list. The command must be fully embedded in the script string
    # itself, with zero args trailing `-c`, to reach the sandboxed process.
    script = f"sleep {_GRACE_SLEEP_SECONDS}; exec {shlex.join(cmd)}"
    return ["bash", "-c", script]


class SrtBackend:
    name = "srt"

    def build_args(
        self,
        spec: SandboxSpec,
        environ: Mapping[str, str],
        mask_paths: Sequence[str] = (),
    ) -> list[str]:
        return build_args(spec, environ, mask_paths)

    def wrap_command(self, cmd: Sequence[str]) -> Sequence[str]:
        return wrap_command(cmd)
