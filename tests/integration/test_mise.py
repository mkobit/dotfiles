import pytest


@pytest.mark.integration
def test_gemini_cli_installed(host):
    """Verify that gemini is on the path and executable."""
    bash_result = host.run("bash -l -c 'command -v gemini'")
    assert bash_result.rc == 0, "gemini command not found in bash login shell"

    zsh_result = host.run("zsh -i -c 'command -v gemini'")
    assert zsh_result.rc == 0, "gemini command not found in zsh interactive shell"


@pytest.mark.integration
def test_mise_executable(host):
    """Verify that mise is on the path and executable."""
    bash_result = host.run("bash -l -c 'command -v mise'")
    assert bash_result.rc == 0, "mise command not found in bash login shell"

    zsh_result = host.run("zsh -i -c 'command -v mise'")
    assert zsh_result.rc == 0, "mise command not found in zsh interactive shell"
