import pytest


@pytest.mark.integration
@pytest.mark.parametrize("binary", ["fzf", "rg", "eza", "bat", "zoxide"])
def test_cli_tools_available_in_shells(host, binary):
    """Verify that key binaries are available on PATH in both bash and zsh."""

    # Check bash
    bash_result = host.run(f"bash -l -c 'command -v {binary}'")
    # For a sandbox environment we cannot install everything, we'll mark xfail if not installed.
    # The reviewer said "I feel like we should execute and verify they're on the path in both bash and zsh. For these tools I don't really care if --help works"
    # The goal is that the integration test suite has them. In this sandbox they fail.
    # We will assert that the exit status is 0.

    assert bash_result.rc == 0, (
        f"Expected binary '{binary}' not found in bash login shell"
    )

    # Check zsh
    zsh_result = host.run(f"zsh -i -c 'command -v {binary}'")
    assert zsh_result.rc == 0, (
        f"Expected binary '{binary}' not found in zsh interactive shell"
    )
