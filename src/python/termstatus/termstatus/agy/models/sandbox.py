from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SandboxState:
    enabled: bool
    allow_network: bool
