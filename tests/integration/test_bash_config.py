import os

import pytest


def get_chezmoi_dest():
    """Get the target destination for chezmoi."""
    dest = os.environ.get("CHEZMOI_DEST")
    if dest:
        return dest
    return os.path.expanduser("~")


@pytest.mark.integration
def test_bash_config_loads_effectively(host):
    """Verify that bash actually loads the intended configuration without errors."""
    dest_dir = get_chezmoi_dest()
    config_path = os.path.join(dest_dir, ".dotfiles/bash/config.bash")

    if not os.path.exists(config_path):
        pytest.skip(f"Bash config not found at: {config_path}")

    # Use bash to source the config and verify it loads cleanly
    result = host.run(f"bash -c 'source {config_path}'")
    assert result.rc == 0, (
        f"Bash failed to load config correctly. stderr: {result.stderr}"
    )
