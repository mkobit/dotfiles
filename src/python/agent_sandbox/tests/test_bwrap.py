from pathlib import Path

import pytest

from agent_sandbox.bwrap import CACHE_REL, SandboxSpec, build_args


def bind_pairs(args, flag):
    pairs = []
    for i, arg in enumerate(args):
        if arg == flag:
            pairs.append((args[i + 1], args[i + 2]))
    return pairs


def setenv_map(args):
    env = {}
    for i, arg in enumerate(args):
        if arg == "--setenv":
            env[args[i + 1]] = args[i + 2]
    return env


@pytest.fixture
def home(tmp_path):
    home = tmp_path / "home"
    for rel in (".local/bin", ".local/share/mise", ".claude", CACHE_REL):
        (home / rel).mkdir(parents=True)
    (home / ".claude.json").write_text("{}")
    return home


@pytest.fixture
def project(tmp_path):
    project = tmp_path / "home" / "projects" / "demo"
    project.mkdir(parents=True)
    return project


def spec_for(home, project, **overrides):
    return SandboxSpec(
        home=overrides.pop("home", home),
        project_root=overrides.pop("project_root", project),
        project_write=overrides.pop("project_write", True),
        profile_name=overrides.pop("profile_name", "autonomous"),
        cwd=overrides.pop("cwd", project),
        git_common_dir=overrides.pop("git_common_dir", None),
        extra_env=overrides.pop("extra_env", {}),
        keep_tty=overrides.pop("keep_tty", False),
    )


def test_home_is_tmpfs_with_explicit_rebinds(home, project):
    args = build_args(spec_for(home, project), {"PATH": "/usr/bin"})
    tmpfs_targets = [args[i + 1] for i, a in enumerate(args) if a == "--tmpfs"]
    assert str(home) in tmpfs_targets
    assert "/tmp" in tmpfs_targets
    ro = bind_pairs(args, "--ro-bind")
    assert (str(home / ".local/bin"), str(home / ".local/bin")) in ro
    assert (str(home / ".local/share/mise"), str(home / ".local/share/mise")) in ro
    # Not created on disk, so not bound.
    assert all(".dotfiles" not in src for src, _ in ro)


def test_agent_state_bound_rw_and_credentials_never_bound(home, project):
    args = build_args(spec_for(home, project), {})
    rw = bind_pairs(args, "--bind")
    assert (str(home / ".claude"), str(home / ".claude")) in rw
    assert (str(home / ".claude.json"), str(home / ".claude.json")) in rw
    joined = " ".join(args)
    assert ".ssh" not in joined
    assert ".gnupg" not in joined
    assert ".config/gh" not in joined


def test_project_bind_mode_follows_profile(home, project):
    rw_args = build_args(spec_for(home, project, project_write=True), {})
    ro_args = build_args(spec_for(home, project, project_write=False), {})
    assert (str(project), str(project)) in bind_pairs(rw_args, "--bind")
    assert (str(project), str(project)) in bind_pairs(ro_args, "--ro-bind")
    assert (str(project), str(project)) not in bind_pairs(ro_args, "--bind")


def test_git_common_dir_bound_for_linked_worktrees(home, project):
    common = home / "projects" / "main-checkout" / ".git"
    common.mkdir(parents=True)
    args = build_args(spec_for(home, project, git_common_dir=common), {})
    assert (str(common), str(common)) in bind_pairs(args, "--bind")


def test_cache_is_dedicated_not_host_cache(home, project):
    args = build_args(spec_for(home, project), {})
    assert (str(home / CACHE_REL), str(home / ".cache")) in bind_pairs(args, "--bind")


def test_env_is_cleared_with_allowlist_only(home, project):
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
    assert env["GIT_CONFIG_GLOBAL"] == str(home / ".config/ai-policy/git/sandbox.gitconfig")
    assert "SSH_AUTH_SOCK" not in env
    assert "GPG_TTY" not in env
    assert "GH_TOKEN" not in env


def test_extra_env_injected(home, project):
    args = build_args(spec_for(home, project, extra_env={"GH_TOKEN": "scoped"}), {})
    assert setenv_map(args)["GH_TOKEN"] == "scoped"


def test_mask_paths_are_tmpfs(home, project):
    args = build_args(spec_for(home, project), {}, mask_paths=("/mnt", "/run/user/1000"))
    tmpfs_targets = [args[i + 1] for i, a in enumerate(args) if a == "--tmpfs"]
    assert "/mnt" in tmpfs_targets
    assert "/run/user/1000" in tmpfs_targets


def test_new_session_unless_keep_tty(home, project):
    assert "--new-session" in build_args(spec_for(home, project), {})
    assert "--new-session" not in build_args(spec_for(home, project, keep_tty=True), {})


def test_chdir_to_cwd(home, project):
    args = build_args(spec_for(home, project), {})
    idx = args.index("--chdir")
    assert args[idx + 1] == str(project)
    assert Path(args[idx + 1]).is_absolute()
