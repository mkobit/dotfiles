import os

import pytest


@pytest.mark.integration
def test_tmux_config_loaded(host):
    """Verify that tmux starts and loads a configuration file."""
    socket_name = f"test-{os.getpid()}"
    result = host.run(f"tmux -L {socket_name} start-server \\; display-message -p '#{{config_files}}' \\; kill-server")
    assert result.rc == 0, f"tmux failed to start.\nstderr: {result.stderr}"
    assert result.stdout.strip(), "tmux reported no config files loaded"
