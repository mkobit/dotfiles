"""macOS sandbox-exec (Seatbelt) backend stub.

When implemented: render a .sb profile under
~/.config/ai-policy/seatbelt/<profile>.sb from sandbox.toml data,
then emit `sandbox-exec -p <profile-file> -- <command>`.
"""

from collections.abc import Mapping, Sequence

from agent_sandbox.sandbox.spec import SandboxSpec


class SeatbeltBackend:
    name = "seatbelt"

    def build_args(
        self,
        spec: SandboxSpec,
        environ: Mapping[str, str],
        mask_paths: Sequence[str] = (),
    ) -> list[str]:
        raise NotImplementedError(
            "macOS Seatbelt backend not yet implemented; track this when first Mac use is needed"
        )
