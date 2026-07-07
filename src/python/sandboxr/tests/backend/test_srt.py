import dataclasses
import json
import os
import shlex
import stat
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest

from sandboxr.backend.bwrap import CACHE_REL
from sandboxr.backend.srt import (
    SrtBackend,
    build_args,
    build_settings,
    wrap_command,
    write_settings,
)
from sandboxr.sandbox.spec import SandboxSpec


@pytest.fixture
def home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    for rel in (".local/bin", ".local/share/mise", ".claude", CACHE_REL):
        (home / rel).mkdir(parents=True)
    (home / ".claude.json").write_text("{}")
    return home


@pytest.fixture
def mise_install(tmp_path: Path):
    """Fake `mise where npm:@anthropic-ai/sandbox-runtime` result: a real
    cli.js under a mise-style install dir, plus the mocked which()/run()
    needed to resolve it."""
    install_dir = tmp_path / "mise-installs" / "npm-anthropic-ai-sandbox-runtime" / "0.0.63"
    cli_js = install_dir / "node_modules" / "@anthropic-ai" / "sandbox-runtime" / "dist" / "cli.js"
    cli_js.parent.mkdir(parents=True)
    cli_js.write_text("")

    def _which(name: str, **kwargs: object) -> str | None:
        if name in ("node", "mise"):
            return f"/usr/bin/{name}"
        return None

    def _run(args: list[str], **kwargs: object) -> CompletedProcess:
        return CompletedProcess(args, 0, stdout=f"{install_dir}\n", stderr="")

    with (
        patch("shutil.which", side_effect=_which),
        patch("sandboxr.backend.srt.subprocess.run", side_effect=_run),
    ):
        yield cli_js


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
    network: str = "allowlist",
    allowed_domains: tuple[str, ...] = ("api.example.com",),
    git_common_dir: Path | None = None,
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
        profile_name="srt-test",
        cwd=project,
        git_common_dir=git_common_dir,
        network=network,
        allowed_domains=allowed_domains,
        ssh_agent_sock=ssh_agent_sock,
        gpg_agent_sock=gpg_agent_sock,
        extra_ro=extra_ro,
        extra_rw=extra_rw,
        home_rw=home_rw,
        home_mask=home_mask,
    )


def test_deny_read_includes_home_and_mask_paths(home: Path, project: Path) -> None:
    settings = build_settings(spec_for(home, project), mask_paths=("/mnt",))
    assert settings["filesystem"]["denyRead"] == [str(home), "/mnt"]


def test_allow_read_includes_ro_home_paths(home: Path, project: Path) -> None:
    settings = build_settings(spec_for(home, project))
    allow_read = settings["filesystem"]["allowRead"]
    assert str(home / ".local/bin") in allow_read
    assert str(home / ".local/share/mise") in allow_read


def test_allow_read_includes_project_extra_ro_and_home_rw(
    home: Path,
    project: Path,
    tmp_path: Path,
) -> None:
    extra = tmp_path / "extra-ro"
    extra.mkdir()
    (home / ".config").mkdir()
    settings = build_settings(spec_for(home, project, extra_ro=(extra,), home_rw=(".config",)))
    allow_read = settings["filesystem"]["allowRead"]
    assert str(project) in allow_read
    assert str(extra) in allow_read
    assert str(home / ".config") in allow_read


def test_allow_write_includes_rw_home_paths(home: Path, project: Path) -> None:
    settings = build_settings(spec_for(home, project))
    allow_write = settings["filesystem"]["allowWrite"]
    assert str(home / ".claude") in allow_write
    assert str(home / CACHE_REL) in allow_write


def test_allow_read_includes_rw_home_paths(home: Path, project: Path) -> None:
    # RW_HOME_PATHS must be readable too, not just writable -- e.g. claude
    # needs to *read* ~/.claude.json (its own auth state), not just write it.
    # bwrap's --bind grants read+write; the srt port must match that.
    settings = build_settings(spec_for(home, project))
    allow_read = settings["filesystem"]["allowRead"]
    assert str(home / ".claude") in allow_read
    assert str(home / ".claude.json") in allow_read


