import pytest


@pytest.mark.integration
def test_zsh_initialization(host):
    """Verify that zsh initializes without errors."""

    # Run zsh as an interactive login shell, then exit immediately.
    # This ensures .zprofile and .zshrc are sourced.
    result = host.run("zsh -i -c 'exit'")

    # Check that return code is 0, which means no fatal errors.
    assert result.rc == 0, (
        f"zsh exited with {result.rc}\nstderr: {result.stderr}\nstdout: {result.stdout}"
    )

    # Ideally, stderr should not contain syntax errors or missing command errors
    # Filter out known non-errors if any exist, but for a clean config it should be
    # empty or not contain "error"/"command not found".
    stderr_lower = result.stderr.lower()

    # Filter out known warnings caused by running an interactive shell
    # without a true TTY
    known_benign_warnings = [
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
    for warning in known_benign_warnings:
        stderr_lower = stderr_lower.replace(warning.lower(), "")

    if (
        "error" in stderr_lower
        or "command not found" in stderr_lower
        or "no such file or directory" in stderr_lower
    ):
        pytest.fail(
            f"Potential errors found during zsh startup:\n{result.stderr}\n"
            f"Filtered Stderr:\n{stderr_lower}"
        )
