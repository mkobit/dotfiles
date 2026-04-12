import os
import subprocess

import pytest


@pytest.mark.asyncio
async def test_zsh_config_syntax():
    """Ensure compiled config.zsh evaluates correctly without syntax errors."""
    try:
        config_path = os.path.expanduser("~/.dotfiles/zsh/config.zsh")
        if not os.path.exists(config_path):
            pytest.skip("zsh config not found")

        # Verify syntax with zsh -n
        subprocess.run(["zsh", "-n", config_path], check=True)
    except FileNotFoundError:
        pytest.skip("zsh not installed")


@pytest.mark.asyncio
async def test_bash_config_syntax():
    """Ensure compiled config.bash evaluates correctly without syntax errors."""
    try:
        config_path = os.path.expanduser("~/.dotfiles/bash/config.bash")
        if not os.path.exists(config_path):
            pytest.skip("bash config not found")

        # Verify syntax with bash -n
        subprocess.run(["bash", "-n", config_path], check=True)
    except FileNotFoundError:
        pytest.skip("bash not installed")