def test_allow_write_includes_project_only_when_project_write(home: Path, project: Path) -> None:
    writable = build_settings(spec_for(home, project, project_write=True))
    readonly = build_settings(spec_for(home, project, project_write=False))
    assert str(project) in writable["filesystem"]["allowWrite"]
    assert str(project) not in readonly["filesystem"]["allowWrite"]


def test_deny_write_includes_home_mask(home: Path, project: Path) -> None:
    settings = build_settings(spec_for(home, project, home_mask=(".config/gh",)))
    assert str(home / ".config/gh") in settings["filesystem"]["denyWrite"]


def test_deny_read_includes_home_mask(home: Path, project: Path) -> None:
    # home_mask must hide read too, not just write -- otherwise a credential
    # dir nested under a home_rw expose (e.g. .config/gh under .config)
    # stays readable even though it's supposed to be masked.
    settings = build_settings(spec_for(home, project, home_mask=(".config/gh",)))
    assert str(home / ".config/gh") in settings["filesystem"]["denyRead"]


def test_allow_read_includes_wsl_resolv_conf(home: Path, project: Path, tmp_path: Path) -> None:
    # Regression: default_mask_paths() denyReads /mnt on WSL2, and
    # /etc/resolv.conf is a symlink into /mnt/wsl/resolv.conf -- without
    # re-exposing it, DNS resolution inside the sandbox fails outright
    # (confirmed empirically: a real `claude` session hung after this broke).
    # bwrap.py already has this re-expose (wsl_runtime_binds()); srt.py must
    # match it.
    resolv = tmp_path / "resolv.conf"
    resolv.write_text("nameserver 1.1.1.1")
    with patch("sandboxr.backend.bwrap.WSL_RUNTIME_BINDS", (str(resolv),)):
        settings = build_settings(spec_for(home, project), mask_paths=("/mnt",))
    assert str(resolv) in settings["filesystem"]["allowRead"]


def test_network_allowlist_sets_allowed_domains(home: Path, project: Path) -> None:
    domains = ("api.example.com", "*.foo.com")
    settings = build_settings(spec_for(home, project, network="allowlist", allowed_domains=domains))
    assert settings["network"]["allowedDomains"] == ["api.example.com", "*.foo.com"]
    assert settings["network"]["deniedDomains"] == []


def test_network_none_denies_everything(home: Path, project: Path) -> None:
    settings = build_settings(spec_for(home, project, network="none", allowed_domains=()))
    assert settings["network"]["allowedDomains"] == []
    assert settings["network"]["deniedDomains"] == ["*"]


def test_network_shared_raises(home: Path, project: Path) -> None:
    with pytest.raises(ValueError, match="shared"):
        build_settings(spec_for(home, project, network="shared", allowed_domains=()))


def test_allow_unix_sockets_for_ssh_and_gpg(home: Path, project: Path, tmp_path: Path) -> None:
    ssh_sock = tmp_path / "ssh.sock"
    ssh_sock.touch()
    settings = build_settings(spec_for(home, project, ssh_agent_sock=ssh_sock))
    assert settings["network"]["allowUnixSockets"] == [str(ssh_sock)]


def test_no_allow_unix_sockets_key_when_no_agents(home: Path, project: Path) -> None:
    settings = build_settings(spec_for(home, project))
    assert "allowUnixSockets" not in settings["network"]


def test_write_settings_writes_json_mode_0600(home: Path) -> None:
    path = write_settings({"a": 1}, home)
    assert json.loads(path.read_text()) == {"a": 1}
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_write_settings_cleans_up_stale_files(home: Path) -> None:
    settings_dir = home / ".local/share/sandboxr/srt-settings"
    settings_dir.mkdir(parents=True)
    stale = settings_dir / "stale.json"
    stale.write_text("{}")
    os.utime(stale, (0, 0))
    write_settings({"a": 1}, home)
    assert not stale.exists()


def test_build_args_returns_node_cli_and_settings(
    home: Path,
    project: Path,
    mise_install: Path,
) -> None:
    args = build_args(spec_for(home, project), {})
    assert args[-4] == "/usr/bin/node"
    assert args[-3] == str(mise_install)
    assert args[-2] == "-s"
    assert Path(args[-1]).exists()


