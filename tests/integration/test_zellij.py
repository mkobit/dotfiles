import os

import pytest


@pytest.mark.integration
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
def test_zellij_available(host, shell_cmd):
    """Verify zellij binary is on PATH in login shells."""
    result = host.run(f"{shell_cmd} 'command -v zellij'")
    assert result.rc == 0, (
        f"'zellij' not found via {shell_cmd!r}.\nstderr: {result.stderr}"
    )


@pytest.mark.integration
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
def test_zellij_version(host, shell_cmd):
    """Verify zellij reports a version string in login shells."""
    result = host.run(f"{shell_cmd} 'zellij --version'")
    assert result.rc == 0, (
        f"'zellij --version' failed via {shell_cmd!r}.\nstderr: {result.stderr}"
    )
    assert "zellij" in result.stdout.lower(), (
        f"Unexpected output from zellij --version: {result.stdout!r}"
    )


@pytest.mark.integration
def test_zellij_config_valid(host):
    """Verify that zellij configuration is valid."""
    result = host.run("zellij setup --check")
    assert result.rc == 0, (
        f"zellij config is invalid.\nstderr: {result.stderr}\nstdout: {result.stdout}"
    )
