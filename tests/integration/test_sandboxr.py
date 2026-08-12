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
def test_doctor_default_passes(host):
    if not _tool_available(host, "bwrap"):
        pytest.skip("bwrap not installed on this runner")
    result = host.run("sandboxr doctor")
    assert result.rc == 0, f"doctor failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert "sandboxr doctor: all probes passed" in result.stdout
    assert "FAIL:" not in result.stdout
    # A passing exit code alone isn't proof the probes actually ran: a bug
    # where the wrapped command silently never executes (exit 0, zero probe
    # output) would pass this check if we only asserted on the return code.
    assert result.stdout.count("PASS:") >= 8, f"expected several PASS lines, got:\n{result.stdout}"


@pytest.mark.integration
@pytest.mark.skipif(not _is_linux, reason="bwrap backend is Linux-only")
def test_doctor_no_project_write_passes(host):
    if not _tool_available(host, "bwrap"):
        pytest.skip("bwrap not installed on this runner")
    result = host.run("sandboxr doctor --no-project-write")
    assert result.rc == 0, f"doctor failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert "sandboxr doctor: all probes passed" in result.stdout
    assert "FAIL:" not in result.stdout
    assert "project write=0 as expected" in result.stdout
