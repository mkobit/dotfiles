"""CLI integration tests using typer CliRunner and --show-command.

All tests use --show-command to verify bwrap invocation structure without
running bwrap. Git detection is disabled by mocking shutil.which("git")
to return None so _project_root falls back to cwd; shutil.which("bwrap")
is faked so _require_bwrap passes on non-Linux hosts.
"""

import os
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sandboxr.main import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _mock_which(monkeypatch):
    """Fake bwrap so _require_bwrap passes; return None for git/gpgconf."""
    _real = shutil.which

    def _which(name, **kwargs):
        if name == "bwrap":
            return "/usr/bin/bwrap"
        if name in ("git", "gpgconf"):
            return None
        return _real(name, **kwargs)

    monkeypatch.setattr(shutil, "which", _which)


@pytest.fixture(autouse=True)
def _chdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


# ── run --show-command ──────────────────────────────────────────────────────


def test_run_show_command_prints_copyable_bwrap_line():
    result = runner.invoke(app, ["run", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    # --show-command's own output is the last line: a single, copy-pasteable
    # command. Everything before it is the always-on per-token echo.
    assert result.output.rstrip().splitlines()[-1].startswith("bwrap")


def test_run_echoes_command_even_without_show_command(monkeypatch):
    # --show-command returns before os.execvp, so it can't prove the echo
    # survives on the real-execution path. Mock execvp instead so run()
    # falls through normally without actually replacing this process.
    monkeypatch.setattr("os.execvp", lambda *args, **kwargs: None)
    result = runner.invoke(app, ["run", "--", "bash"])
    assert result.exit_code == 0
    assert "sandboxr: sandbox invocation" in result.output
    assert "  bwrap" in result.output


def test_run_show_command_project_rw_bound(tmp_path):
    result = runner.invoke(app, ["run", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"--bind {tmp_path} {tmp_path}" in result.output


def test_run_show_command_no_project_write_ro_binds_project(tmp_path):
    result = runner.invoke(app, ["run", "--no-project-write", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"--ro-bind {tmp_path} {tmp_path}" in result.output


def test_run_show_command_network_none_unshares_net():
    result = runner.invoke(app, ["run", "--network", "none", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert "--unshare-net" in result.output


def test_run_show_command_network_shared_does_not_unshare_net():
    result = runner.invoke(app, ["run", "--network", "shared", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert "--unshare-net" not in result.output


def test_run_show_command_extra_ro_bound_when_path_exists(tmp_path):
    ro = tmp_path / "ro_file.txt"
    ro.write_text("data")
    result = runner.invoke(app, ["run", "--ro", str(ro), "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"--ro-bind {ro} {ro}" in result.output


def test_run_show_command_extra_rw_bound_when_path_exists(tmp_path):
    rw = tmp_path / "state_dir"
    rw.mkdir()
    result = runner.invoke(app, ["run", "--rw", str(rw), "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"--bind {rw} {rw}" in result.output


def test_run_show_command_extra_ro_not_bound_when_missing(tmp_path):
    missing = tmp_path / "nonexistent"
    result = runner.invoke(app, ["run", "--ro", str(missing), "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert str(missing) not in result.output


def test_run_show_command_ssh_agent_bound_when_sock_exists(tmp_path, monkeypatch):
    sock = tmp_path / "agent.sock"
    sock.touch()
    monkeypatch.setenv("SSH_AUTH_SOCK", str(sock))
    result = runner.invoke(app, ["run", "--ssh-agent", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"--bind {sock} {sock}" in result.output
    assert f"SSH_AUTH_SOCK {sock}" in result.output


def test_run_show_command_no_ssh_agent_flag_skips_sock(tmp_path, monkeypatch):
    sock = tmp_path / "agent.sock"
    sock.touch()
    monkeypatch.setenv("SSH_AUTH_SOCK", str(sock))
    result = runner.invoke(app, ["run", "--no-ssh-agent", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"SSH_AUTH_SOCK {sock}" not in result.output


def test_run_show_command_skip_permissions_default_adds_flag():
    result = runner.invoke(app, ["run", "--show-command", "--", "claude", "--print", "hi"])
    assert result.exit_code == 0
    assert "--dangerously-skip-permissions" in result.output


def test_run_show_command_no_skip_permissions_omits_flag():
    result = runner.invoke(
        app, ["run", "--no-skip-permissions", "--show-command", "--", "claude", "--print", "hi"]
    )
    assert result.exit_code == 0
    assert "--dangerously-skip-permissions" not in result.output


# ── run intent flags (--local-commit / --web-access / --push / --pr) ──────


def test_run_local_commit_forces_no_ssh_agent(tmp_path, monkeypatch):
    sock = tmp_path / "agent.sock"
    sock.touch()
    monkeypatch.setenv("SSH_AUTH_SOCK", str(sock))
    result = runner.invoke(app, ["run", "--local-commit", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"SSH_AUTH_SOCK {sock}" not in result.output


def test_run_push_true_binds_ssh_agent_sock(tmp_path, monkeypatch):
    sock = tmp_path / "agent.sock"
    sock.touch()
    monkeypatch.setenv("SSH_AUTH_SOCK", str(sock))
    result = runner.invoke(app, ["run", "--no-ssh-agent", "--push", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"SSH_AUTH_SOCK {sock}" in result.output


def test_run_push_false_omits_ssh_agent_sock(tmp_path, monkeypatch):
    sock = tmp_path / "agent.sock"
    sock.touch()
    monkeypatch.setenv("SSH_AUTH_SOCK", str(sock))
    result = runner.invoke(app, ["run", "--no-push", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"SSH_AUTH_SOCK {sock}" not in result.output


def test_run_web_access_false_unshares_net():
    result = runner.invoke(app, ["run", "--no-web-access", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert "--unshare-net" in result.output


def test_run_web_access_true_overrides_network_none():
    result = runner.invoke(
        app, ["run", "--network", "none", "--web-access", "--show-command", "--", "bash"]
    )
    assert result.exit_code == 0
    assert "--unshare-net" not in result.output


def test_run_pr_binds_gh_config_read_only(tmp_path, tmp_path_factory, monkeypatch):
    fake_home = tmp_path_factory.mktemp("home")
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    gh_dir = fake_home / ".config" / "gh"
    gh_dir.mkdir(parents=True)
    result = runner.invoke(app, ["run", "--pr", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"--ro-bind {gh_dir} {gh_dir}" in result.output


def test_run_pr_forces_ssh_agent_on(tmp_path, monkeypatch):
    sock = tmp_path / "agent.sock"
    sock.touch()
    monkeypatch.setenv("SSH_AUTH_SOCK", str(sock))
    result = runner.invoke(app, ["run", "--no-ssh-agent", "--pr", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"SSH_AUTH_SOCK {sock}" in result.output


def test_run_no_command_exits_nonzero():
    result = runner.invoke(app, ["run", "--show-command"])
    assert result.exit_code != 0


def test_run_nested_refused(monkeypatch):
    monkeypatch.setenv("AGENT_RUN_IN_SANDBOX", "1")
    result = runner.invoke(app, ["run", "--show-command", "--", "bash"])
    assert result.exit_code != 0


# ── shell --show-command ────────────────────────────────────────────────────


def test_shell_show_command_ends_with_shell():
    result = runner.invoke(app, ["shell", "--show-command"])
    assert result.exit_code == 0
    last_arg = result.output.strip().split()[-1]
    assert os.path.basename(last_arg) in {"bash", "zsh", "sh", "fish", "dash"}


def test_shell_show_command_tty_default_does_not_add_new_session():
    result = runner.invoke(app, ["shell", "--show-command"])
    assert result.exit_code == 0
    assert "--new-session" not in result.output


def test_shell_show_command_no_tty_adds_new_session():
    result = runner.invoke(app, ["shell", "--no-tty", "--show-command"])
    assert result.exit_code == 0
    assert "--new-session" in result.output


def test_shell_echoes_command_even_without_show_command(monkeypatch):
    monkeypatch.setattr("os.execvp", lambda *args, **kwargs: None)
    result = runner.invoke(app, ["shell"])
    assert result.exit_code == 0
    assert "sandboxr: sandbox invocation" in result.output
    assert "  bwrap" in result.output
