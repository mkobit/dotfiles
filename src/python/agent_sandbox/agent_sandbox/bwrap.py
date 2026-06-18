"""bwrap invocation builder.

Pure argument construction so the bind table is unit-testable. Strategy:
read-only OS, tmpfs over the whole home (default-deny for credentials and
personal state), then explicit re-binds for the toolchain and agent state.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

ENV_PASSTHROUGH = ("TERM", "LANG", "LC_ALL", "COLORTERM", "OLLAMA_HOST")

# Read-only toolchain and config mounts re-exposed under the tmpfs home.
# .local/state/mise carries mise's trust state for project-local mise.toml
# files; without it, any mise shim invoked inside the sandbox from a
# directory that has a local mise.toml (like this repo) errors on trust.
RO_HOME_PATHS = (
    ".local/bin",
    ".local/share/mise",
    ".local/state/mise",
    ".config/mise",
    ".dotfiles",
    ".config/ai-policy",
    ".local/share/ai",
)

# Agent state and OAuth stores: the agents' own credentials are the one secret
# class that must be present for the tools to run at all.
# Exact agy state dir is uncertain (binary uses XDG_CONFIG_HOME); we bind both
# common candidates so OAuth state survives across runs regardless of which
# one ends up being canonical.
RW_HOME_PATHS = (
    ".claude",
    ".claude.json",
    ".gemini",
    ".antigravity",
    ".config/antigravity-cli",
    ".config/opencode",
    ".local/share/opencode",
)

# Dedicated cache mounted at ~/.cache. Never share the host cache: a poisoned
# cache would cross the sandbox boundary when the human later builds on host.
CACHE_REL = ".local/share/agent-sandbox/cache"


@dataclass(frozen=True)
class SandboxSpec:
    home: Path
    project_root: Path
    project_write: bool
    profile_name: str
    cwd: Path
    git_common_dir: Path | None = None
    extra_env: dict[str, str] = field(default_factory=dict)
    tty: bool = False
    # "shared" reuses the host netns; "none" adds --unshare-net for an
    # air-gapped sandbox (no model APIs, no exfiltration, no apt/npm/cargo).
    network: str = "shared"
    # Profile-supplied paths under $HOME to expose rw / mask. See
    # config.Profile.home_rw / home_mask for the schema rationale.
    home_rw: tuple[str, ...] = ()
    home_mask: tuple[str, ...] = ()


def default_mask_paths(uid: int) -> tuple[str, ...]:
    # /mnt masks Windows drives on WSL; /run/user/<uid> masks gpg/ssh agent sockets.
    candidates = ("/mnt", f"/run/user/{uid}")
    return tuple(path for path in candidates if Path(path).is_dir())


def build_args(spec: SandboxSpec, environ: Mapping[str, str], mask_paths: Sequence[str] = ()) -> list[str]:
    home = spec.home
    args: list[str] = [
        "bwrap",
        "--die-with-parent",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--unshare-cgroup-try",
    ]
    if not spec.tty:
        # Prevents TIOCSTI input injection into the host terminal.
        args.append("--new-session")
    if spec.network == "none":
        args.append("--unshare-net")
    # /tmp here is the bwrap mount target for a fresh tmpfs, not insecure temp use.
    args += ["--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp"]  # noqa: S108
    for path in mask_paths:
        args += ["--tmpfs", path]
    args += ["--tmpfs", str(home)]
    for rel in RO_HOME_PATHS:
        path = home / rel
        if path.exists():
            args += ["--ro-bind", str(path), str(path)]
    for rel in RW_HOME_PATHS:
        path = home / rel
        if path.exists():
            args += ["--bind", str(path), str(path)]
    args += ["--bind", str(home / CACHE_REL), str(home / ".cache")]
    # Profile-supplied broad rw exposes (e.g. .config for the chezmoi profile).
    # Run before home_mask so credential subdirs are tmpfs-masked on top.
    for rel in spec.home_rw:
        path = home / rel
        if path.exists():
            args += ["--bind", str(path), str(path)]
    for rel in spec.home_mask:
        args += ["--tmpfs", str(home / rel)]
    project_bind = "--bind" if spec.project_write else "--ro-bind"
    args += [project_bind, str(spec.project_root), str(spec.project_root)]
    if spec.git_common_dir is not None:
        # Linked worktrees write objects and refs into the main checkout's .git.
        args += [project_bind, str(spec.git_common_dir), str(spec.git_common_dir)]
    args += ["--clearenv", "--setenv", "HOME", str(home)]
    args += ["--setenv", "PATH", environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")]
    for key in ENV_PASSTHROUGH:
        value = environ.get(key)
        if value is not None:
            args += ["--setenv", key, value]
    env = {
        "AGENT_RUN_PROFILE": spec.profile_name,
        # Marker for nesting detection: agent-run refuses to start when it
        # sees this set, since it means we're already inside a sandbox.
        "AGENT_RUN_IN_SANDBOX": "1",
        "GIT_CONFIG_GLOBAL": str(home / ".config/ai-policy/git/sandbox.gitconfig"),
        **spec.extra_env,
    }
    for key in sorted(env):
        args += ["--setenv", key, env[key]]
    args += ["--chdir", str(spec.cwd)]
    return args
