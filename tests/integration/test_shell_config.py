import os
import subprocess

import pytest


def get_chezmoi_dest():
    """Get the target destination for chezmoi."""
    dest = os.environ.get("CHEZMOI_DEST")
    if dest:
        return dest
    # Fallback to home directory if environment variable is not set
    return os.path.expanduser("~")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_zsh_config_syntax():
    """Ensure compiled config.zsh evaluates correctly without syntax errors."""
    dest_dir = get_chezmoi_dest()
    config_path = os.path.join(dest_dir, ".dotfiles/zsh/config.zsh")
    if not os.path.exists(config_path):
        pytest.skip("zsh config not found")

    # Verify syntax with zsh -n
    subprocess.run(["zsh", "-n", config_path], check=True)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_bash_config_syntax():
    """Ensure compiled config.bash evaluates correctly without syntax errors."""
    dest_dir = get_chezmoi_dest()
    config_path = os.path.join(dest_dir, ".dotfiles/bash/config.bash")
    if not os.path.exists(config_path):
        pytest.skip("bash config not found")

    # Verify syntax with bash -n
    subprocess.run(["bash", "-n", config_path], check=True)
