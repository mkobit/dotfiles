import shutil
import subprocess

import pytest


@pytest.mark.integration
def test_jules_cli_available():
    """Verify that jules CLI is available and executable in the shell environment."""
    jules_path = shutil.which("jules")
    assert jules_path is not None, "jules command not found on PATH"


@pytest.mark.integration
def test_jules_cli_help():
    """Verify that the jules CLI actually runs correctly (prints help)."""
    jules_path = shutil.which("jules")
    assert jules_path is not None, "jules command not found on PATH"

    result = subprocess.run([jules_path, "--help"], capture_output=True, text=True)

    assert result.returncode == 0, f"jules --help failed.\nstderr: {result.stderr}"
    assert "Usage: jules" in result.stdout or "Usage:" in result.stdout, (
        "Did not find expected help output."
    )
