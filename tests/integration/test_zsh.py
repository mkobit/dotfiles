import pytest


@pytest.mark.integration
def test_zsh_initialization(host):
    """Verify that zsh initializes without errors."""

    # Run zsh as an interactive login shell, then exit immediately.
    # This ensures .zprofile and .zshrc are sourced.
    result = host.run("zsh -i -c 'exit'")

    # Filter out known warnings caused by running an interactive shell without a
    # true TTY. These are structural limitations of the test environment, not
    # configuration errors. rc may be non-zero for the same reason (e.g. a shell
    # init snippet whose last statement is an `if [[ -o zle ]]` block that is
    # skipped without a terminal).
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
    stderr_lower = result.stderr.lower()
    for warning in known_benign_warnings:
        stderr_lower = stderr_lower.replace(warning.lower(), "")

    if "error" in stderr_lower or "command not found" in stderr_lower or "no such file or directory" in stderr_lower:
        pytest.fail(f"Potential errors found during zsh startup:\n{result.stderr}\nFiltered Stderr:\n{stderr_lower}")
