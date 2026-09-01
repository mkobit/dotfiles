import subprocess
import sys
import time
from pathlib import Path


def test_entrypoint_does_not_import_typer_for_agy_render() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import sys; import termstatus.entrypoint; print('typer' in sys.modules)"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == "False\n"


def test_console_script_renders_from_a_fresh_process() -> None:
    command = [str(Path(sys.executable).with_name("statusline")), "antigravity", "render"]
    payload = '{"agent_state":"working"}'
    durations = []
    for _ in range(5):
        started = time.perf_counter()
        result = subprocess.run(command, input=payload, capture_output=True, check=False, text=True, timeout=1)
        durations.append(time.perf_counter() - started)
        assert result.returncode == 0
        assert "working" in result.stdout
    assert max(durations) < 0.75
