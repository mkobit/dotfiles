from dataclasses import dataclass

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

USE_ICONS = True
ICON_DIR = "\uf115" if USE_ICONS else "📁"
ICON_BRANCH = "\ue0a0" if USE_ICONS else ""
ICON_REMOTE = "\uf0c1" if USE_ICONS else "🔗"
ICON_DIRTY = "\uf06a" if USE_ICONS else "!"
ICON_CLEAN = "\uf00c" if USE_ICONS else "✓"
ICON_STAGED = "\uf067" if USE_ICONS else "+"
ICON_UNTRACKED = "\uf128" if USE_ICONS else "?"
ICON_TIMER = "\uf017" if USE_ICONS else "⏱"
ICON_COST = "💳" if USE_ICONS else "💳"
ICON_TOKENS = "\uf4a5" if USE_ICONS else "⚡"
ICON_ROBOT = "\uf544" if USE_ICONS else "🤖"
ICON_WORKTREE = "\uf1bb" if USE_ICONS else "🌳"

BLOCK_FILLED = "\u2588"  # █
BLOCK_EMPTY = "\u2591"  # ░
DIVIDER_DOT = " • "
DIVIDER_BAR = " │ "


@dataclass
class Segment:
    text: str
