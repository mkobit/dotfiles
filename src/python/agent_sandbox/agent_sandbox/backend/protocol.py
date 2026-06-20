from collections.abc import Mapping, Sequence
from typing import Protocol

from agent_sandbox.sandbox.spec import SandboxSpec


class SandboxBackend(Protocol):
    name: str

    def build_args(
        self,
        spec: SandboxSpec,
        environ: Mapping[str, str],
        mask_paths: Sequence[str] = (),
    ) -> list[str]: ...


def select_backend(backend_name: str, *, platform: str) -> SandboxBackend:
    """Map a profile backend field + current platform to a concrete backend."""
    from agent_sandbox.backend.bwrap import BwrapBackend
    from agent_sandbox.backend.seatbelt import SeatbeltBackend

    if backend_name == "auto":
        if platform.startswith("linux"):
            return BwrapBackend()
        if platform == "darwin":
            return SeatbeltBackend()
        raise ValueError(f"no auto backend for platform {platform!r}")
    if backend_name == "bwrap":
        return BwrapBackend()
    if backend_name == "seatbelt":
        return SeatbeltBackend()
    raise ValueError(f"unknown backend {backend_name!r}")
