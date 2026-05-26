import pytest


@pytest.mark.integration
def test_bash_login_loads_cleanly(host):
    """Verify that a bash login shell sources config without errors."""
    result = host.run("bash -l -c 'exit'")
    assert result.rc == 0, f"bash login shell exited with {result.rc}\nstderr: {result.stderr}"
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


@pytest.mark.integration
def test_bash_login_shell_produces_no_stdout(host):
    """bash -l must produce no stdout in non-interactive contexts.

    Jules' env-save hook runs `bash -l -c 'env'` after env_setup.sh exits and
    parses stdout strictly as KEY=VALUE pairs.  Any non-KEY=VALUE line — a
    warning, a banner, a "tool not found" message — causes the parse to fail
    silently, breaking every subsequent Jules task with no actionable error.

    Guard: this test catches regressions before they reach Jules.  If it fails,
    ~/.bash_profile (or a file it sources) is emitting stdout in a
    non-interactive login shell.  Fix: gate the offending output behind
    `[[ $- == *i* ]]` or redirect it to stderr.
    """
    result = host.run("bash -l -c 'true'")
    assert result.rc == 0, f"bash -l -c 'true' failed\nstderr: {result.stderr}"
    assert result.stdout == "", (
        "bash -l produced stdout — Jules env-save hook will fail.\n"
        "~/.bash_profile or a file it sources is printing to stdout in a non-interactive login shell.\n"
        "Fix: gate the output behind [[ $- == *i* ]] or redirect to stderr.\n"
        f"Stdout was:\n{result.stdout}"
    )
