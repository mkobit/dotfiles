import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import typer

app = typer.Typer(help="Zellij subcommands")

_URL_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[a-zA-Z0-9_.~!*'();:@&=+$,/?%#-]+")

_BUILTIN_PATTERNS: list[dict] = [
    {
        "label": "url",
        "regex": r'https?://[^\s<>"\']+[^\s<>"\',.:;!?)\']',
        "url": "{match}",
        "prefix": "",
    },
]

_DEFAULT_PATTERNS_FILE = Path.home() / ".config" / "termbud" / "patterns.toml"


def _load_patterns(path: Path | None = None) -> list[dict]:
    toml_path = path or _DEFAULT_PATTERNS_FILE
    if not toml_path.exists():
        return []
    with open(toml_path, "rb") as f:
        data = tomllib.load(f)
    return [
        {
            "label": p["label"],
            "regex": p["regex"],
            "url": p["url"],
            "prefix": p.get("prefix", ""),
        }
        for p in data.get("patterns", {}).values()
    ]


def _extract(text: str, patterns: list[dict]) -> list[tuple[str, str, str, str]]:
    seen: set[tuple[str, str]] = set()
    results = []
    for p in patterns:
        for m in re.finditer(p["regex"], text, re.MULTILINE):
            val = m.group(1) if m.lastindex else m.group(0)
            if (p["label"], val) not in seen:
                seen.add((p["label"], val))
                results.append((p["label"], val, p["url"], p["prefix"]))
    return results


def _fmt(label: str, display: str) -> str:
    return f"[{label:<16}] {display}"


def _platform_cmds() -> tuple[str, str]:
    if sys.platform == "darwin":
        return "open", "pbcopy"
    if "microsoft" in os.uname().release.lower():
        return "wslview", "clip.exe"
    if os.environ.get("WAYLAND_DISPLAY") or shutil.which("wl-copy"):
        return "xdg-open", "wl-copy"
    return "xdg-open", "xclip -selection clipboard"


@app.command("pick")
def pick(
    patterns_file: Path | None = typer.Option(
        None,
        "--patterns-file",
        "-p",
        help="Patterns TOML file (default: ~/.config/termbud/patterns.toml)",
    ),
    open_cmd: str | None = typer.Option(None, "--open-cmd", help="Command to open URLs"),
) -> None:
    """Pick a pattern match from Zellij scrollback and open or yank it."""
    default_open, copy_cmd = _platform_cmds()
    open_cmd = open_cmd or default_open

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp_path = tmp.name

    try:
        subprocess.run(
            ["zellij", "action", "dump-screen", "--full", tmp_path],
            check=True,
        )
        text = Path(tmp_path).read_text(errors="replace")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("termbud: failed to dump Zellij screen", file=sys.stderr)
        sys.exit(1)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    patterns = _BUILTIN_PATTERNS + _load_patterns(patterns_file)
    matches = _extract(text, patterns)

    if not matches:
        print("termbud: no patterns found", file=sys.stderr)
        sys.exit(0)

    # Each fzf line: "display\turl\tyank_value" — fzf shows col 1, binds act on cols 2/3.
    lines = [
        f"{_fmt(label, prefix + match)}\t{url_tmpl.replace('{match}', match)}\t{prefix + match}"
        for label, match, url_tmpl, prefix in matches
    ]

    fzf_args = [
        "fzf",
        "--ansi",
        "--prompt", "pick> ",
        "--header", "enter/ctrl-o: open  ctrl-y: yank  esc: quit",
        "--delimiter", "\t",
        "--with-nth", "1",
        f"--bind=enter:execute-silent({open_cmd} {{2}})+abort",
        f"--bind=ctrl-o:execute-silent({open_cmd} {{2}})+abort",
        f"--bind=ctrl-y:execute-silent(printf '%s' {{3}} | {copy_cmd})+abort",
        "--no-multi",
        "--layout", "reverse",
    ]

    r, w = os.pipe()
    os.write(w, "\n".join(lines).encode())
    os.close(w)
    os.dup2(r, 0)
    os.close(r)
    os.execvp("fzf", fzf_args)


@app.command("open-url")
def open_url(
    open_cmd: str | None = typer.Option(
        None,
        "--open-cmd",
        help="Command to use to open the URL. Defaults to guessing based on OS.",
    ),
) -> None:
    """Open a URL from the current Zellij pane's scrollback."""
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

    urls = _URL_PATTERN.findall(scrollback)

    if not urls:
        print("No URLs found.", file=sys.stderr)
        sys.exit(0)

    ordered_urls = list(dict.fromkeys(reversed(urls)))

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as urls_file:
        urls_file.write("\n".join(ordered_urls))
        urls_file_name = urls_file.name

    default_open, copy_cmd = _platform_cmds()
    open_cmd = open_cmd or default_open

    fzf_env = os.environ.copy()
    fzf_env["FZF_DEFAULT_COMMAND"] = f"cat {shlex.quote(urls_file_name)}"

    try:
        try:
            result = subprocess.run(
                ["fzf", "--prompt=Open URL: ", "--expect=enter,ctrl-c"],
                env=fzf_env,
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            if os.path.exists(urls_file_name):
                os.remove(urls_file_name)

        if not result.stdout:
            sys.exit(0)

        lines = result.stdout.splitlines()
        if len(lines) < 2:
            sys.exit(0)

        key_pressed = lines[0]
        url = lines[1]

        if key_pressed == "enter":
            subprocess.run([*shlex.split(open_cmd), url], check=False)
        elif key_pressed == "ctrl-c":
            subprocess.run(shlex.split(copy_cmd), input=url, text=True, check=False)

    except OSError:
        print("Failed to execute fzf", file=sys.stderr)
        sys.exit(1)
