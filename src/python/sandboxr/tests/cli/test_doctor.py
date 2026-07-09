import os
import subprocess
from pathlib import Path

from sandboxr.cli.doctor import PROBE_SCRIPT, _probe_env
from sandboxr.sandbox.spec import SandboxSpec


def spec_for(*, network: str = "shared", allowed_domains: tuple[str, ...] = ()) -> SandboxSpec:
    return SandboxSpec(
        home=Path("/home/test"),
        project_root=Path("/home/test/project"),
        project_write=True,
        profile_name="test",
        cwd=Path("/home/test/project"),
        network=network,
        allowed_domains=allowed_domains,
    )


def test_probe_env_includes_project_and_network() -> None:
    env = _probe_env(spec_for())
    assert env["PROBE_PROJECT"] == "/home/test/project"
    assert env["PROBE_PROJECT_WRITE"] == "1"
    assert env["PROBE_NETWORK"] == "shared"


def test_probe_env_no_domain_vars_when_not_allowlist() -> None:
    env = _probe_env(spec_for(network="none"))
    assert "PROBE_ALLOWED_DOMAIN" not in env
    assert "PROBE_DENIED_DOMAIN" not in env


def test_probe_env_sets_allowed_and_denied_domain_for_allowlist() -> None:
    env = _probe_env(spec_for(network="allowlist", allowed_domains=("api.example.com",)))
    assert env["PROBE_ALLOWED_DOMAIN"] == "api.example.com"
    assert "PROBE_DENIED_DOMAIN" in env
    assert env["PROBE_DENIED_DOMAIN"] != "api.example.com"


def _run_probe_script(tmp_path: Path, curl_script: str, **probe_env: str) -> str:
    curl_stub = tmp_path / "curl"
    curl_stub.write_text(curl_script)
    curl_stub.chmod(0o755)
    env = {
        "PATH": f"{tmp_path}:{os.environ.get('PATH', '/usr/bin:/bin')}",
        "HOME": str(tmp_path),
        "PROBE_PROJECT": str(tmp_path),
        "PROBE_PROJECT_WRITE": "0",
        "PROBE_EXPECT_GH": "0",
        "PROBE_NETWORK": "allowlist",
        **probe_env,
    }
    result = subprocess.run(
        ["bash", "-c", PROBE_SCRIPT],  # noqa: S607
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    return result.stdout


def test_probe_domain_classifies_connection_failure_as_unreachable(tmp_path: Path) -> None:
    # Regression: a real connection failure must not be folded into the
    # header capture and misread as "reachable" -- curl's own stderr (-S)
    # has to be discarded, and classification must gate on curl's exit code.
    curl_stub = "#!/bin/sh\necho 'curl: (7) Failed to connect' >&2\nexit 7\n"
    output = _run_probe_script(tmp_path, curl_stub, PROBE_ALLOWED_DOMAIN="allowed.example.com")
    assert "FAIL: allowed domain unreachable, expected reachable (allowed.example.com)" in output


def test_probe_domain_classifies_successful_response_as_reachable(tmp_path: Path) -> None:
    curl_stub = "#!/bin/sh\nprintf 'HTTP/1.1 200 OK\\r\\n\\r\\n'\nexit 0\n"
    output = _run_probe_script(tmp_path, curl_stub, PROBE_ALLOWED_DOMAIN="allowed.example.com")
    assert "PASS: allowed domain reachable (allowed.example.com)" in output


def test_probe_domain_classifies_proxy_denial_as_blocked(tmp_path: Path) -> None:
    curl_stub = (
        "#!/bin/sh\n"
        "printf 'HTTP/1.1 403 Forbidden\\r\\n"
        "X-Proxy-Error: blocked-by-sandbox-runtime\\r\\n\\r\\n'\n"
        "exit 0\n"
    )
    output = _run_probe_script(tmp_path, curl_stub, PROBE_DENIED_DOMAIN="denied.example.com")
    assert "PASS: denied domain blocked (denied.example.com)" in output
