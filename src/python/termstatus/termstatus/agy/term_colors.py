from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

_STATE_COLORS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "idle": "\033[2m",
        "thinking": "\033[36m",
        "working": "\033[34m",
        "tool_use": "\033[35m",
        "initializing": "\033[33m",
    }
)
