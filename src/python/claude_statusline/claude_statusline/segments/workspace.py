from pathlib import Path

from claude_statusline.models import Segment, SegmentGenerationResult
from claude_statusline.segments.constants import BLUE, RESET, get_icon


def shorten_path(path: Path) -> str:
    """Returns just the basename of the path for display."""
    if str(path) == "/":
        return "/"
    return path.name


def format_directory(cwd: Path) -> SegmentGenerationResult | None:
    display_path = shorten_path(cwd)
    cwd_link = f"\033]8;;file://{cwd}\033\\{display_path}\033]8;;\033\\"
    return SegmentGenerationResult(
        line=0,
        index=5,
        generator="internal.workspace",
        segment=Segment(text=f"{BLUE}{get_icon('dir')} {cwd_link}{RESET}"),
    )


def format_obsidian_vault(cwd: Path) -> SegmentGenerationResult | None:
    current = cwd
    while current != current.parent:
        if (current / ".obsidian").is_dir():
            vault_name = current.name
            return SegmentGenerationResult(
                line=0,
                index=40,
                generator="internal.workspace",
                segment=Segment(
                    text=f"{BLUE}{get_icon('obsidian')} {vault_name}{RESET}"
                ),
            )
        current = current.parent
    return None
