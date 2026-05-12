import os
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import NamedTuple, TypedDict

import typer

app = typer.Typer(help="Zellij subcommands")

_URL_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[a-zA-Z0-9_.~!*'();:@&=+$,/?%#-]+")


class Pattern(TypedDict):
    label: str
    regex: str
    url: str
    prefix: str


class Match(NamedTuple):
    label: str
    value: str
    url_template: str
    prefix: str


_BUILTIN_PATTERNS: list[Pattern] = [
    {
        "label": "web",
        "regex": r'https?://[^\s<>"\']+[^\s<>"\',.:;!?)\']',
        "url": "{match}",
        "prefix": "",
    },
    {
        "label": "url",
        # Non-http(s) schemes: file, ftp, ssh, git, etc.
        "regex": r'(?<!\w)(?!https?://)[a-zA-Z][a-zA-Z0-9+.-]*://[^\s<>"\']+[^\s<>"\',.:;!?)\']',
        "url": "{match}",
        "prefix": "",
    },
    {
        "label": "path",
        # Absolute and home-relative paths. Negative lookbehind avoids matching
        # paths that are already part of a scheme:// URL.
        "regex": r'(?<![/:\w])((?:~|\.{1,2})?/[^\s<>"\',:;`|&\\]+)',
        "url": "{match}",
        "prefix": "",
    },
]


def _load_patterns(path: Path | None = None) -> list[Pattern]:
    if path is None:
        return []
    if not path.exists():
        return []
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return [
        Pattern(
            label=p["label"],
            regex=p["regex"],
            url=p["url"],
            prefix=p.get("prefix", ""),
        )
        for p in data.get("patterns", {}).values()
    ]


def _extract(text: str, patterns: list[Pattern]) -> list[Match]:
    seen: set[tuple[str, str]] = set()
    results: list[Match] = []
    for p in patterns:
        for m in re.finditer(p["regex"], text, re.MULTILINE):
            val = m.group(1) if m.lastindex else m.group(0)
            if (p["label"], val) not in seen:
                seen.add((p["label"], val))
                results.append(Match(p["label"], val, p["url"], p["prefix"]))
    return results


_DIM_CYAN = "\033[2;36m"
_RESET    = "\033[0m"


def _fmt(label: str, display: str, label_width: int = 4) -> str:
    return f"{_DIM_CYAN}{label:>{label_width}}{_RESET}  {display}"


def _platform_cmds() -> tuple[str, str]:
    if sys.platform == "darwin":
        return "open", "pbcopy"
    if "microsoft" in os.uname().release.lower():
        return "wslview", "clip.exe"
    if os.environ.get("WAYLAND_DISPLAY") or shutil.which("wl-copy"):
        return "xdg-open", "wl-copy"
    return "xdg-open", "xclip -selection clipboard"


def _editor_cmd() -> str:
    return os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nvim"


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
    """Pick a pattern match from stdin and open or yank it.

    Reads scrollback text from stdin. Pipe from the shell wrapper:
        zellij action dump-screen --full | termbud zellij pick
    """
    default_open, copy_cmd = _platform_cmds()
    open_cmd = open_cmd or default_open
    editor = _editor_cmd()

    text = sys.stdin.read()

    patterns = _BUILTIN_PATTERNS + _load_patterns(patterns_file)
    matches = _extract(text, patterns)

    if not matches:
        print("termbud: no patterns found", file=sys.stderr)
        sys.exit(0)

    label_width = max(len(m.label) for m in matches)
    # Each fzf line: "display\turl\tyank_value" — fzf shows col 1, binds act on cols 2/3.
    lines = "\n".join(
        _fmt(m.label, m.prefix + m.value, label_width)
        + f"\t{m.url_template.replace('{match}', m.value)}"
        + f"\t{m.prefix + m.value}"
        for m in matches
    )

    subprocess.run(
        [
            "fzf",
            "--ansi",
            "--prompt", "pick> ",
            "--header", f"enter: insert  ctrl-o: open  ctrl-y: yank  ctrl-e: {editor}  esc: quit",
            "--delimiter", "\t",
            "--with-nth", "1",
            # enter: fzf default — prints tab-separated line to stdout, wrapper handles write-chars
            f"--bind=ctrl-o:execute-silent({open_cmd} {{2}})+clear-query",
            f"--bind=ctrl-y:execute-silent(printf '%s' {{3}} | {copy_cmd})",
            f"--bind=ctrl-e:execute({editor} {{3}})+abort",
            "--no-multi",
            "--layout", "reverse",
        ],
        input=lines,
        text=True,
    )


@app.command("open-url")
def open_url(
    open_cmd: str | None = typer.Option(
        None,
        "--open-cmd",
        help="Command to use to open the URL. Defaults to guessing based on OS.",
    ),
) -> None:
    """Open a URL from the current Zellij pane's scrollback."""
    import tempfile

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
