import platform

import pytest

_is_linux = platform.system() == "Linux"


def _tool_available(host, command: str) -> bool:
    return host.run(f"command -v {command}").rc == 0


def _srt_available(host) -> bool:
    return host.run("mise where npm:@anthropic-ai/sandbox-runtime").rc == 0


def _domain_reachable(host, domain: str) -> bool:
    return host.run(f"curl -sf --max-time 5 --head https://{domain}").rc == 0


@pytest.mark.integration
def test_sandboxr_on_path(host):
    result = host.run("command -v sandboxr")
    assert result.rc == 0, f"sandboxr not found on PATH.\nstderr: {result.stderr}"


@pytest.mark.integration
@pytest.mark.skipif(not _is_linux, reason="bwrap backend is Linux-only")
def test_doctor_bwrap_profile_passes(host):
    if not _tool_available(host, "bwrap"):
        pytest.skip("bwrap not installed on this runner")
    # readonly, not autonomous: autonomous moved to the srt backend
    # (domain-allowlisted egress) so it no longer exercises bwrap.
    result = host.run("sandboxr doctor --profile readonly")
    assert result.rc == 0, f"doctor failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert "sandboxr doctor: all probes passed" in result.stdout
    assert "FAIL:" not in result.stdout
    # A passing exit code alone isn't proof the probes actually ran: a bug
    # where the wrapped command silently never executes (confirmed to have
    # happened for real with the srt backend -- exit 0, zero probe output)
    # would pass this check if we only asserted on the return code.
    assert result.stdout.count("PASS:") >= 8, f"expected several PASS lines, got:\n{result.stdout}"


@pytest.mark.integration
@pytest.mark.skipif(not _is_linux, reason="srt-claude acceptance profile targets Linux for now")
def test_doctor_srt_claude_profile_passes(host):
    if not _srt_available(host):
        pytest.skip("srt not provisioned via mise on this runner")
    if not _domain_reachable(host, "api.anthropic.com"):
        pytest.skip("api.anthropic.com unreachable from runner — sandbox domain probe requires host access")
    result = host.run("sandboxr doctor --profile srt-claude")
    assert result.rc == 0, f"doctor failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert "sandboxr doctor: all probes passed" in result.stdout
    assert "FAIL:" not in result.stdout
    assert result.stdout.count("PASS:") >= 8, f"expected several PASS lines, got:\n{result.stdout}"
    # Confirms the domain allowlist is enforced by the real srt proxy, not
    # just that srt.py compiled a settings file that looks right.
    assert "allowed domain reachable" in result.stdout
    assert "denied domain blocked" in result.stdout
