import pytest


@pytest.mark.integration
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
def test_mise_on_path(host, shell_cmd):
    """Verify that mise is on PATH in bash and zsh login shells."""
    result = host.run(f"{shell_cmd} 'command -v mise'")
    assert result.rc == 0, f"mise not found via {shell_cmd!r}.\nstderr: {result.stderr}"


@pytest.mark.integration
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
def test_gemini_on_path(host, shell_cmd):
    """Verify that gemini is on PATH in bash and zsh login shells."""
    result = host.run(f"{shell_cmd} 'command -v gemini'")
    assert result.rc == 0, (
        f"gemini not found via {shell_cmd!r}.\nstderr: {result.stderr}"
    )
