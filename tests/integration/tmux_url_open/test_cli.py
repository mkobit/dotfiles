import subprocess


def test_tmux_url_open_help():
    result = subprocess.run(
        ["uv", "run", "tmux-url-open", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Usage: tmux-url-open" in result.stdout
