import subprocess


def test_tmux_runtime_tools_help():
    result = subprocess.run(
        ["uv", "run", "tmux-runtime-tools", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Usage: tmux-runtime-tools" in result.stdout
