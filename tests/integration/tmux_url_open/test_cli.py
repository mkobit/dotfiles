import shutil
import subprocess

import pytest


@pytest.mark.integration
def test_tmux_url_open_on_path() -> None:
    assert shutil.which("tmux-url-open") is not None, (
        "tmux-url-open not found on PATH — run chezmoi apply to install it"
    )


@pytest.mark.integration
def test_tmux_url_open_help() -> None:
    result = subprocess.run(
        ["tmux-url-open", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--pane-id" in result.stdout
