from pathlib import Path

from sandboxr.cli.doctor import _probe_env
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
