import os
import re
import subprocess
import sys
import tempfile

import typer

app = typer.Typer(help="Zellij subcommands")


@app.command("open-url")
def open_url(
    open_cmd: str | None = typer.Option(
        None,
        "--open-cmd",
        help="Command to use to open the URL. Defaults to guessing based on OS.",
    ),
) -> None:
    """Open a URL from the current Zellij pane's scrollback."""
    # Dump Zellij screen to a temporary file
    with tempfile.NamedTemporaryFile(
        mode="w+", delete=False, suffix=".txt"
    ) as temp_file:
        temp_file_path = temp_file.name

    try:
        subprocess.run(
            ["zellij", "action", "dump-screen", temp_file_path],
            check=True,
        )
        with open(temp_file_path, encoding="utf-8") as f:
            scrollback = f.read()
    except subprocess.CalledProcessError:
        print("Failed to capture Zellij pane", file=sys.stderr)
        os.remove(temp_file_path)
        sys.exit(1)
    except FileNotFoundError:
        print(
            "Zellij command not found. Are you running inside Zellij?", file=sys.stderr
        )
        os.remove(temp_file_path)
        sys.exit(1)
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    url_pattern = re.compile(
        r"[a-zA-Z][a-zA-Z0-9+.-]*://[a-zA-Z0-9_.~!*'();:@&=+$,/?%#-]+"
    )
    urls = url_pattern.findall(scrollback)

    if not urls:
        print("No URLs found.", file=sys.stderr)
        sys.exit(0)

    seen: set[str] = set()
    ordered_urls: list[str] = []
    for url in reversed(urls):
        if url not in seen:
            seen.add(url)
            ordered_urls.append(url)

    try:
        fzf = subprocess.Popen(
            ["fzf", "--prompt=Open URL: "],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        selected_url_bytes, _ = fzf.communicate(input="\n".join(ordered_urls))
        selected_url = selected_url_bytes.strip()
    except FileNotFoundError:
        print("fzf not found.", file=sys.stderr)
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
        print(f"Failed to execute {open_cmd}", file=sys.stderr)
        sys.exit(1)
