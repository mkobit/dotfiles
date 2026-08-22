import platform

import pytest

_is_linux = platform.system() == "Linux"


def _tool_available(host, command: str) -> bool:
    return host.run(f"command -v {command}").rc == 0


@pytest.mark.integration
def test_sandboxr_on_path(host):
    result = host.run("command -v sandboxr")
    assert result.rc == 0, f"sandboxr not found on PATH.\nstderr: {result.stderr}"


@pytest.mark.integration
@pytest.mark.skipif(not _is_linux, reason="bwrap backend is Linux-only")
def test_sandboxr_on_hold_fails_closed(host):
    result = host.run("sandboxr doctor")
    assert result.rc == 1, f"expected sandboxr to fail closed while on hold.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert "sandboxr is currently on hold" in result.stderr
