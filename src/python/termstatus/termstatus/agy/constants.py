from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from whenever import TimeDelta

_ANSI_ESCAPE_PATTERN: Final = r"(?:\x1b\[[0-9;]*m|\x1b]8;;.*?(?:\x1b\\|\x07))"
_STATE_COLORS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "idle": "\033[2m",
        "thinking": "\033[36m",
        "working": "\033[34m",
        "tool_use": "\033[35m",
        "initializing": "\033[33m",
    }
)
_GIT_TIMEOUT: Final[TimeDelta] = TimeDelta(milliseconds=125)
_GIT_CLEANUP_RESERVE: Final[TimeDelta] = TimeDelta(milliseconds=10)
_GIT_CLEANUP_SCHEDULING_MARGIN: Final[TimeDelta] = TimeDelta(milliseconds=5)
_GIT_STATUS_MAX_BYTES: Final[int] = 64 * 1024
