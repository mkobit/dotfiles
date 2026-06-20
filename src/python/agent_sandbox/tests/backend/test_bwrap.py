from pathlib import Path

import pytest

from agent_sandbox.backend.bwrap import CACHE_REL, build_args
from agent_sandbox.sandbox.spec import SandboxSpec


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


def spec_for(home: Path, project: Path, **overrides: object) -> SandboxSpec:
    return SandboxSpec(
        home=overrides.pop("home", home),  # type: ignore[arg-type]
        project_root=overrides.pop("project_root", project),  # type: ignore[arg-type]
        project_write=overrides.pop("project_write", True),  # type: ignore[arg-type]
        profile_name=overrides.pop("profile_name", "autonomous"),  # type: ignore[arg-type]
        cwd=overrides.pop("cwd", project),  # type: ignore[arg-type]
        git_common_dir=overrides.pop("git_common_dir", None),  # type: ignore[arg-type]
        extra_env=overrides.pop("extra_env", {}),  # type: ignore[arg-type]
        tty=overrides.pop("tty", False),  # type: ignore[arg-type]
        network=overrides.pop("network", "shared"),  # type: ignore[arg-type]
        ssh_agent_sock=overrides.pop("ssh_agent_sock", None),  # type: ignore[arg-type]
        gpg_agent_sock=overrides.pop("gpg_agent_sock", None),  # type: ignore[arg-type]
        extra_ro=overrides.pop("extra_ro", ()),  # type: ignore[arg-type]
        extra_rw=overrides.pop("extra_rw", ()),  # type: ignore[arg-type]
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
    assert setenv_map(args)["GH_TOKEN"] == "scoped"


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
