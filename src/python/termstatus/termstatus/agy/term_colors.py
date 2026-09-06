import math
import os
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

RESET: Final[str] = "\033[0m"
BOLD: Final[str] = "\033[1m"
DIM: Final[str] = "\033[2m"

RED: Final[str] = "\033[31m"
GREEN: Final[str] = "\033[32m"
YELLOW: Final[str] = "\033[33m"
BLUE: Final[str] = "\033[34m"
MAGENTA: Final[str] = "\033[35m"
CYAN: Final[str] = "\033[36m"
WHITE: Final[str] = "\033[37m"

BRIGHT_GREEN: Final[str] = "\033[92m"
ORANGE: Final[str] = "\033[38;5;208m"
AMBER: Final[str] = "\033[38;5;214m"
SKY_BLUE: Final[str] = "\033[38;5;75m"

SEPARATOR: Final[str] = f" {DIM}•{RESET} "

_STATE_COLORS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "idle": "\033[2m",
        "thinking": "\033[36m",
        "working": "\033[38;5;214m",
        "tool_use": "\033[35m",
        "initializing": "\033[33m",
    }
)

_STATE_ICONS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "idle": ("", ""),
        "thinking": ("💭", "💭"),
        "working": ("⚡", "⚡"),
        "tool_use": ("🔧", "🔧"),
        "initializing": ("⏳", "⏳"),
    }
)


def meter_color(remaining_pct: float) -> str:
    try:
        if not math.isfinite(remaining_pct):
            return RED
        if remaining_pct >= 70:
            return GREEN
        if remaining_pct >= 30:
            return YELLOW
        return RED
    except TypeError, ValueError:
        return RED


def use_icons() -> bool:
    return (
        os.environ.get("CLAUDE_STATUSLINE_NO_ICONS", "0") != "1" and os.environ.get("TERMSTATUS_NO_ICONS", "0") != "1"
    )


_ICONS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "dir": ("📁", "📁"),
        "branch": ("\ue0a0", "🪾"),
        "remote": ("\uf0c1", "🔗"),
        "github": ("\ue709", "🔗"),
        "dirty": ("!", "!"),
        "clean": ("✓", "✓"),
        "tokens": ("\uf4a5", "⚡"),
        "cost": ("💳", "💳"),
    }
)

_FULLNESS_ICONS_UTF8: Final[tuple[str, ...]] = (
    "○",  # 0%
    "◔",  # 25%
    "◑",  # 50%
    "◕",  # 75%
    "●",  # 100%
)


def fullness_icon(remaining_pct: float) -> str:
    try:
        if not math.isfinite(remaining_pct):
            return _FULLNESS_ICONS_UTF8[0]
        clamped = max(0.0, min(100.0, remaining_pct))
        index = round(clamped / 100 * 4)
        return _FULLNESS_ICONS_UTF8[index]
    except TypeError, ValueError:
        return _FULLNESS_ICONS_UTF8[0]


moon_icon = fullness_icon


def get_icon(key: str) -> str:
    if key in _ICONS:
        pair = _ICONS[key]
        return pair[0] if use_icons() else pair[1]
    return ""


def state_icon(state: str) -> str:
    if not use_icons():
        return ""
    if pair := _STATE_ICONS.get(state):
        return pair[0] if pair[0] else pair[1]
    return ""
