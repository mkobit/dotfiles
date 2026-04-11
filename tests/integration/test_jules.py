import pytest


@pytest.mark.integration
def test_jules_cli_available(host):
    """Verify that jules CLI is available and executable in the shell environment."""

    # We want to ensure that if we load the zsh environment, we can resolve 'jules'.
    # This simulates what a user does when opening a terminal.
    result = host.run("zsh -i -c 'command -v jules'")

    assert result.rc == 0, (
        f"jules command not found in zsh environment.\nstderr: {result.stderr}"
    )
    assert "jules" in result.stdout, (
        "command -v jules did not print a path containing 'jules'."
    )


@pytest.mark.integration
def test_jules_cli_help(host):
    """Verify that the jules CLI actually runs correctly (prints help)."""

    result = host.run("zsh -i -c 'jules --help'")

    assert result.rc == 0, f"jules --help failed.\nstderr: {result.stderr}"
    assert "Usage: jules" in result.stdout or "Usage:" in result.stdout, (
        "Did not find expected help output."
    )
