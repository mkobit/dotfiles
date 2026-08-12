from pathlib import Path

from sandboxr.cli.doctor import _probe_env
from sandboxr.sandbox.spec import SandboxSpec


def spec_for(*, network: str = "shared") -> SandboxSpec:
    return SandboxSpec(
        home=Path("/home/test"),
        project_root=Path("/home/test/project"),
        project_write=True,
        cwd=Path("/home/test/project"),
        network=network,
    )


def test_probe_env_includes_project_and_network() -> None:
    env = _probe_env(spec_for())
    assert env["PROBE_PROJECT"] == "/home/test/project"
    assert env["PROBE_PROJECT_WRITE"] == "1"
    assert env["PROBE_NETWORK"] == "shared"


def test_probe_env_for_airgapped() -> None:
    env = _probe_env(spec_for(network="none"))
    assert env["PROBE_NETWORK"] == "none"
