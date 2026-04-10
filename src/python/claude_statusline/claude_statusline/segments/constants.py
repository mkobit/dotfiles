import functools
import os
from dataclasses import dataclass
from typing import Literal

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

ICONS: dict[IconKey, tuple[str, str]] = {
    # key: (nerdfont, emoji)
    "dir": ("\uf115", "📁"),
    "branch": ("\ue0a0", "🪾"),
    "remote": ("\uf0c1", "🔗"),
    "dirty": ("\uf06a", "!"),
    "clean": ("\uf00c", "✓"),
    "staged": ("\uf067", "+"),
    "untracked": ("\uf128", "?"),
    "timer": ("\uf017", "⏱"),
    "cost": ("💳", "💳"),
    "tokens": ("\uf4a5", "⚡"),
    "robot": ("\uf544", "🤖"),
    "worktree": ("\uf1bb", "🌳"),
    "obsidian": ("\ue65d", "🟣"),
}


def get_icon(key: IconKey) -> str:
    """Returns the nerd font icon or emoji fallback based on environment."""
    nerd_font, fallback = ICONS[key]
    return nerd_font if use_icons() else fallback


BLOCK_FILLED = "\u2588"  # █
BLOCK_EMPTY = "\u2591"  # ░
DIVIDER_DOT = " • "
DIVIDER_BAR = " │ "


@dataclass
class Segment:
    text: str
