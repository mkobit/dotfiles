import pytest

from sandboxr.backend.bwrap import BwrapBackend
from sandboxr.backend.protocol import select_backend
from sandboxr.backend.srt import SrtBackend


def test_select_auto_linux_returns_bwrap() -> None:
    assert isinstance(select_backend("auto", platform="linux"), BwrapBackend)


def test_select_auto_darwin_raises() -> None:
    with pytest.raises(ValueError, match="no auto backend"):
        select_backend("auto", platform="darwin")


def test_select_auto_unknown_platform_raises() -> None:
    with pytest.raises(ValueError, match="no auto backend"):
        select_backend("auto", platform="freebsd")


def test_select_explicit_bwrap_works_everywhere() -> None:
    assert isinstance(select_backend("bwrap", platform="darwin"), BwrapBackend)


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
