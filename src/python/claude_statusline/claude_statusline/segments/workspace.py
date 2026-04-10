from pathlib import Path

from claude_statusline.segments.constants import BLUE, RESET, Segment, get_icon


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


def format_directory(cwd: Path) -> Segment | None:
    display_path = shorten_path(cwd)
    cwd_link = f"\033]8;;file://{cwd}\033\\{display_path}\033]8;;\033\\"
    return Segment(f"{BLUE}{get_icon('dir')} {cwd_link}{RESET}")
