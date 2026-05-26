import atexit
import contextlib
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import NamedTuple, TypedDict

import typer

from termbud.utils import editor_cmd, platform_cmds

app = typer.Typer(help="Zellij subcommands")

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
_RESET = "\033[0m"


def _fmt(label: str, display: str, label_width: int = 4) -> str:
    return f"{_DIM_CYAN}{label:>{label_width}}{_RESET}  {display}"


def _fzf_args(open_cmd: str, copy_cmd: str, editor: str) -> list[str]:
    return [
        "fzf",
        "--ansi",
        "--prompt",
        "pick> ",
        "--header",
        f"enter: insert  ctrl-o: open  ctrl-y: yank  ctrl-e: open in {editor}  esc: quit",
        "--delimiter",
        "\t",
        "--with-nth",
        "1",
        f"--bind=ctrl-o:execute-silent({open_cmd} {{2}})+clear-query",
        f"--bind=ctrl-y:execute-silent(printf '%s' {{3}} | {copy_cmd})",
        f"--bind=ctrl-e:execute({editor} {{3}})+abort",
        "--no-multi",
        "--layout",
        "reverse",
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
    with contextlib.suppress(OSError):
        subprocess.run(["zellij", "action", *args], capture_output=True, check=False)


@app.command("history-search")
def history_search(
    from_file: Path | None = typer.Option(
        None,
        "--from-file",
        help="Read scrollback from file (written by DumpScreen keybind action before Run)",
    ),
    patterns_file: Path | None = typer.Option(
        None,
        "--patterns-file",
        "-p",
        help="Extra patterns TOML file (default: $XDG_CONFIG_HOME/termbud/patterns.toml)",
    ),
    open_cmd: str | None = typer.Option(None, "--open-cmd", help="Command to open URLs"),
    source_pane_id: str | None = typer.Option(None, "--source-pane-id", hidden=True),
) -> None:
    """Scrollback pattern picker — runs inside a Zellij floating pane.

    Invoke via DumpScreen keybind (config.kdl):

        DumpScreen "/tmp/termbud_scrollback.txt" { full true }
        Run "termbud" "zellij" "history-search" "--from-file" "/tmp/termbud_scrollback.txt" {
            floating true
            close_on_exit true
        }
    """
    if "ZELLIJ" not in os.environ:
        print("termbud: must be run inside a Zellij session", file=sys.stderr)
        raise typer.Exit(1)

    if from_file is None and source_pane_id is None:
        print("termbud: --from-file or --source-pane-id required", file=sys.stderr)
        raise typer.Exit(1)

    default_open, copy_cmd = platform_cmds()
    open_cmd = open_cmd or default_open
    editor = editor_cmd()

    atexit.register(lambda: _zellij("switch-mode", "normal"))
    _zellij("switch-mode", "locked")

    if from_file is not None:
        scrollback = from_file.read_text()
    else:
        assert source_pane_id is not None
        scrollback = subprocess.run(
            ["zellij", "action", "dump-screen", "--full", "-p", source_pane_id],
            capture_output=True,
            text=True,
            check=False,
        ).stdout

    if not scrollback.strip():
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
        check=False,
    )

    if result.stdout:
        parts = result.stdout.strip().split("\t")
        yank = parts[2] if len(parts) >= 3 else ""
        # Write-back requires source pane ID; blocked by Zellij #4993 (ZELLIJ_ORIGIN_PANE_ID not
        # exposed in Run-spawned panes) and #4136 (focus-previous-pane broken in floating panes).
        if yank and source_pane_id:
            _zellij("write-chars", "--pane-id", source_pane_id, yank)
