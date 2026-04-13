import os

import pytest


def get_chezmoi_dest():
    """Get the target destination for chezmoi."""
    dest = os.environ.get("CHEZMOI_DEST")
    if dest:
        return dest
    return os.path.expanduser("~")


@pytest.mark.integration
def test_tmux_config_loads_effectively(host):
    """Verify that tmux actually loads the intended configuration without errors."""
    dest_dir = get_chezmoi_dest()
    config_path = os.path.join(dest_dir, ".dotfiles/tmux/config.tmux")

    if not os.path.exists(config_path):
        pytest.skip(f"Tmux config not found at: {config_path}")

    # Use tmux to source the config and list keys or options to verify it loads cleanly
    result = host.run(
        f"tmux -f {config_path} start-server \\; show-options -g \\; kill-server"
    )
    assert result.rc == 0, (
        f"Tmux failed to load config correctly. stderr: {result.stderr}"
    )
