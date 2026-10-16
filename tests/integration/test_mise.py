import json
import os
import shlex
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _render_shell(template, destination, shell):
    result = subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPOSITORY_ROOT),
            "--destination",
            str(destination),
            "execute-template",
            "--override-data",
            json.dumps({"shell": shell, "local": {"bin": {"mise": {"installation_method": "github_releases"}}}}),
            *(["--file", str(template)] if isinstance(template, Path) else [template]),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


@pytest.mark.parametrize("shell", ["bash", "zsh"])
def test_shared_path_preserves_host_tool_before_existing_mise_shims(tmp_path, shell):
    shell_path = shutil.which(shell)
    if shell_path is None:
        pytest.skip(f"{shell} is unavailable")
    host_bin = tmp_path / "host-bin"
    shims = tmp_path / ".local/share/mise/shims"
    for directory, version in ((host_bin, "host uv"), (shims, "stale shim")):
        directory.mkdir(parents=True)
        executable = directory / "uv"
        executable.write_text(f"#!/bin/sh\nprintf '%s\\n' '{version}'\n", encoding="utf-8")
        executable.chmod(0o755)
    fragment = tmp_path / "path.sh"
    fragment.write_text(_render_shell('{{ template "shell/xdg_path.sh" . }}', tmp_path, shell), encoding="utf-8")

    options = ["--noprofile", "--norc"] if shell == "bash" else ["-d", "-f"]
    result = subprocess.run(
        [shell_path, *options, "-lc", f"source {shlex.quote(str(fragment))}; uv --version"],
        env={**os.environ, "PATH": f"{host_bin}:/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "host uv\n"


@pytest.mark.parametrize("shell", ["bash", "zsh"])
@pytest.mark.parametrize("interactive", [False, True])
def test_mise_activation_runs_only_in_interactive_shells(tmp_path, shell, interactive):
    shell_path = shutil.which(shell)
    if shell_path is None:
        pytest.skip(f"{shell} is unavailable")
    local_bin = tmp_path / ".local/bin"
    local_bin.mkdir(parents=True)
    mise = local_bin / "mise"
    mise.write_text(
        f"#!/bin/sh\ntest \"$1 $2\" = 'activate {shell}' || exit 1\nprintf '%s\\n' 'export TEST_MISE_ACTIVATED=yes'\n",
        encoding="utf-8",
    )
    mise.chmod(0o755)
    if shell == "zsh":
        modifier = _render_shell(REPOSITORY_ROOT / "src/chezmoi/modify_dot_zprofile.tmpl", tmp_path, shell)
        profile = subprocess.run(
            ["/bin/sh", "-c", modifier], input="", text=True, capture_output=True, check=True
        ).stdout
        (tmp_path / ".zprofile").write_text(profile, encoding="utf-8")
        startup = ""
        options = ["-d"]
    else:
        fragment = tmp_path / "mise.sh"
        fragment.write_text(_render_shell('{{ template "shell/mise.sh" . }}', tmp_path, shell), encoding="utf-8")
        startup = f"source {shlex.quote(str(fragment))}; "
        options = ["--noprofile", "--norc"]
    env = {key: value for key, value in os.environ.items() if key != "TEST_MISE_ACTIVATED"}
    env.update({"PATH": f"{local_bin}:/usr/bin:/bin", "ZDOTDIR": str(tmp_path)})

    result = subprocess.run(
        [
            shell_path,
            *options,
            "-lic" if interactive else "-lc",
            startup + 'printf "%s\\n" "${TEST_MISE_ACTIVATED:-no}"',
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == ("yes\n" if interactive else "no\n")


@pytest.mark.parametrize(
    ("overlay_settings", "expected_shims", "expected_log_level"),
    [
        pytest.param(None, False, "warn", id="base-init"),
        pytest.param("", False, "warn", id="minimal-overlay"),
        pytest.param('log_level = "debug"\n', False, "debug", id="overlay-setting"),
        pytest.param('log_level = "debug"\nactivate_shims = true\n', True, "debug", id="overlay-override"),
    ],
)
def test_mise_config_disables_activation_shims_unless_overridden(
    tmp_path, overlay_settings, expected_shims, expected_log_level
):
    config = tmp_path / "chezmoi.toml"
    chezmoi = shutil.which("chezmoi")
    assert chezmoi is not None
    if overlay_settings is None:
        command = [
            chezmoi,
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPOSITORY_ROOT),
            "--destination",
            str(tmp_path),
            "execute-template",
            "--init",
            "--file",
            str(REPOSITORY_ROOT / "src/chezmoi/.chezmoi.toml.tmpl"),
        ]
        initialized = subprocess.run(
            command, env={**os.environ, "CI": "1", "PATH": os.defpath}, capture_output=True, text=True, check=True
        )
        config.write_text(initialized.stdout, encoding="utf-8")
    else:
        config.write_text("[data.mise.settings]\n" + overlay_settings, encoding="utf-8")
    rendered = subprocess.run(
        [
            "chezmoi",
            "--config",
            str(config),
            "--source",
            str(REPOSITORY_ROOT),
            "--destination",
            str(tmp_path),
            "execute-template",
            "--file",
            str(REPOSITORY_ROOT / "src/chezmoi/dot_config/mise/config.toml.tmpl"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    settings = tomllib.loads(rendered.stdout)["settings"]
    assert settings.get("activate_shims") is expected_shims
    assert settings["log_level"] == expected_log_level


@pytest.mark.integration
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
def test_mise_on_path(host, shell_cmd):
    """Verify that mise is on PATH in bash and zsh login shells."""
    result = host.run(f"{shell_cmd} 'command -v mise'")
    assert result.rc == 0, f"mise not found via {shell_cmd!r}.\nstderr: {result.stderr}"
