import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

from chezmoi_cli import ChezmoiCli

SOURCE = Path("src/chezmoi/dot_dotfiles/hammerspoon")
pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="Hammerspoon requires macOS")


def test_rendered_hammerspoon_config_loads():
    executable = Path("/Applications/Hammerspoon.app/Contents/MacOS/Hammerspoon")
    assert executable.is_file(), f"Hammerspoon is missing: {executable}"
    existing = subprocess.run(
        ["pgrep", "-x", "Hammerspoon"],
        capture_output=True,
        stdin=subprocess.DEVNULL,
        timeout=5,
        check=False,
    )
    if existing.returncode == 0:
        pytest.skip("Hammerspoon is already running")
    assert existing.returncode == 1, f"Could not check Hammerspoon processes: {existing.stderr.decode()}"

    scratch = (Path.cwd() / ".scratch").resolve()
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hammerspoon-", dir=scratch) as directory:
        target = Path(directory)
        config_dir = target / ".dotfiles/hammerspoon"
        shutil.copytree(SOURCE, config_dir)
        rendered = asyncio.run(
            ChezmoiCli(source=target, destination=target, config="/dev/null", config_format="toml")
            .execute_template(
                file=SOURCE / "config.lua.tmpl",
                override_data={"hammerspoon": {"window_manager": {"enabled": False}}},
            )
            .run_async()
        )
        assert rendered.returncode == 0, rendered.stderr
        (config_dir / "config.lua").write_text(rendered.stdout)
        (config_dir / "config.lua.tmpl").unlink()
        real_init = config_dir / "dotfiles-init.lua"
        (config_dir / "init.lua").rename(real_init)
        status_path = target / "load-status"
        (config_dir / "init.lua").write_text(
            f"local ok, err = pcall(dofile, {json.dumps(str(real_init))})\n"
            f'local status = assert(io.open({json.dumps(str(status_path) + ".pending")}, "w"))\n'
            'status:write(ok and "loaded" or tostring(err))\n'
            "status:close()\n"
            f"assert(os.rename({json.dumps(str(status_path) + '.pending')}, {json.dumps(str(status_path))}))\n"
        )
        report_dir = Path(os.environ["RUNNER_TEMP"]) / "integration-reports" if "RUNNER_TEMP" in os.environ else target
        report_dir.mkdir(parents=True, exist_ok=True)
        log_path = report_dir / "hammerspoon-startup.log"
        with log_path.open("w") as log:
            process = subprocess.Popen(
                [str(executable), "-MJConfigFile", str(config_dir / "init.lua")],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                deadline = time.monotonic() + 20
                while not status_path.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.1)
                status = status_path.read_text() if status_path.exists() else "No config load result"
                assert status == "loaded", f"{status}\nStartup log ({log_path}):\n{log_path.read_text()}"
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
