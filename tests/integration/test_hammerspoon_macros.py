import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import suppress
from pathlib import Path

import pytest
from integration_support.chezmoi import chezmoi_argv, run_chezmoi

SOURCE = Path("src/chezmoi/dot_dotfiles/hammerspoon")


@pytest.fixture
def loaded_hammerspoon(request):
    if not request.config.getoption("--start-hammerspoon"):
        pytest.skip("Use --start-hammerspoon to start the config load check")
    if sys.platform != "darwin":
        pytest.skip("Hammerspoon requires macOS")

    app = Path(os.environ.get("HAMMERSPOON_APP", "/Applications/Hammerspoon.app"))
    executable = app / "Contents/MacOS/Hammerspoon"
    cli = app / "Contents/Frameworks/hs/hs"
    assert executable.is_file() and cli.is_file(), f"Hammerspoon app or bundled CLI is missing: {app}"
    existing = subprocess.run(
        ["pgrep", "-x", "Hammerspoon"],
        capture_output=True,
        stdin=subprocess.DEVNULL,
        timeout=5,
        check=False,
    )
    assert existing.returncode == 1, "Stop the config load check: Hammerspoon is already running"

    scratch = (Path.cwd() / ".scratch").resolve()
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hammerspoon-", dir=scratch) as directory:
        target = Path(directory)
        config_dir = target / ".dotfiles/hammerspoon"
        shutil.copytree(SOURCE, config_dir)
        rendered = asyncio.run(
            run_chezmoi(
                chezmoi_argv(
                    "--config-format",
                    "toml",
                    "execute-template",
                    "-f",
                    "--override-data",
                    json.dumps({"hammerspoon": {"window_manager": {"enabled": False}}}),
                    str(SOURCE / "config.lua.tmpl"),
                    source=target,
                    destination=target,
                    config="/dev/null",
                )
            )
        )
        assert rendered.returncode == 0, rendered.stderr
        (config_dir / "config.lua").write_text(rendered.stdout)
        (config_dir / "config.lua.tmpl").unlink()
        real_init = config_dir / "dotfiles-init.lua"
        (config_dir / "init.lua").rename(real_init)
        token = uuid.uuid4().hex
        (config_dir / "init.lua").write_text(
            'require("hs.ipc")\n'
            f"local ok, err = pcall(dofile, {json.dumps(str(real_init))})\n"
            "_G.DotfilesLoadCheck = {\n"
            f'    token = "{token}", ok = ok, error = tostring(err),\n'
            '    config = type(_G.DotfilesConfig) == "table",\n'
            '    actions = type(_G.DotfilesActions) == "table",\n'
            '    tag = type((_G.DotfilesActions or {}).wrapPromptTag) == "function",\n'
            "    menu = _G.DotfilesMacroMenu ~= nil,\n"
            "}\n"
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
            last_probe = "No IPC response"
            result = None
            try:
                deadline = time.monotonic() + 45
                while time.monotonic() < deadline and process.poll() is None:
                    try:
                        probe = subprocess.run(
                            [str(cli), "-q", "-t", "1", "-c", "return hs.json.encode(_G.DotfilesLoadCheck or {})"],
                            stdin=subprocess.DEVNULL,
                            capture_output=True,
                            text=True,
                            timeout=3,
                            check=False,
                        )
                        last_probe = f"Exit {probe.returncode}: {probe.stdout}\n{probe.stderr}"
                        if probe.returncode == 0:
                            result = json.loads(probe.stdout)
                            if result.get("token") == token:
                                break
                    except (subprocess.TimeoutExpired, json.JSONDecodeError) as error:
                        last_probe = str(error)
                    time.sleep(0.2)
                assert result and result.get("token") == token, (
                    f"Hammerspoon startup failed or IPC timed out (exit {process.poll()}).\n"
                    f"{last_probe}\nStartup log ({log_path}):\n{log_path.read_text()}"
                )
                yield result, log_path
            finally:
                if process.poll() is None:
                    with suppress(ProcessLookupError):
                        process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        with suppress(ProcessLookupError):
                            process.kill()
                        process.wait(timeout=5)


@pytest.mark.hammerspoon
def test_rendered_hammerspoon_config_loads(loaded_hammerspoon):
    result, log_path = loaded_hammerspoon
    assert result["ok"], f"Config load failed: {result['error']}\n{log_path.read_text()}"
    assert result["config"] and result["actions"] and result["tag"] and result["menu"], result
