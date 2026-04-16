import os
import re
import subprocess
import sys

import typer

app = typer.Typer(help="Tmux subcommands")


@app.command("open-url")
def open_url(
    pane_id: str = typer.Option(..., "--pane-id", help="The tmux pane ID to capture"),
    open_cmd: str | None = typer.Option(
        None,
        "--open-cmd",
        help="Command to use to open the URL. Defaults to guessing based on OS.",
    ),
) -> None:
    """Open a URL from a tmux pane's scrollback."""
    try:
        result = subprocess.run(
            ["tmux", "capture-pane", "-J", "-S", "-", "-t", pane_id, "-p"],
            capture_output=True,
            text=True,
            check=True,
        )
        scrollback = result.stdout
    except subprocess.CalledProcessError:
        subprocess.run(
            ["tmux", "display-message", "Failed to capture pane"], check=False
        )
        sys.exit(1)

    url_pattern = re.compile(
        r"[a-zA-Z][a-zA-Z0-9+.-]*://[a-zA-Z0-9_.~!*'();:@&=+$,/?%#-]+"
    )
    urls = url_pattern.findall(scrollback)

    if not urls:
        subprocess.run(["tmux", "display-message", "No URLs found."], check=False)
        sys.exit(0)

    seen: set[str] = set()
    ordered_urls: list[str] = []
    for url in reversed(urls):
        if url not in seen:
            seen.add(url)
            ordered_urls.append(url)

    try:
        fzf = subprocess.Popen(
            ["fzf-tmux", "-p", "80%,80%", "--prompt=Open URL: "],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        selected_url_bytes, _ = fzf.communicate(input="\n".join(ordered_urls))
        selected_url = selected_url_bytes.strip()
    except FileNotFoundError:
        subprocess.run(["tmux", "display-message", "fzf-tmux not found."], check=False)
        sys.exit(1)

    if not selected_url:
        sys.exit(0)

    if not open_cmd:
        if sys.platform == "darwin":
            open_cmd = "open"
        elif "microsoft" in os.uname().release.lower():
            open_cmd = "wslview"
        else:
            open_cmd = "xdg-open"

    try:
        os.execvp(open_cmd, [open_cmd, selected_url])
    except OSError:
        subprocess.run(
            ["tmux", "display-message", f"Failed to execute {open_cmd}"], check=False
        )
        sys.exit(1)
