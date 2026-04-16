import functools
import os
from typing import Literal, NamedTuple


class IconPair(NamedTuple):
    nerd_font: str
    fallback: str


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
ORANGE = "\033[38;5;208m"

BG_DIM = "\033[48;5;236m"
BG_RESET = "\033[49m"


@functools.cache
def use_icons() -> bool:
    """Returns True if the terminal supports icons, checking environment."""
    return os.environ.get("CLAUDE_STATUSLINE_NO_ICONS", "0") != "1"


IconKey = Literal[
    "dir",
    "branch",
    "remote",
    "github",
    "gitlab",
    "dirty",
    "clean",
    "staged",
    "untracked",
    "stash",
    "timer",
    "dot",
    "cost",
    "tokens",
    "robot",
    "worktree",
    "obsidian",
]

ICONS: dict[IconKey, IconPair] = {
    # key: (nerdfont, emoji)
    "dir": IconPair("\uf115", "📁"),
    "branch": IconPair("\ue0a0", "🪾"),
    "remote": IconPair("\uf0c1", "🔗"),
    "github": IconPair("\ue709", ""),
    "gitlab": IconPair("\uf296", ""),
    "dirty": IconPair("\uf06a", "!"),
    "clean": IconPair("\uf00c", "✓"),
    "staged": IconPair("\uf067", "+"),
    "untracked": IconPair("\uf128", "?"),
    "stash": IconPair("\uf01c", "$"),
    "timer": IconPair("\U000F0954", "⏱"),
    "dot": IconPair("\uf444", "·"),
    "cost": IconPair("💳", "💳"),
    "tokens": IconPair("\uf4a5", "⚡"),
    "robot": IconPair("\uf544", "🤖"),
    "worktree": IconPair("\uf1bb", "🌳"),
    "obsidian": IconPair("\ue65d", "🟣"),
}


def get_icon(key: IconKey) -> str:
    """Returns the nerd font icon or emoji fallback based on environment."""
    icon_pair = ICONS[key]
    return icon_pair.nerd_font if use_icons() else icon_pair.fallback


DIVIDER_DOT = " • "
DIVIDER_BAR = " │ "

# nf-md-battery_* icons (remaining context, 10% increments)
# U+F0079 = nf-md-battery (100%), U+F008E = nf-md-battery_outline (0%)
_BATTERY_ICONS_NERD = [
    "\U000F008E",  # 0%  — outline/empty
    "\U000F007A",  # 10%
    "\U000F007B",  # 20%
    "\U000F007C",  # 30%
    "\U000F007D",  # 40%
    "\U000F007E",  # 50%
    "\U000F007F",  # 60%
    "\U000F0080",  # 70%
    "\U000F0081",  # 80%
    "\U000F0082",  # 90%
    "\U000F0079",  # 100% — full
]
_BATTERY_ICONS_FALLBACK = ["_", "1", "2", "3", "4", "5", "6", "7", "8", "9", "#"]


def get_battery_icon(remaining_pct: float) -> str:
    """Returns the battery icon for the given remaining percentage (0-100)."""
    index = round(max(0.0, min(100.0, remaining_pct)) / 10)
    icons = _BATTERY_ICONS_NERD if use_icons() else _BATTERY_ICONS_FALLBACK
    return icons[index]
