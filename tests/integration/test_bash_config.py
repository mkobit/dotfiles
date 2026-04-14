import pytest


@pytest.mark.integration
def test_bash_login_loads_cleanly(host):
    """Verify that a bash login shell sources config without errors."""
    result = host.run("bash -l -c 'exit'")
    assert result.rc == 0, (
        f"bash login shell exited with {result.rc}\nstderr: {result.stderr}"
    )
    stderr_lower = result.stderr.lower()
    known_benign = [
        "not interactive and can't open terminal",
        "inappropriate ioctl for device",
        "not a tty",
        "no job control in this shell",
    ]
    for warning in known_benign:
        stderr_lower = stderr_lower.replace(warning, "")
    assert "error" not in stderr_lower and "command not found" not in stderr_lower, (
        f"Errors found during bash login startup:\n{result.stderr}"
    )
