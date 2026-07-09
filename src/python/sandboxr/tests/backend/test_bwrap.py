from pathlib import Path
from unittest.mock import patch

import pytest

from sandboxr.backend.bwrap import CACHE_REL, BwrapBackend, build_args
from sandboxr.sandbox.spec import SandboxSpec


def bind_pairs(args: list[str], flag: str) -> list[tuple[str, str]]:
    return [(args[i + 1], args[i + 2]) for i, a in enumerate(args) if a == flag]


def setenv_map(args: list[str]) -> dict[str, str]:
    return {args[i + 1]: args[i + 2] for i, a in enumerate(args) if a == "--setenv"}


@pytest.fixture
def home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    for rel in (".local/bin", ".local/share/mise", ".claude", CACHE_REL):
        (home / rel).mkdir(parents=True)
    (home / ".claude.json").write_text("{}")
    return home


@pytest.fixture
def project(tmp_path: Path) -> Path:
    project = tmp_path / "home" / "projects" / "demo"
    project.mkdir(parents=True)
    return project


def spec_for(
    home: Path,
    project: Path,
    *,
    project_write: bool = True,
    profile_name: str = "autonomous",
    git_common_dir: Path | None = None,
    extra_env: dict[str, str] | None = None,
    tty: bool = False,
    network: str = "shared",
    ssh_agent_sock: Path | None = None,
    gpg_agent_sock: Path | None = None,
    extra_ro: tuple[Path, ...] = (),
    extra_rw: tuple[Path, ...] = (),
    home_rw: tuple[str, ...] = (),
    home_mask: tuple[str, ...] = (),
) -> SandboxSpec:
    return SandboxSpec(
        home=home,
        project_root=project,
        project_write=project_write,
        profile_name=profile_name,
        cwd=project,
        git_common_dir=git_common_dir,
        extra_env=extra_env or {},
        tty=tty,
        network=network,
        ssh_agent_sock=ssh_agent_sock,
        gpg_agent_sock=gpg_agent_sock,
        extra_ro=extra_ro,
        extra_rw=extra_rw,
        home_rw=home_rw,
        home_mask=home_mask,
    )


def test_home_is_tmpfs_with_explicit_rebinds(home: Path, project: Path) -> None:
    args = build_args(spec_for(home, project), {"PATH": "/usr/bin"})
    tmpfs_targets = [args[i + 1] for i, a in enumerate(args) if a == "--tmpfs"]
    assert str(home) in tmpfs_targets
    assert "/tmp" in tmpfs_targets
    ro = bind_pairs(args, "--ro-bind")
    assert (str(home / ".local/bin"), str(home / ".local/bin")) in ro
    assert (str(home / ".local/share/mise"), str(home / ".local/share/mise")) in ro
    assert all(".dotfiles" not in src for src, _ in ro)


def test_agent_state_bound_rw_and_credentials_never_bound(home: Path, project: Path) -> None:
    args = build_args(spec_for(home, project), {})
    rw = bind_pairs(args, "--bind")
    assert (str(home / ".claude"), str(home / ".claude")) in rw
    assert (str(home / ".claude.json"), str(home / ".claude.json")) in rw
    joined = " ".join(args)
    assert ".ssh" not in joined
    assert ".gnupg" not in joined
    assert ".config/gh" not in joined


def test_project_bind_mode_follows_profile(home: Path, project: Path) -> None:
    rw_args = build_args(spec_for(home, project, project_write=True), {})
    ro_args = build_args(spec_for(home, project, project_write=False), {})
    assert (str(project), str(project)) in bind_pairs(rw_args, "--bind")
    assert (str(project), str(project)) in bind_pairs(ro_args, "--ro-bind")
    assert (str(project), str(project)) not in bind_pairs(ro_args, "--bind")


def test_git_common_dir_bound_for_linked_worktrees(home: Path, project: Path) -> None:
    common = home / "projects" / "main-checkout" / ".git"
    common.mkdir(parents=True)
    args = build_args(spec_for(home, project, git_common_dir=common), {})
    assert (str(common), str(common)) in bind_pairs(args, "--bind")


