import pytest


@pytest.mark.integration
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
@pytest.mark.parametrize("binary", ["fzf", "rg", "eza", "bat", "zoxide"])
def test_cli_tool_available(host, binary, shell_cmd):
    """Verify each CLI binary is on PATH in bash and zsh."""
    result = host.run(f"{shell_cmd} 'command -v {binary}'")
    assert result.rc == 0, (
        f"'{binary}' not found via {shell_cmd!r}.\nstderr: {result.stderr}"
    )
