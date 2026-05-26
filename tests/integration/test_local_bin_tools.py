import pytest

TOOLS = ["jules", "termbud", "transcribe", "claude-statusline"]


@pytest.mark.integration
@pytest.mark.parametrize("tool", TOOLS)
def test_tool_installed_in_dotfiles_bin(host, tool):
    result = host.run(f"zsh -i -c 'command -v {tool}'")
    assert result.rc == 0, f"{tool} not found in PATH.\nstderr: {result.stderr}"
    assert "dotfiles" in result.stdout, f"{tool} not installed in ~/.local/bin/dotfiles/.\nstdout: {result.stdout}"


@pytest.mark.integration
@pytest.mark.parametrize("tool", TOOLS)
def test_tool_not_using_uv_run(host, tool):
    result = host.run(f"zsh -i -c 'command -v {tool}'")
    assert result.rc == 0, f"{tool} not found.\nstderr: {result.stderr}"
    binary_path = result.stdout.strip()
    content = host.file(binary_path).content_string
    assert "uv run" not in content, (
        f"{tool} at {binary_path} still delegates to 'uv run'; expected a uv tool install binary."
    )