def test_cache_is_dedicated_not_host_cache(home: Path, project: Path) -> None:
    args = build_args(spec_for(home, project), {})
    assert (str(home / CACHE_REL), str(home / ".cache")) in bind_pairs(args, "--bind")


def test_env_is_cleared_with_allowlist_only(home: Path, project: Path) -> None:
    environ = {
        "PATH": "/usr/bin",
        "TERM": "xterm",
        "SSH_AUTH_SOCK": "/run/ssh.sock",
        "GPG_TTY": "/dev/tty1",
        "GH_TOKEN": "host-secret",
        "OLLAMA_HOST": "localhost:11434",
    }
    args = build_args(spec_for(home, project), environ)
    assert "--clearenv" in args
    env = setenv_map(args)
    assert env["PATH"] == "/usr/bin"
    assert env["TERM"] == "xterm"
    assert env["OLLAMA_HOST"] == "localhost:11434"
    assert env["HOME"] == str(home)
    assert env["AGENT_RUN_PROFILE"] == "autonomous"
    assert env["AGENT_RUN_IN_SANDBOX"] == "1"
    assert env["GIT_CONFIG_GLOBAL"] == str(home / ".config/ai-policy/git/sandbox.gitconfig")
    assert "SSH_AUTH_SOCK" not in env
    assert "GPG_TTY" not in env
    assert "GH_TOKEN" not in env


def test_extra_env_injected(home: Path, project: Path) -> None:
    args = build_args(spec_for(home, project, extra_env={"GH_TOKEN": "scoped"}), {})
    assert setenv_map(args)["GH_TOKEN"] == "scoped"  # noqa: S105


def test_mask_paths_are_tmpfs(home: Path, project: Path) -> None:
    args = build_args(spec_for(home, project), {}, mask_paths=("/mnt", "/run/user/1000"))
    tmpfs_targets = [args[i + 1] for i, a in enumerate(args) if a == "--tmpfs"]
    assert "/mnt" in tmpfs_targets
    assert "/run/user/1000" in tmpfs_targets


def test_new_session_unless_tty(home: Path, project: Path) -> None:
    assert "--new-session" in build_args(spec_for(home, project), {})
    assert "--new-session" not in build_args(spec_for(home, project, tty=True), {})


def test_chdir_to_cwd(home: Path, project: Path) -> None:
    args = build_args(spec_for(home, project), {})
    idx = args.index("--chdir")
    assert args[idx + 1] == str(project)
    assert Path(args[idx + 1]).is_absolute()


def test_network_shared_does_not_unshare(home: Path, project: Path) -> None:
    assert "--unshare-net" not in build_args(spec_for(home, project, network="shared"), {})


def test_network_none_unshares_net(home: Path, project: Path) -> None:
    assert "--unshare-net" in build_args(spec_for(home, project, network="none"), {})


def test_ssh_agent_sock_bound_and_env_set(home: Path, project: Path, tmp_path: Path) -> None:
    sock = tmp_path / "ssh-agent.sock"
    sock.touch()
    args = build_args(spec_for(home, project, ssh_agent_sock=sock), {})
    assert (str(sock), str(sock)) in bind_pairs(args, "--bind")
    assert setenv_map(args)["SSH_AUTH_SOCK"] == str(sock)


def test_ssh_agent_sock_missing_not_bound(home: Path, project: Path, tmp_path: Path) -> None:
    sock = tmp_path / "missing.sock"
    args = build_args(spec_for(home, project, ssh_agent_sock=sock), {})
    joined = " ".join(args)
    assert str(sock) not in joined
    assert "SSH_AUTH_SOCK" not in setenv_map(args)


def test_gpg_agent_sock_bound_with_gnupg_ro(home: Path, project: Path, tmp_path: Path) -> None:
    sock = tmp_path / "S.gpg-agent"
    sock.touch()
    gnupg = home / ".gnupg"
    gnupg.mkdir()
    args = build_args(spec_for(home, project, gpg_agent_sock=sock), {})
    assert (str(sock), str(sock)) in bind_pairs(args, "--bind")
    assert (str(gnupg), str(gnupg)) in bind_pairs(args, "--ro-bind")
    assert setenv_map(args)["GNUPGHOME"] == str(gnupg)


