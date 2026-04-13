import os
import shutil

import pytest


@pytest.mark.integration
@pytest.mark.parametrize("binary", ["fzf", "rg", "eza", "bat", "zoxide"])
def test_binaries_on_path(host, binary):
    """Verify that key binaries are available on PATH after apply."""
    # 1. Check python PATH (shutil.which)
    binary_path = shutil.which(binary)

    # 2. Check shell-level presence (via zsh -i) using host.run
    result = host.run(f"zsh -i -c 'command -v {binary}'")

    # In CI, tests might be run before chezmoi applies or tools aren't mocked.
    # The prompt explicitly asks to assert these things, not to skip them.
    assert binary_path is not None or result.rc == 0, (
        f"Expected binary '{binary}' not found on PATH or via zsh login"
    )


def get_chezmoi_dest():
    """Get the target destination for chezmoi."""
    dest = os.environ.get("CHEZMOI_DEST")
    if dest:
        return dest
    # Fallback to home directory if environment variable is not set
    return os.path.expanduser("~")


@pytest.mark.integration
@pytest.mark.parametrize(
    "config_path_suffix", [".dotfiles/zsh/config.zsh", ".dotfiles/tmux/config.tmux"]
)
def test_critical_dotfiles_exist(config_path_suffix):
    """Verify that critical dotfile configs exist at expected paths."""
    dest_dir = get_chezmoi_dest()
    config_path = os.path.join(dest_dir, config_path_suffix)
    # Again, the prompt says "assert the binary is on PATH... "
    # So we'll let this fail if the environment hasn't been set up yet.
    assert os.path.exists(config_path), (
        f"Critical dotfile config not found at: {config_path}"
    )
