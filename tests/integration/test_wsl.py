import os
import platform
import subprocess

import pytest

_is_wsl = "microsoft" in platform.release().lower()


@pytest.mark.integration
@pytest.mark.skipif(not _is_wsl, reason="WSL-only: verifies .wslconfig was deployed")
def test_wslconfig_deployed_to_windows_profile(host):
    """Verify .wslconfig was deployed to the Windows user profile."""
    result = subprocess.run(
        ["/mnt/c/Windows/System32/cmd.exe", "/c", "echo %USERPROFILE%"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, "Could not get Windows user profile path via cmd.exe"
    win_profile = result.stdout.strip()
    unix_profile = subprocess.check_output(["wslpath", "-u", win_profile], text=True).strip()
    wslconfig = host.file(os.path.join(unix_profile, ".wslconfig"))
    assert wslconfig.exists


@pytest.mark.integration
@pytest.mark.skipif(not _is_wsl, reason="WSL-only: verifies /etc/wsl.conf was deployed")
def test_wslconf_deployed(host):
    """Verify /etc/wsl.conf was deployed and contains expected settings."""
    wslconf = host.file("/etc/wsl.conf")
    assert wslconf.exists
    assert "[boot]" in wslconf.content_string
    assert "systemd=true" in wslconf.content_string
