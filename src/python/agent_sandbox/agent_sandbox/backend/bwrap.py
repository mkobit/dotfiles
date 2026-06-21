"""bwrap invocation builder.

Pure argument construction — the bind table is unit-testable without
running bwrap. Strategy: read-only OS root, tmpfs over the whole home
(default-deny for credentials and personal state), then explicit re-binds
for the toolchain and agent state.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path

from agent_sandbox.sandbox.spec import SandboxSpec

ENV_PASSTHROUGH = ("TERM", "LANG", "LC_ALL", "COLORTERM", "OLLAMA_HOST")

# Toolchain and config mounts re-exposed under the tmpfs home.
# .local/state/mise carries mise's trust state for project-local mise.toml
# files; without it, mise shims invoked from a directory with a local
# mise.toml error on trust checks.
RO_HOME_PATHS = (
    ".local/bin",
    ".local/share/mise",
    ".local/state/mise",
    ".config/mise",
    ".dotfiles",
    ".config/ai-policy",
    ".local/share/ai",
)

# Agent state and OAuth stores: the agents' own credentials must be present
# for the tools to function. Both common agy state dirs are bound so OAuth
# state survives regardless of which one ends up canonical.
RW_HOME_PATHS = (
    ".claude",
    ".claude.json",
    ".gemini",
    ".antigravity",
    ".config/antigravity-cli",
    ".config/opencode",
    ".local/share/opencode",
)

# Dedicated cache mounted at ~/.cache. Never share the host cache: a
# poisoned cache would cross the sandbox boundary on the next host build.
CACHE_REL = ".local/share/agent-sandbox/cache"


def default_mask_paths(uid: int) -> tuple[str, ...]:
    # /mnt masks Windows drives on WSL2.
    # /run/user/<uid> masks gpg/ssh agent sockets (re-exposed selectively).
    candidates = ("/mnt", f"/run/user/{uid}")
    return tuple(path for path in candidates if Path(path).is_dir())


def build_args(
    spec: SandboxSpec,
    environ: Mapping[str, str],
    mask_paths: Sequence[str] = (),
) -> list[str]:
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
        args.append("--new-session")
    if spec.network == "none":
        args.append("--unshare-net")
    # /tmp is a bwrap tmpfs mount target, not a temp-file use.
    args += ["--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp"]
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
    # SSH agent: bind the socket after the /run/user tmpfs mask so it
    # overrides and becomes reachable. Keys never enter the sandbox; only
    # signing operations are forwarded to the host agent.
    if spec.ssh_agent_sock is not None and spec.ssh_agent_sock.exists():
        args += ["--bind", str(spec.ssh_agent_sock), str(spec.ssh_agent_sock)]
    # GPG agent: bind ~/.gnupg ro (keyring for key lookup) then the agent
    # socket rw (for signing). The private key stays on the host.
    if spec.gpg_agent_sock is not None and spec.gpg_agent_sock.exists():
        gnupg_dir = home / ".gnupg"
        if gnupg_dir.exists():
            args += ["--ro-bind", str(gnupg_dir), str(gnupg_dir)]
        args += ["--bind", str(spec.gpg_agent_sock), str(spec.gpg_agent_sock)]
    # Ad-hoc path binds from --ro / --rw flags or profile extra_ro/extra_rw.
    for path in spec.extra_ro:
        if path.exists():
            args += ["--ro-bind", str(path), str(path)]
    for path in spec.extra_rw:
        if path.exists():
            args += ["--bind", str(path), str(path)]
    args += ["--bind", str(home / CACHE_REL), str(home / ".cache")]
    project_bind = "--bind" if spec.project_write else "--ro-bind"
    args += [project_bind, str(spec.project_root), str(spec.project_root)]
    if spec.git_common_dir is not None:
        args += [project_bind, str(spec.git_common_dir), str(spec.git_common_dir)]
    args += ["--clearenv", "--setenv", "HOME", str(home)]
    args += ["--setenv", "PATH", environ.get("PATH", "/usr/local/bin:/usr/bin:/bin")]
    for key in ENV_PASSTHROUGH:
        value = environ.get(key)
        if value is not None:
            args += ["--setenv", key, value]
    env: dict[str, str] = {
        "AGENT_RUN_PROFILE": spec.profile_name,
        "AGENT_RUN_IN_SANDBOX": "1",
        "GIT_CONFIG_GLOBAL": str(home / ".config/ai-policy/git/sandbox.gitconfig"),
        **spec.extra_env,
    }
    if spec.ssh_agent_sock is not None and spec.ssh_agent_sock.exists():
        env["SSH_AUTH_SOCK"] = str(spec.ssh_agent_sock)
    if spec.gpg_agent_sock is not None and spec.gpg_agent_sock.exists():
        env["GNUPGHOME"] = str(home / ".gnupg")
    for key in sorted(env):
        args += ["--setenv", key, env[key]]
    args += ["--chdir", str(spec.cwd)]
    return args


class BwrapBackend:
    name = "bwrap"

    def build_args(
        self,
        spec: SandboxSpec,
        environ: Mapping[str, str],
        mask_paths: Sequence[str] = (),
    ) -> list[str]:
        return build_args(spec, environ, mask_paths)
