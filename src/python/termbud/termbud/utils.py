import os
import shutil
import sys


def platform_cmds() -> tuple[str, str]:
    if sys.platform == "darwin":
        return "open", "pbcopy"
    if "microsoft" in os.uname().release.lower():
        return "wslview", "clip.exe"
    if os.environ.get("WAYLAND_DISPLAY") or shutil.which("wl-copy"):
        return "xdg-open", "wl-copy"
    return "xdg-open", "xclip -selection clipboard"


def editor_cmd() -> str:
    return os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nvim"
