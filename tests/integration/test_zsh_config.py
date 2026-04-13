import os

import pytest


def get_chezmoi_dest():
    """Get the target destination for chezmoi."""
    dest = os.environ.get("CHEZMOI_DEST")
    if dest:
        return dest
    return os.path.expanduser("~")


@pytest.mark.integration
def test_zsh_config_loads_effectively(host):
    """Verify that zsh actually loads the intended configuration without errors."""
    dest_dir = get_chezmoi_dest()
    config_path = os.path.join(dest_dir, ".dotfiles/zsh/config.zsh")

    if not os.path.exists(config_path):
        pytest.skip(f"Zsh config not found at: {config_path}")

    # Use zsh to source the config and verify it loads cleanly
    result = host.run(f"ZDOTDIR={dest_dir} zsh -c 'source {config_path}'")
    assert result.rc == 0, (
        f"Zsh failed to load config correctly. stderr: {result.stderr}"
    )
