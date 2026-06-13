"""Sandbox backend dispatch.

A backend turns a SandboxSpec into an argv that runs the user's command in
an isolated environment. The Linux/WSL implementation uses bwrap; the macOS
path will use sandbox-exec + a Seatbelt profile (not implemented yet).
"""

from collections.abc import Mapping, Sequence
from typing import Protocol

from agent_sandbox.bwrap import SandboxSpec
from agent_sandbox.bwrap import build_args as _bwrap_build_args


class SandboxBackend(Protocol):
    name: str

    def build_args(
        self,
        spec: SandboxSpec,
        environ: Mapping[str, str],
        mask_paths: Sequence[str] = (),
    ) -> list[str]: ...


class BwrapBackend:
    name = "bwrap"

    def build_args(
        self,
        spec: SandboxSpec,
        environ: Mapping[str, str],
        mask_paths: Sequence[str] = (),
    ) -> list[str]:
        return _bwrap_build_args(spec, environ, mask_paths)


class SeatbeltBackend:
    """Stub: macOS sandbox-exec backend, not implemented in this pass.

    When implemented: render a .sb profile under
    ~/.config/ai-policy/seatbelt/<profile>.sb from sandbox.toml, then emit
    `sandbox-exec -p <profile-file> -- <command>`.
    """

    name = "seatbelt"

    def build_args(
        self,
        spec: SandboxSpec,
        environ: Mapping[str, str],
        mask_paths: Sequence[str] = (),
    ) -> list[str]:
        raise NotImplementedError("macOS Seatbelt backend not yet implemented; track this when first Mac use is needed")


def select_backend(backend_name: str, *, platform: str) -> SandboxBackend:
    """Map a profile's backend field + the current platform to a concrete backend."""
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