def test_build_args_env_prefix_curates_environment(
    home: Path,
    project: Path,
    mise_install: Path,
) -> None:
    # Neither srt's settings.json nor its own internal bwrap wrapping clears
    # the environment, so sandboxr must curate it itself, the same way
    # bwrap.py's --clearenv/--setenv does -- otherwise the full host
    # environment (secrets included) flows straight into the sandbox.
    args = build_args(spec_for(home, project), {"SECRET_TOKEN": "leak-me"})
    assert args[0] == "env"
    assert args[1] == "-i"
    env_args = args[2:-4]
    assert f"HOME={home}" in env_args
    assert "AGENT_RUN_IN_SANDBOX=1" in env_args
    assert "AGENT_RUN_PROFILE=srt-test" in env_args
    assert not any(a.startswith("SECRET_TOKEN") for a in env_args)


def test_build_args_env_includes_extra_env(home: Path, project: Path, mise_install: Path) -> None:
    spec = spec_for(home, project)
    spec = dataclasses.replace(spec, extra_env={"GH_TOKEN": "abc123"})
    args = build_args(spec, {})
    assert "GH_TOKEN=abc123" in args[2:-4]


def test_build_args_env_includes_ssh_and_gpg_agent_vars(
    home: Path,
    project: Path,
    tmp_path: Path,
    mise_install: Path,
) -> None:
    ssh_sock = tmp_path / "ssh.sock"
    ssh_sock.touch()
    args = build_args(spec_for(home, project, ssh_agent_sock=ssh_sock), {})
    assert f"SSH_AUTH_SOCK={ssh_sock}" in args[2:-4]


def test_build_args_env_passthrough_from_environ(
    home: Path,
    project: Path,
    mise_install: Path,
) -> None:
    args = build_args(spec_for(home, project), {"TERM": "xterm-256color"})
    assert "TERM=xterm-256color" in args[2:-4]


def test_build_args_raises_when_node_missing(home: Path, project: Path) -> None:
    with patch("shutil.which", return_value=None), pytest.raises(RuntimeError, match="node"):
        build_args(spec_for(home, project), {})


def _which_node_only(name: str, **kwargs: object) -> str | None:
    return "/usr/bin/node" if name == "node" else None


def _which_node_and_mise(name: str, **kwargs: object) -> str | None:
    return f"/usr/bin/{name}" if name in ("node", "mise") else None


def test_build_args_raises_when_mise_missing(home: Path, project: Path) -> None:
    with (
        patch("shutil.which", side_effect=_which_node_only),
        pytest.raises(RuntimeError, match="mise"),
    ):
        build_args(spec_for(home, project), {})


def test_build_args_raises_when_srt_not_provisioned(home: Path, project: Path) -> None:
    def _run(args: list[str], **kwargs: object) -> CompletedProcess:
        return CompletedProcess(args, 1, stdout="", stderr="not installed")

    with (
        patch("shutil.which", side_effect=_which_node_and_mise),
        patch("sandboxr.backend.srt.subprocess.run", side_effect=_run),
        pytest.raises(RuntimeError, match="not provisioned"),
    ):
        build_args(spec_for(home, project), {})


def test_wrap_command_prepends_grace_sleep() -> None:
    cmd = ["claude", "--dangerously-skip-permissions"]
    wrapped = wrap_command(cmd)
    assert wrapped == ["bash", "-c", "sleep 0.2; exec claude --dangerously-skip-permissions"]


def test_wrap_command_has_no_trailing_positional_args() -> None:
    # Regression: srt silently drops every positional arg that follows a
    # `bash -c <script>` spawn, so the wrapped command must be exactly
    # ["bash", "-c", script] -- nothing trailing for srt to swallow.
    wrapped = wrap_command(["claude", "--dangerously-skip-permissions"])
    assert len(wrapped) == 3
    assert wrapped[0] == "bash"
    assert wrapped[1] == "-c"


def test_wrap_command_preserves_args_with_spaces_and_quotes() -> None:
    cmd = ["sh", "-c", 'echo "hi there"']
    wrapped = wrap_command(cmd)
    script = wrapped[2]
    embedded = script.removeprefix("sleep 0.2; exec ")
    assert shlex.split(embedded) == cmd


def test_backend_name_is_srt() -> None:
    assert SrtBackend().name == "srt"
