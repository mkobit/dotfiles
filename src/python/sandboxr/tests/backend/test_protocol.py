from pathlib import Path

import pytest

from sandboxr.backend.bwrap import BwrapBackend
from sandboxr.backend.protocol import select_backend
from sandboxr.backend.seatbelt import SeatbeltBackend
from sandboxr.backend.srt import SrtBackend
from sandboxr.sandbox.spec import SandboxSpec


def test_select_auto_linux_returns_bwrap() -> None:
    assert isinstance(select_backend("auto", platform="linux"), BwrapBackend)


def test_select_auto_darwin_returns_seatbelt() -> None:
    assert isinstance(select_backend("auto", platform="darwin"), SeatbeltBackend)


def test_select_auto_unknown_platform_raises() -> None:
    with pytest.raises(ValueError, match="no auto backend"):
        select_backend("auto", platform="freebsd")


def test_select_explicit_bwrap_works_everywhere() -> None:
    assert isinstance(select_backend("bwrap", platform="darwin"), BwrapBackend)


def test_select_explicit_seatbelt_works_everywhere() -> None:
    assert isinstance(select_backend("seatbelt", platform="linux"), SeatbeltBackend)


def test_select_explicit_srt_works_everywhere() -> None:
    assert isinstance(select_backend("srt", platform="linux"), SrtBackend)


def test_select_auto_never_returns_srt() -> None:
    # srt is opt-in only for now (see plan scope decision #1); "auto" keeps
    # resolving to the existing per-platform default until srt passes
    # acceptance.
    assert not isinstance(select_backend("auto", platform="linux"), SrtBackend)


def test_select_unknown_backend_raises() -> None:
    with pytest.raises(ValueError, match="unknown backend"):
        select_backend("docker", platform="linux")


def test_seatbelt_build_args_raises_not_implemented(tmp_path: Path) -> None:
    spec = SandboxSpec(
        home=tmp_path,
        project_root=tmp_path,
        project_write=True,
        profile_name="autonomous",
        cwd=tmp_path,
    )
    with pytest.raises(NotImplementedError, match="Seatbelt"):
        SeatbeltBackend().build_args(spec=spec, environ={})


def test_seatbelt_wrap_command_is_identity() -> None:
    cmd = ["claude", "--dangerously-skip-permissions"]
    assert SeatbeltBackend().wrap_command(cmd) == cmd
