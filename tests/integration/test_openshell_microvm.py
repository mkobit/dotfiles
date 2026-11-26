"""Chezmoi integration for the OpenShell MicroVM gateway."""

import json
import os
import shutil
import subprocess
import tomllib
from pathlib import Path
from stat import S_IMODE

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHEZMOI_SOURCE = REPO_ROOT / "src" / "chezmoi"
BINS_EXTERNAL_TEMPLATE = CHEZMOI_SOURCE / "dot_local/bin/.chezmoiexternals/bins.toml.tmpl"
MICROVM_TARGETS = {
    ".config/openshell/microvm-gateway.toml",
    ".config/systemd/user/openshell-microvm.service",
}
MICROVM_BINARIES = {
    "openshell-gateway": "c32085d64ccef037121c0e87bee1a57d6e886d77f77bb8b260cb08f0a6cce6a3",
    "openshell-driver-vm": "87bd26e5f49acdc4c6165aa463ad3964c40d5ef066125f99956f7e8eea0a0f65",
}
WSL_KERNEL = "5.15.0-microsoft-standard-WSL2"
LINUX_KERNEL = "6.12.0-generic"


def _chezmoi(
    destination: Path,
    *args: str,
    source: Path = REPO_ROOT,
    path: str = os.defpath,
) -> str:
    chezmoi = shutil.which("chezmoi")
    assert chezmoi is not None
    result = subprocess.run(
        [
            chezmoi,
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(source),
            "--no-tty",
            "--destination",
            str(destination),
            *args,
        ],
        env={**os.environ, "CI": "1", "PATH": path},
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _platform(system: str, arch: str, osrelease: str) -> dict[str, object]:
    return {"os": system, "arch": arch, "kernel": {"osrelease": osrelease}}


@pytest.mark.parametrize(
    ("system", "arch", "osrelease", "has_wslpath", "enabled"),
    [
        pytest.param("linux", "amd64", WSL_KERNEL, True, True, id="wsl2-amd64"),
        pytest.param("linux", "arm64", WSL_KERNEL, True, False, id="wsl2-arm64"),
        pytest.param("linux", "amd64", "4.4.0-19041-Microsoft", True, False, id="wsl1-amd64"),
        pytest.param("linux", "amd64", WSL_KERNEL, False, False, id="wsl2-without-wslpath"),
        pytest.param("linux", "amd64", LINUX_KERNEL, True, False, id="native-linux"),
        pytest.param("darwin", "arm64", "", True, False, id="macos"),
    ],
)
def test_init_selects_microvm_on_wsl2_amd64(
    tmp_path: Path, system: str, arch: str, osrelease: str, *, has_wslpath: bool, enabled: bool
) -> None:
    stubs = {"sw_vers": "15.7.1"}
    if has_wslpath:
        stubs["wslpath"] = "/mnt/c/Users/example"
    for name, output in stubs.items():
        stub = tmp_path / name
        stub.write_text(f"#!/bin/sh\nprintf '%s\\n' '{output}'\n", encoding="utf-8")
        stub.chmod(0o755)

    rendered = _chezmoi(
        tmp_path,
        "execute-template",
        "--init",
        "--override-data",
        json.dumps({"chezmoi": _platform(system, arch, osrelease)}),
        "--file",
        str(CHEZMOI_SOURCE / ".chezmoi.toml.tmpl"),
        path=str(tmp_path),
    )
    assert tomllib.loads(rendered)["data"]["local"]["bin"]["openshell"].get("microvm", False) is enabled


MICROVM_CASES = [
    pytest.param(
        ("amd64", WSL_KERNEL, {"installation_method": "github_releases", "microvm": True}, True),
        id="enabled",
    ),
    pytest.param(
        ("amd64", WSL_KERNEL, {"installation_method": "github_releases", "microvm": False}, False),
        id="disabled",
    ),
    pytest.param(
        ("amd64", WSL_KERNEL, {"installation_method": "github_releases"}, False),
        id="missing-option",
    ),
    pytest.param(
        ("amd64", WSL_KERNEL, {"installation_method": "none", "microvm": True}, False),
        id="parent-disabled",
    ),
    pytest.param(
        ("arm64", WSL_KERNEL, {"installation_method": "github_releases", "microvm": True}, False),
        id="unsupported-architecture",
    ),
    pytest.param(
        ("amd64", LINUX_KERNEL, {"installation_method": "github_releases", "microvm": True}, True),
        id="native-linux",
    ),
]


@pytest.fixture(params=MICROVM_CASES)
def microvm_case(request: pytest.FixtureRequest) -> tuple[str, bool]:
    arch, osrelease, openshell, enabled = request.param
    override = json.dumps(
        {
            "chezmoi": _platform("linux", arch, osrelease),
            "local": {"bin": {"openshell": openshell}},
        }
    )
    return override, enabled


def test_microvm_binary_downloads(
    tmp_path: Path,
    microvm_case: tuple[str, bool],
) -> None:
    override, enabled = microvm_case
    externals = tomllib.loads(
        _chezmoi(
            tmp_path,
            "execute-template",
            "--override-data",
            override,
            "--file",
            str(BINS_EXTERNAL_TEMPLATE),
        )
    )
    assert MICROVM_BINARIES.keys() & externals.keys() == (MICROVM_BINARIES.keys() if enabled else set())
    if enabled:
        for name, checksum in MICROVM_BINARIES.items():
            entry = externals[name]
            assert entry["type"] == "archive-file"
            assert entry["executable"] is True
            assert entry["path"] == name
            assert entry["url"].endswith(f"/v0.1.9/{name}-x86_64-unknown-linux-gnu.tar.gz")
            assert entry["checksum"]["sha256"] == checksum


def test_microvm_managed_targets(tmp_path: Path, microvm_case: tuple[str, bool]) -> None:
    override, enabled = microvm_case
    source = tmp_path / "source"
    # Keep the local source entries and skip unrelated external downloads.
    shutil.copytree(CHEZMOI_SOURCE, source, ignore=shutil.ignore_patterns(".chezmoiexternals"))
    managed = _chezmoi(tmp_path, "managed", "--override-data", override, source=source).splitlines()
    assert MICROVM_TARGETS.intersection(managed) == (MICROVM_TARGETS if enabled else set())

    config_dir = tmp_path / ".config/openshell"
    config_dir.mkdir(mode=0o700, parents=True)
    gateway = config_dir / "gateways" / "test-gateway"
    gateway.parent.mkdir()
    gateway.write_text("OpenShell gateway state", encoding="utf-8")
    _chezmoi(
        tmp_path,
        "apply",
        "--persistent-state",
        str(tmp_path / "chezmoistate.boltdb"),
        "--exclude",
        "scripts",
        "--override-data",
        override,
        str(config_dir),
        source=source,
    )
    assert S_IMODE(config_dir.stat().st_mode) == 0o700
    assert gateway.read_text(encoding="utf-8") == "OpenShell gateway state"

    if enabled:
        config = tomllib.loads(
            _chezmoi(
                tmp_path,
                "cat",
                "--override-data",
                override,
                str(tmp_path / ".config/openshell/microvm-gateway.toml"),
                source=source,
            )
        )["openshell"]
        state_dir = tmp_path / ".local/state/openshell-microvm"
        assert config["gateway"]["bind_address"] == "127.0.0.1:17671"
        assert config["gateway"]["compute_driver"] == "vm"
        assert config["gateway"]["guest_tls_ca"] == str(state_dir / "tls/ca.crt")
        assert config["drivers"]["vm"]["state_dir"] == str(state_dir / "vm")
        assert config["drivers"]["vm"]["driver_dir"] == str(tmp_path / ".local/bin")
        assert config["drivers"]["vm"]["default_image"] == (
            "nvcr.io/nvidia/base/ubuntu@sha256:494398fac1b07614c63ba179e3558d84a5a9ce19a6374560ceac04d822462e45"
        )
        assert config["drivers"]["vm"]["bootstrap_image"] == config["drivers"]["vm"]["default_image"]


def test_microvm_service_uses_quoted_destination_paths(tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(CHEZMOI_SOURCE, source, ignore=shutil.ignore_patterns(".chezmoiexternals"))
    destination = tmp_path / "home with 100%"
    destination.mkdir()
    unit = _chezmoi(
        destination,
        "cat",
        "--override-data",
        json.dumps(
            {
                "chezmoi": _platform("linux", "amd64", WSL_KERNEL),
                "local": {"bin": {"openshell": {"installation_method": "github_releases", "microvm": True}}},
            }
        ),
        str(destination / ".config/systemd/user/openshell-microvm.service"),
        source=source,
    ).splitlines()
    home = tmp_path / "home with 100%%"
    gateway = f'":{home}/.local/bin/openshell-gateway"'
    tls_dir = home / ".local/state/openshell-microvm/tls"
    config = home / ".config/openshell/microvm-gateway.toml"
    assert f'Environment="OPENSHELL_LOCAL_TLS_DIR={tls_dir}"' in unit
    assert any(line.startswith(f'ExecStartPre={gateway} generate-certs --output-dir "{tls_dir}" ') for line in unit)
    assert f'ExecStart={gateway} --config "{config}" --health-port 0' in unit
