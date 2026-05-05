import pytest


@pytest.mark.integration
def test_zsh_interactive_login_loads_cleanly(host):
    """Verify that a zsh interactive login shell sources config without errors."""
    result = host.run("zsh -i -l -c 'exit'")
    assert result.rc == 0, f"zsh interactive login shell exited with {result.rc}\nstderr: {result.stderr}"
    stderr_lower = result.stderr.lower()
    known_benign = [
        "not interactive and can't open terminal",
        "compinit: initialization aborted",
        "inappropriate ioctl for device",
        "zsh: command not found: compdef",
        "can't change option: zle",
        "stty: 'standard input'",
        "(eval):1:",
        "(eval):2:",
        "not a tty",
        "no job control in this shell",
    ]
    for warning in known_benign:
        stderr_lower = stderr_lower.replace(warning, "")
    assert "error" not in stderr_lower and "command not found" not in stderr_lower, (
        f"Errors found during zsh startup:\n{result.stderr}"
    )
