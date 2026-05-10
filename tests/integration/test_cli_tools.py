import pytest


@pytest.mark.integration
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
@pytest.mark.parametrize("binary", ["fzf", "rg", "eza", "bat", "zoxide"])
def test_cli_tool_available(host, binary, shell_cmd):
    """Verify each CLI binary is on PATH in bash and zsh."""
    result = host.run(f"{shell_cmd} 'command -v {binary}'")
    assert result.rc == 0, f"'{binary}' not found via {shell_cmd!r}.\nstderr: {result.stderr}"


@pytest.mark.integration
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
def test_opencode_available(host, shell_cmd):
    """Verify opencode is on PATH in bash and zsh, if supported by the OS."""
    if host.system_info.type == "darwin":
        pytest.skip("opencode is currently disabled on macOS")
    result = host.run(f"{shell_cmd} 'command -v opencode'")
    assert result.rc == 0, f"'opencode' not found via {shell_cmd!r}.\nstderr: {result.stderr}"


@pytest.mark.integration
def test_opencode_help(host):
    """Verify opencode --help runs successfully on supported platforms."""
    if host.system_info.type == "darwin":
        pytest.skip("opencode is currently disabled on macOS")
    result = host.run("opencode --help")
    assert result.rc == 0, f"'opencode --help' failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"
