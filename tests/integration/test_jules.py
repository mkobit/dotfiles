import os
import subprocess

import pytest


@pytest.mark.integration
def test_jules_cli_available():
    """Verify that jules CLI is available and executable in the shell environment."""

    env = os.environ.copy()

    # We want to ensure that if we load the zsh environment, we can resolve 'jules'.
    # This simulates what a user does when opening a terminal.
    result = subprocess.run(
        ["zsh", "-i", "-c", "command -v jules"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, (
        f"jules command not found in zsh environment.\nstderr: {result.stderr}"
    )
    assert "jules" in result.stdout, (
        "command -v jules did not print a path containing 'jules'."
    )


@pytest.mark.integration
def test_jules_cli_help():
    """Verify that the jules CLI actually runs correctly (prints help)."""
    env = os.environ.copy()

    result = subprocess.run(
        ["zsh", "-i", "-c", "jules --help"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"jules --help failed.\nstderr: {result.stderr}"
    assert "Usage: jules" in result.stdout or "Usage:" in result.stdout, (
        "Did not find expected help output."
    )
