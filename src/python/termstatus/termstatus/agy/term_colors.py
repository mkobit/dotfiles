import math
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from termstatus.segments.constants import (
    AMBER,
    CYAN,
    DIM,
    GREEN,
    MAGENTA,
    ORANGE,
    RED,
    RESET,
    YELLOW,
    use_icons,
)

SEPARATOR: Final[str] = f" {DIM}•{RESET} "

_STATE_COLORS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "idle": DIM,
        "thinking": CYAN,
        "working": AMBER,
        "tool_use": MAGENTA,
        "initializing": YELLOW,
    }
)

_STATE_ICONS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "idle": ("", ""),
        "thinking": ("🧠", "🧠"),
        "working": ("🔄", "🔄"),
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
        if remaining_pct >= 40:
            return YELLOW
        if remaining_pct >= 15:
            return ORANGE
        return RED
    except TypeError, ValueError:
        return RED


_ICONS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "dir": ("📁", "📁"),
        "branch": ("\ue0a0", "🪾"),
        "detached": ("➦", "➦"),
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


_FULLNESS_THRESHOLDS: Final[tuple[tuple[float, str], ...]] = (
    (75.0, "●"),
    (50.0, "◕"),
    (25.0, "◑"),
    (5.0, "◔"),
)


def fullness_icon(remaining_pct: float) -> str:
    try:
        if not math.isfinite(remaining_pct):
            return _FULLNESS_ICONS_UTF8[0]
        for threshold, icon in _FULLNESS_THRESHOLDS:
            if remaining_pct >= threshold:
                return icon
        return _FULLNESS_ICONS_UTF8[0]
    except TypeError, ValueError:
        return _FULLNESS_ICONS_UTF8[0]


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
