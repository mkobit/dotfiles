from typing import Final

from whenever import TimeDelta

_ANSI_ESCAPE_PATTERN: Final = r"(?:\x1b\[[0-9;]*m|\x1b]8;;.*?(?:\x1b\\|\x07))"
STATE_COLORS: Final = {
    "idle": "\033[2m",
    "thinking": "\033[36m",
    "working": "\033[34m",
    "tool_use": "\033[35m",
    "initializing": "\033[33m",
}
GIT_TIMEOUT: Final = TimeDelta(milliseconds=125)
_GIT_CLEANUP_RESERVE: Final = TimeDelta(milliseconds=10)
_GIT_CLEANUP_SCHEDULING_MARGIN: Final = TimeDelta(milliseconds=5)
GIT_STATUS_MAX_BYTES: Final = 64 * 1024
