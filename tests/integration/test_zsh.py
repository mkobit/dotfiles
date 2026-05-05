import pytest


@pytest.mark.integration
def test_zsh_non_interactive_no_zoxide_doctor(host):
    """Verify that a non-interactive zsh shell does not trigger the zoxide doctor warning.

    The zoxide chpwd hook only fires in interactive shells, so initializing
    zoxide in non-interactive contexts is pointless and causes a spurious
    doctor warning every time `cd` is called (e.g. in AI agent sessions).
    """
    # Source .zshrc explicitly so the zsh config is loaded but the shell is
    # still non-interactive. Before the fix, this would trigger the zoxide
    # doctor warning because the chpwd hook was registered in non-interactive
    # contexts where it can never fire.
    result = host.run("zsh -c 'source ~/.zshrc; cd /tmp; cd -'")

    assert "zoxide: detected a possible configuration issue" not in result.stderr, (
        f"zoxide doctor warning fired in non-interactive shell:\n{result.stderr}"
    )


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
