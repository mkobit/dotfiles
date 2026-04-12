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


@functools.cache
def use_icons() -> bool:
    """Returns True if the terminal supports icons, checking environment."""
    if os.environ.get("CLAUDE_STATUSLINE_NO_ICONS", "0") == "1":
        return False
    return True


IconKey = Literal[
    "dir",
    "branch",
    "remote",
    "dirty",
    "clean",
    "staged",
    "untracked",
    "timer",
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
    "dirty": IconPair("\uf06a", "!"),
    "clean": IconPair("\uf00c", "✓"),
    "staged": IconPair("\uf067", "+"),
    "untracked": IconPair("\uf128", "?"),
    "timer": IconPair("\uf017", "⏱"),
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


BLOCK_FILLED = "\u2588"  # █
BLOCK_EMPTY = "\u2591"  # ░
DIVIDER_DOT = " • "
DIVIDER_BAR = " │ "
