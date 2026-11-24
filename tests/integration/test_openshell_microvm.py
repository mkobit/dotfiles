"""Chezmoi integration for the OpenShell MicroVM gateway."""

import json
import os
import shutil
import subprocess
import tomllib
from pathlib import Path

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
        env={**os.environ, "CI": "1", "PATH": f"{destination}:{os.defpath}"},
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
    ("system", "arch", "osrelease", "enabled"),
    [
        pytest.param("linux", "amd64", WSL_KERNEL, True, id="wsl-amd64"),
        pytest.param("linux", "arm64", WSL_KERNEL, False, id="wsl-arm64"),
        pytest.param("linux", "amd64", LINUX_KERNEL, False, id="native-linux"),
        pytest.param("darwin", "arm64", "", False, id="macos"),
    ],
)
def test_init_selects_microvm_on_wsl_amd64(
    tmp_path: Path, system: str, arch: str, osrelease: str, *, enabled: bool
) -> None:
    for name, output in (("sw_vers", "15.7.1"), ("wslpath", "/mnt/c/Users/example")):
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
        assert config["drivers"]["vm"]["default_image"] == "nvcr.io/nvidia/base/ubuntu:24.04"
