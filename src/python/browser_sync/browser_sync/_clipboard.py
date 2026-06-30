"""macOS clipboard access via pbcopy."""

import subprocess


def copy_to_clipboard(text: str) -> None:
    """Copy text to the macOS clipboard."""
    subprocess.run(["pbcopy"], input=text.encode(), check=True)
