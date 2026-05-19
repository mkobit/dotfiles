import atexit
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
_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


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
        # paths that are already part of a scheme:// URL. Trailing bracket/punct
        # chars are excluded via the final character class.
        "regex": r'(?<![/:\w])((?:~|\.{1,2})?/[^\s<>"\',:;`|&\\]*[^\s<>"\',:;`|&\\()[\]{}.!?,])',
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


def _default_patterns_file() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(xdg) / "termbud" / "patterns.toml"


def _extract(text: str, patterns: list[Pattern]) -> list[Match]:
    text = _ANSI_ESCAPE.sub("", text)
    seen: set[tuple[str, str]] = set()
    results: list[Match] = []
    for p in patterns:
        for m in re.finditer(p["regex"], text, re.MULTILINE):
            val = (m.group(1) if m.lastindex else m.group(0)).strip()
            if not val:
                continue
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


def _fzf_args(open_cmd: str, copy_cmd: str, editor: str) -> list[str]:
    return [
        "fzf",
        "--ansi",
        "--prompt", "pick> ",
        "--header", f"enter: insert  ctrl-o: open  ctrl-y: yank  ctrl-e: open in {editor}  esc: quit",
        "--delimiter", "\t",
        "--with-nth", "1",
        f"--bind=ctrl-o:execute-silent({open_cmd} {{2}})+clear-query",
        f"--bind=ctrl-y:execute-silent(printf '%s' {{3}} | {copy_cmd})",
        f"--bind=ctrl-e:execute({editor} {{3}})+abort",
        "--no-multi",
        "--layout", "reverse",
    ]


def _format_lines(matches: list[Match]) -> str:
    label_width = max(len(m.label) for m in matches)
    return "\n".join(
        _fmt(m.label, m.prefix + m.value, label_width)
        + f"\t{m.url_template.replace('{match}', m.value)}"
        + f"\t{m.prefix + m.value}"
        for m in matches
    )


def _zellij(*args: str) -> None:
    subprocess.run(["zellij", "action", *args], capture_output=True)


@app.command("pick")
def pick(
    patterns_file: Path | None = typer.Option(
        None,
        "--patterns-file",
        "-p",
        help="Patterns TOML file (default: $XDG_CONFIG_HOME/termbud/patterns.toml)",
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

    patterns = _BUILTIN_PATTERNS + _load_patterns(patterns_file or _default_patterns_file())
    matches = _extract(text, patterns)

    if not matches:
        print("termbud: no patterns found", file=sys.stderr)
        sys.exit(0)

    subprocess.run(
        _fzf_args(open_cmd, copy_cmd, editor),
        input=_format_lines(matches),
        text=True,
    )


@app.command("open")
def open_picker(
    patterns_file: Path | None = typer.Option(
        None,
        "--patterns-file",
        "-p",
        help="Patterns TOML file (default: $XDG_CONFIG_HOME/termbud/patterns.toml)",
    ),
    open_cmd: str | None = typer.Option(None, "--open-cmd", help="Command to open URLs"),
) -> None:
    """Open the scrollback picker from a Zellij floating pane."""
    if "ZELLIJ" not in os.environ:
        print("termbud: must be run inside a Zellij session", file=sys.stderr)
        raise typer.Exit(1)

    floating_pane_id = os.environ["ZELLIJ_PANE_ID"]

    default_open, copy_cmd = _platform_cmds()
    open_cmd = open_cmd or default_open
    editor = _editor_cmd()

    atexit.register(lambda: _zellij("switch-mode", "normal"))
    _zellij("switch-mode", "locked")

    source_pane_id: str | None = None
    scrollback = ""
    for pane_id in range(int(floating_pane_id) - 1, 0, -1):
        out = subprocess.run(
            ["zellij", "action", "dump-screen", "--full", "-p", str(pane_id)],
            capture_output=True,
            text=True,
        ).stdout
        if out.strip():
            source_pane_id = str(pane_id)
            scrollback = out
            break

    if not source_pane_id:
        raise typer.Exit(0)

    patterns = _BUILTIN_PATTERNS + _load_patterns(patterns_file or _default_patterns_file())
    matches = _extract(scrollback, patterns)

    if not matches:
        raise typer.Exit(0)

    result = subprocess.run(
        _fzf_args(open_cmd, copy_cmd, editor),
        input=_format_lines(matches),
        text=True,
        stdout=subprocess.PIPE,
    )

    if result.stdout:
        parts = result.stdout.strip().split("\t")
        yank = parts[2] if len(parts) >= 3 else ""
        if yank:
            _zellij("write-chars", "--pane-id", source_pane_id, yank)
