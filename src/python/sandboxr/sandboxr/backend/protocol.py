from collections.abc import Mapping, Sequence
from typing import Protocol

from sandboxr.sandbox.spec import SandboxSpec


class SandboxBackend(Protocol):
    name: str

    def build_args(
        self,
        spec: SandboxSpec,
        environ: Mapping[str, str],
        mask_paths: Sequence[str] = (),
    ) -> list[str]: ...

    def wrap_command(self, cmd: Sequence[str]) -> Sequence[str]: ...
