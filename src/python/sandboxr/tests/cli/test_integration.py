"""CLI integration tests using typer CliRunner and --show-command.

All tests use --show-command to verify bwrap invocation structure without
running bwrap. Git detection is disabled by mocking shutil.which("git")
to return None so _project_root falls back to cwd; shutil.which("bwrap")
is faked so _require_bwrap passes on non-Linux hosts.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sandboxr.backend import srt as srt_backend
from sandboxr.main import app
from sandboxr.profile import loader

SANDBOX_TOML = """
default_profile = "default"

[profiles.default]
enabled = true
backend = "bwrap"
project_write = true
network = "shared"
ssh_agent = false
gpg_agent = false

[profiles.readonly]
enabled = true
backend = "bwrap"
project_write = false
network = "shared"
ssh_agent = false
gpg_agent = false

[profiles.airgap]
enabled = true
backend = "bwrap"
project_write = false
network = "none"
ssh_agent = false
gpg_agent = false

[profiles.srt-allowlist]
enabled = true
backend = "srt"
project_write = true
network = "allowlist"
allowed_domains = ["api.example.com"]
ssh_agent = false
gpg_agent = false
"""

runner = CliRunner()


@pytest.fixture(autouse=True)
def _patch_config(tmp_path, monkeypatch):
    config = tmp_path / "sandbox.toml"
    config.write_text(SANDBOX_TOML)
    monkeypatch.setattr(loader, "CONFIG_PATH", config)


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


def test_run_show_command_starts_with_bwrap():
    result = runner.invoke(app, ["run", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert result.output.startswith("bwrap")


def test_run_show_command_project_rw_bound(tmp_path):
    result = runner.invoke(app, ["run", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"--bind {tmp_path} {tmp_path}" in result.output


def test_run_show_command_readonly_profile_ro_binds_project(tmp_path):
    result = runner.invoke(app, ["run", "--profile", "readonly", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert f"--ro-bind {tmp_path} {tmp_path}" in result.output


def test_run_show_command_airgap_profile_unshares_net():
    result = runner.invoke(app, ["run", "--profile", "airgap", "--show-command", "--", "bash"])
    assert result.exit_code == 0
    assert "--unshare-net" in result.output


def test_run_show_command_network_none_override_unshares_net():
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


def test_run_no_command_exits_nonzero():
    result = runner.invoke(app, ["run", "--show-command"])
    assert result.exit_code != 0


def test_run_unknown_profile_exits_nonzero():
    result = runner.invoke(app, ["run", "--profile", "unknown", "--show-command", "--", "bash"])
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


# ── profiles subcommand ─────────────────────────────────────────────────────


def test_profiles_lists_all_profiles():
    result = runner.invoke(app, ["profiles"])
    assert result.exit_code == 0
    assert "default" in result.output
    assert "readonly" in result.output
    assert "airgap" in result.output


def test_profiles_marks_default():
    result = runner.invoke(app, ["profiles"])
    assert result.exit_code == 0
    assert "(default)" in result.output


def test_profiles_shows_capability_fields():
    result = runner.invoke(app, ["profiles"])
    assert result.exit_code == 0
    assert "network=" in result.output
    assert "project_write=" in result.output
    assert "ssh_agent=" in result.output
    assert "gpg_agent=" in result.output


# ── run --show-command (srt backend) ────────────────────────────────────────


def test_run_srt_backend_fails_when_node_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(shutil, "which", lambda name, **kwargs: None)
    result = runner.invoke(
        app,
        ["run", "--profile", "srt-allowlist", "--show-command", "--", "bash"],
    )
    assert result.exit_code != 0


def test_run_srt_backend_fails_when_not_provisioned(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        shutil,
        "which",
        lambda name, **kwargs: f"/usr/bin/{name}" if name in ("node", "mise") else None,
    )

    def _run(args, **kwargs):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="not installed")

    monkeypatch.setattr(srt_backend.subprocess, "run", _run)
    result = runner.invoke(
        app,
        ["run", "--profile", "srt-allowlist", "--show-command", "--", "bash"],
    )
    assert result.exit_code != 0


def test_run_srt_backend_show_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(
        shutil,
        "which",
        lambda name, **kwargs: f"/usr/bin/{name}" if name in ("node", "mise") else None,
    )
    install_dir = tmp_path / "mise-installs" / "npm-anthropic-ai-sandbox-runtime" / "0.0.63"
    cli_js = install_dir / srt_backend.CLI_JS_RELATIVE_TO_INSTALL
    cli_js.parent.mkdir(parents=True)
    cli_js.write_text("")

    def _run(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout=f"{install_dir}\n", stderr="")

    monkeypatch.setattr(srt_backend.subprocess, "run", _run)
    result = runner.invoke(
        app,
        ["run", "--profile", "srt-allowlist", "--show-command", "--", "bash"],
    )
    assert result.exit_code == 0
    assert result.output.startswith("env -i ")
    assert "AGENT_RUN_IN_SANDBOX=1" in result.output
    assert "/usr/bin/node" in result.output
    assert str(cli_js) in result.output
    assert "-s" in result.output
    # startup-race workaround: the trailing command is wrapped, not raw.
    assert 'sleep 0.2; exec "$@"' in result.output
