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
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as temp_file:
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
        print("Zellij command not found. Are you running inside Zellij?", file=sys.stderr)
        os.remove(temp_file_path)
        sys.exit(1)
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    url_pattern = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[a-zA-Z0-9_.~!*'();:@&=+$,/?%#-]+")
    urls = url_pattern.findall(scrollback)

    if not urls:
        print("No URLs found.", file=sys.stderr)
        sys.exit(0)

    ordered_urls = list(dict.fromkeys(reversed(urls)))

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as urls_file:
        urls_file.write("\n".join(ordered_urls))
        urls_file_name = urls_file.name

    if sys.platform == "darwin":
        default_open_cmd = "open"
        copy_cmd = "pbcopy"
    elif "microsoft" in os.uname().release.lower():
        default_open_cmd = "wslview"
        copy_cmd = "clip.exe"
    else:
        default_open_cmd = "xdg-open"
        copy_cmd = "xclip -selection clipboard"

    open_cmd = open_cmd or default_open_cmd

    fzf_env = os.environ.copy()
    fzf_env["FZF_DEFAULT_COMMAND"] = f"cat {urls_file_name}"

    fzf_args = [
        "fzf",
        "--prompt=Open URL: ",
        "--bind",
        f"enter:execute-silent({open_cmd} {{}})+abort",
        "--bind",
        f"ctrl-c:execute-silent(echo -n {{}} | {copy_cmd})+abort",
    ]

    try:
        os.execvpe("fzf", fzf_args, fzf_env)
    except OSError:
        print("Failed to execute fzf", file=sys.stderr)
        os.remove(urls_file_name)
        sys.exit(1)
