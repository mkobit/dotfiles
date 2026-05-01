import platform
import time

import pytest


@pytest.mark.integration
@pytest.mark.skipif(platform.system() != "Darwin", reason="Hammerspoon is macOS only")
def test_hammerspoon_config_valid(host):
    """Verify that Hammerspoon config is valid by executing it via the CLI headless mode."""
    # Attempt to start Hammerspoon in background so IPC works
    host.run("open -j -a Hammerspoon || true")

    # Try to find hs cli
    hs_paths = [
        "/Applications/Hammerspoon.app/Contents/Frameworks/hs/hs",
        "/opt/homebrew/bin/hs",
        "/usr/local/bin/hs",
        "hs",
    ]
    hs_cmd = None
    for path in hs_paths:
        if host.run(f"command -v {path}").rc == 0:
            hs_cmd = path
            break

    if not hs_cmd:
        host.run("killall Hammerspoon || true")
        pytest.skip("Hammerspoon CLI 'hs' not found, skipping validation.")

    # Verify config loading
    # We use pcall to catch errors instead of crashing HS or just returning non-zero exit code unpredictably
    cmd = f'{hs_cmd} -c \'local ok, err = pcall(dofile, os.getenv("HOME") .. "/.dotfiles/hammerspoon/init.lua"); if not ok then print(err); os.exit(1) end; print("SUCCESS")\''

    # Wait for HS to start and be ready for IPC by polling
    for _ in range(20):  # poll every 0.25s up to 5s
        result = host.run(cmd)
        if result.rc != 69:  # RC 69 is 'ipc not loaded/reachable'
            break
        time.sleep(0.25)

    # Clean up
    host.run("killall Hammerspoon || true")

    if result.rc == 69:
        pytest.skip(f"Hammerspoon IPC not reachable in headless CI: {result.stderr}")
    elif result.rc != 0 or "SUCCESS" not in result.stdout:
        pytest.fail(
            f"Hammerspoon config failed to load.\nRC: {result.rc}\nStdout: {result.stdout}\nStderr: {result.stderr}"
        )
