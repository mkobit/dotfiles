from pathlib import Path

import pytest

from agent_sandbox.backend import BwrapBackend, SeatbeltBackend, select_backend
from agent_sandbox.bwrap import SandboxSpec


def test_select_auto_linux_returns_bwrap():
    assert isinstance(select_backend("auto", platform="linux"), BwrapBackend)


def test_select_auto_darwin_returns_seatbelt():
    assert isinstance(select_backend("auto", platform="darwin"), SeatbeltBackend)


def test_select_auto_unknown_platform_raises():
    with pytest.raises(ValueError, match="no auto backend"):
        select_backend("auto", platform="freebsd")


def test_select_explicit_bwrap_works_everywhere():
    assert isinstance(select_backend("bwrap", platform="darwin"), BwrapBackend)


def test_select_explicit_seatbelt_works_everywhere():
    assert isinstance(select_backend("seatbelt", platform="linux"), SeatbeltBackend)


def test_select_unknown_backend_raises():
    with pytest.raises(ValueError, match="unknown backend"):
        select_backend("docker", platform="linux")


def test_seatbelt_build_args_raises_not_implemented(tmp_path: Path):
    spec = SandboxSpec(
        home=tmp_path,
        project_root=tmp_path,
        project_write=True,
        profile_name="autonomous",
        cwd=tmp_path,
    )
    with pytest.raises(NotImplementedError, match="Seatbelt"):
        SeatbeltBackend().build_args(spec=spec, environ={})
