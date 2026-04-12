from pathlib import Path

from claude_statusline.models import Segment, SegmentGenerationResult
from claude_statusline.segments.constants import BLUE, RESET, get_icon


def shorten_path(path: Path) -> str:
    """Shortens the path for display (e.g. ~/projects/foo -> .../projects/foo)."""
    try:
        rel_path = path.relative_to(Path.home())
        parts = list(rel_path.parts)
        if len(parts) > 3:
            return f".../{parts[-2]}/{parts[-1]}"
        if str(rel_path) == ".":
            return "~"
        return f"~/{rel_path}"
    except ValueError:
        parts = list(path.parts)
        if len(parts) > 3:
            return f".../{parts[-2]}/{parts[-1]}"
        return str(path)


def format_directory(cwd: Path) -> SegmentGenerationResult | None:
    display_path = shorten_path(cwd)
    cwd_link = f"\033]8;;file://{cwd}\033\\{display_path}\033]8;;\033\\"
    return SegmentGenerationResult(
        line=1,
        index=0,
        generator="internal.workspace",
        segment=Segment(text=f"{BLUE}{get_icon('dir')} {cwd_link}{RESET}"),
    )


def format_obsidian_vault(cwd: Path) -> SegmentGenerationResult | None:
    current = cwd
    while current != current.parent:
        if (current / ".obsidian").is_dir():
            vault_name = current.name
            return SegmentGenerationResult(
                line=1,
                index=10,
                generator="internal.workspace",
                segment=Segment(
                    text=f"{BLUE}{get_icon('obsidian')} {vault_name}{RESET}"
                ),
            )
        current = current.parent
    return None
