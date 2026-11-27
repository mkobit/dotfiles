import os
import platform
import shutil
import subprocess
from pathlib import Path

import pytest

from chezmoi_cli import ChezmoiCli

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WSL_CMD = "/mnt/c/Windows/System32/cmd.exe"
FONT_HOOK = "dot_local/share/fonts/.chezmoiscripts/run_onchange_after_install-wsl-windows-fonts.sh.tmpl"
WSL_RELEASE = "6.18.33-microsoft-standard-WSL2"
_is_wsl = platform.system() == "Linux" and "microsoft" in platform.release().lower()


@pytest.mark.integration
@pytest.mark.skipif(not _is_wsl, reason="WSL-only: verifies .wslconfig was deployed")
def test_wslconfig_deployed_to_windows_profile(host):
    """Verify .wslconfig was deployed to the Windows user profile."""
    if not os.access(WSL_CMD, os.X_OK) or shutil.which("wslpath") is None:
        pytest.skip("Windows interop tools are unavailable")
    integration = (
        ChezmoiCli().execute_template('{{ dig "wsl" "windows_integration" false . | toJson }}').run(check=True).stdout
    )
    if integration.strip() != "true":
        pytest.skip("Windows integration is disabled in the chezmoi config")
    result = subprocess.run(
        [WSL_CMD, "/c", "echo %USERPROFILE%"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, "Could not get Windows user profile path via cmd.exe"
    win_profile = result.stdout.strip()
    unix_profile = subprocess.check_output(["wslpath", "-u", win_profile], text=True).strip()
    wslconfig = host.file(os.path.join(unix_profile, ".wslconfig"))
    assert wslconfig.exists


def test_wslconfig_template_renders_nested_virtualization():
    """Verify wslconfig template renders nestedVirtualization under [wsl2]."""
    result = (
        ChezmoiCli(config="/dev/null", config_format="toml", source=REPO_ROOT)
        .execute_template('{{ template "wsl/wslconfig" . }}')
        .run()
    )
    assert result.returncode == 0, result.stderr
    assert "nestedVirtualization=true" in result.stdout


@pytest.mark.parametrize(
    ("hook", "enabled", "interop_available", "kernel_release", "expected"),
    [
        ("run_onchange_after_windows_terminal_settings.sh.tmpl", True, False, WSL_RELEASE, False),
        ("run_onchange_after_wslconfig.sh.tmpl", True, False, WSL_RELEASE, False),
        (FONT_HOOK, True, False, WSL_RELEASE, False),
        (FONT_HOOK, None, True, WSL_RELEASE, False),
        (FONT_HOOK, False, True, WSL_RELEASE, False),
        (FONT_HOOK, "false", True, WSL_RELEASE, False),
        (FONT_HOOK, True, True, WSL_RELEASE, True),
        (FONT_HOOK, True, True, "6.18.33-generic", False),
    ],
)
def test_windows_hook_rendering(
    tmp_path: Path, hook: str, enabled: bool | str | None, interop_available: bool, kernel_release: str, expected: bool
) -> None:
    chezmoi = shutil.which("chezmoi")
    assert chezmoi is not None
    if interop_available:
        for command in ("wslpath", "powershell.exe"):
            stub = tmp_path / command
            stub.write_text("#!/bin/sh\nexit 1\n")
            stub.chmod(0o755)
    data: dict[str, object] = {
        "chezmoi": {"os": "linux", "kernel": {"osrelease": kernel_release}},
    }
    if enabled is not None:
        data["wsl"] = {"windows_integration": enabled}
    result = (
        ChezmoiCli(
            executable=chezmoi,
            config="/dev/null",
            config_format="toml",
            source=REPO_ROOT,
            destination=tmp_path,
        )
        .execute_template(override_data=data)
        .run(
            input=(REPO_ROOT / "src" / "chezmoi" / hook).read_text(),
            env={**os.environ, "PATH": str(tmp_path)},
            check=True,
        )
    )
    assert bool(result.stdout.strip()) is expected
