import shutil

import pytest


@pytest.mark.integration
@pytest.mark.parametrize("binary", ["fzf", "rg", "eza", "bat", "zoxide"])
def test_cli_tools_available_in_shells(host, binary):
    """Verify that key binaries are available on PATH in both bash and zsh."""

    # First verify if it's installed via python path or mocked
    binary_path = shutil.which(binary)

    # Check bash
    bash_result = host.run(f"bash -l -c 'command -v {binary}'")

    if binary_path is None and bash_result.rc != 0:
        pytest.skip(f"Binary '{binary}' is not installed in this environment.")

    assert bash_result.rc == 0, (
        f"Expected binary '{binary}' not found in bash login shell"
    )

    # Check zsh
    zsh_result = host.run(f"zsh -i -c 'command -v {binary}'")
    assert zsh_result.rc == 0, (
        f"Expected binary '{binary}' not found in zsh interactive shell"
    )