def test_extra_ro_bound(home: Path, project: Path, tmp_path: Path) -> None:
    ro_path = tmp_path / "some-config"
    ro_path.mkdir()
    args = build_args(spec_for(home, project, extra_ro=(ro_path,)), {})
    assert (str(ro_path), str(ro_path)) in bind_pairs(args, "--ro-bind")


def test_extra_rw_bound(home: Path, project: Path, tmp_path: Path) -> None:
    rw_path = tmp_path / "some-state"
    rw_path.mkdir()
    args = build_args(spec_for(home, project, extra_rw=(rw_path,)), {})
    assert (str(rw_path), str(rw_path)) in bind_pairs(args, "--bind")


def test_extra_path_missing_not_bound(home: Path, project: Path, tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    args = build_args(spec_for(home, project, extra_ro=(missing,)), {})
    assert str(missing) not in " ".join(args)


def test_home_rw_binds_existing_paths(home: Path, project: Path) -> None:
    (home / ".config").mkdir()
    (home / ".local/state").mkdir(parents=True)
    home_rw = (".config", ".local/state", ".nonexistent")
    args = build_args(spec_for(home, project, home_rw=home_rw), {})
    rw = bind_pairs(args, "--bind")
    assert (str(home / ".config"), str(home / ".config")) in rw
    assert (str(home / ".local/state"), str(home / ".local/state")) in rw
    # Skipped because the dir doesn't exist on disk; mirrors RW_HOME_PATHS behavior.
    assert all(".nonexistent" not in src for src, _ in rw)


def test_home_mask_tmpfs_overrides_home_rw(home: Path, project: Path) -> None:
    (home / ".config").mkdir()
    args = build_args(spec_for(home, project, home_rw=(".config",), home_mask=(".config/gh",)), {})
    rw = bind_pairs(args, "--bind")
    tmpfs_targets = [args[i + 1] for i, a in enumerate(args) if a == "--tmpfs"]
    assert (str(home / ".config"), str(home / ".config")) in rw
    assert str(home / ".config/gh") in tmpfs_targets
    # Mask must appear AFTER the bind so it takes effect.
    config_path = str(home / ".config")
    bind_idx = next(i for i, a in enumerate(args) if a == "--bind" and args[i + 1] == config_path)
    tmpfs_idx = next(
        i for i, a in enumerate(args) if a == "--tmpfs" and args[i + 1] == str(home / ".config/gh")
    )
    assert bind_idx < tmpfs_idx


def test_home_rw_empty_by_default(home: Path, project: Path) -> None:
    args = build_args(spec_for(home, project), {})
    rw = bind_pairs(args, "--bind")
    # ~/.config is not among the standard RW_HOME_PATHS, only via home_rw.
    assert (str(home / ".config"), str(home / ".config")) not in rw


def test_wsl_resolv_conf_rebound_after_mnt_mask(home: Path, project: Path, tmp_path: Path) -> None:
    resolv = tmp_path / "resolv.conf"
    resolv.write_text("nameserver 1.1.1.1")
    with patch("sandboxr.backend.bwrap.WSL_RUNTIME_BINDS", (str(resolv),)):
        args = build_args(spec_for(home, project), {}, mask_paths=("/mnt",))
    tmpfs_targets = [args[i + 1] for i, a in enumerate(args) if a == "--tmpfs"]
    ro = bind_pairs(args, "--ro-bind")
    assert "/mnt" in tmpfs_targets
    assert (str(resolv), str(resolv)) in ro
    # resolv.conf rebind must come after the /mnt tmpfs mask.
    mnt_idx = next(i for i, a in enumerate(args) if a == "--tmpfs" and args[i + 1] == "/mnt")
    resolv_str = str(resolv)
    resolv_idx = next(
        i for i, a in enumerate(args) if a == "--ro-bind" and args[i + 1] == resolv_str
    )
    assert mnt_idx < resolv_idx


def test_wrap_command_is_identity() -> None:
    cmd = ["claude", "--dangerously-skip-permissions"]
    assert BwrapBackend().wrap_command(cmd) == cmd
