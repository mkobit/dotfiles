"""Sync Chrome site search shortcuts via DevTools console paste.

Generates JavaScript that uses Chrome's internal SearchEnginesBrowserProxy
to add/remove shortcuts. Paste into DevTools console on chrome://settings/searchEngines.

Data source: a TOML file with Vimium search engine entries.
Every entry becomes a Chrome shortcut: key "sg" -> keyword "@sg".
"""

import argparse
import json
import logging
import subprocess
import sys
import termios
import time
import tomllib
import tty
import typing
from collections.abc import Callable, Sequence
from pathlib import Path

from pydantic import BaseModel

_CHROME_SETTINGS_URL = "chrome://settings/searchEngines"
_OK = 25


class _ColorFormatter(logging.Formatter):
    """Terminal formatter with colored level badges and timestamps."""

    _COLORS: typing.ClassVar[dict[int, str]] = {
        logging.INFO: "\033[0;34m",
        _OK: "\033[0;32m",
        logging.WARNING: "\033[0;33m",
        logging.ERROR: "\033[0;31m",
    }
    _LABELS: typing.ClassVar[dict[int, str]] = {
        logging.INFO: "INFO",
        _OK: "OK  ",
        logging.WARNING: "WARN",
        logging.ERROR: "ERR ",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with timestamp and colored badge."""
        ts = time.strftime("%H:%M:%S")
        color = self._COLORS.get(record.levelno, "\033[0m")
        label = self._LABELS.get(record.levelno, record.levelname)
        return f"\033[2m{ts}\033[0m {color}[{label}]\033[0m {record.getMessage()}"


logging.addLevelName(_OK, "OK")
_log = logging.getLogger(__name__)


class _Shortcut(BaseModel, frozen=True):
    """A browser site search shortcut."""

    keyword: str
    name: str
    url: str


def _parse_toml(path: Path) -> Sequence[_Shortcut]:
    """Parse search-engines.toml into Chrome shortcuts.

    Each entry's key becomes @key. Angle brackets in names are replaced
    with parens to avoid crashing Chrome's Polymer renderer.
    """
    data = tomllib.loads(path.read_text())
    return tuple(
        _Shortcut(
            keyword="@" + entry["key"],
            name=(entry.get("description", "") or entry["key"]).replace("<", "(").replace(">", ")"),
            url=entry["url"],
        )
        for group in data.get("engine", {}).values()
        for entry in group.get("entries", [])
    )


def _build_sync_script(shortcuts: Sequence[_Shortcut], *, prune: bool = False, confirm: bool = False) -> str:
    """Generate JS console script for Chrome search engine sync.

    Args:
        shortcuts: Desired shortcuts to sync.
        prune: If True, identify entries to remove.
        confirm: If True (with prune), actually execute removals.
    """
    desired_json = json.dumps([s.model_dump() for s in shortcuts], indent=2)
    prune_js = "true" if prune else "false"
    confirm_js = "true" if confirm else "false"
    return f"""\
(async () => {{
  const m = await import('chrome://settings/settings.js');
  const proxy = m.SearchEnginesBrowserProxyImpl.getInstance();
  const delay = ms => new Promise(r => setTimeout(r, ms));
  const tag = (color, label, msg) =>
    console.log(`%c${{label}}%c ${{msg}}`, `background:${{color}};color:#fff;padding:1px 6px;border-radius:3px;font-weight:600`, '');

  const data = await proxy.getCategorizedTemplateUrls();
  const active = data.activeSiteShortcuts.filter(e => e.canBeRemoved);
  const currentByKeyword = new Map(active.map(e => [e.keyword, e]));
  await delay(500);

  const desired = {desired_json};
  const desiredKeywords = new Set(desired.map(d => d.keyword));
  const toChrome = url => url.replace(/%s/g, '{{searchTerms}}');
  const toAdd = desired.filter(d => !currentByKeyword.has(d.keyword));
  const prune = {prune_js};
  const confirmRemoval = {confirm_js};
  // Only prune @-prefixed keywords (managed by us), leave others alone
  const toRemove = prune ? active.filter(e => e.keyword.startsWith('@') && !desiredKeywords.has(e.keyword)) : [];

  if (!toAdd.length && !toRemove.length) {{
    tag('#6b7280', 'SYNC', `already converged (${{currentByKeyword.size}} entries)`);
    return;
  }}

  let added = 0, removed = 0, errors = [];

  for (const d of toAdd) {{
    try {{
      proxy.searchEngineEditStarted(0);
      proxy.searchEngineEditCompleted(d.name, d.keyword, toChrome(d.url));
      added++;
      tag('#3b82f6', '+ADD', d.keyword + ' \\u2192 ' + d.name);
    }} catch (e) {{
      errors.push('+' + d.keyword + ': ' + e.message);
    }}
    await delay(150);
  }}

  for (const e of toRemove) {{
    if (!confirmRemoval) {{
      tag('#f59e0b', 'WOULD-DEL', e.keyword + ' \\u2192 ' + e.name + ' (id=' + e.id + ')');
      removed++;
      continue;
    }}
    try {{
      proxy.removeSearchEngine(e.id);
      removed++;
      tag('#f59e0b', '-DEL', e.keyword + ' \\u2192 ' + e.name);
    }} catch (err) {{
      errors.push('-' + e.keyword + ': ' + err.message);
    }}
    await delay(150);
  }}

  const parts = [];
  if (added) parts.push(`+${{added}} added`);
  if (removed && confirmRemoval) parts.push(`-${{removed}} removed`);
  if (removed && !confirmRemoval) parts.push(`${{removed}} would be removed (run with --prune --confirm to apply)`);
  parts.push(`${{currentByKeyword.size - (confirmRemoval ? removed : 0) + added}} total`);

  if (errors.length) {{
    tag('#ef4444', 'ERROR', parts.join(', ') + '\\n' + errors.join('\\n'));
  }} else {{
    tag('#22c55e', 'SYNC', parts.join(', '));
  }}
}})();"""


def _getkey() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _prompt_enter(message: str) -> None:
    print(f"\n\033[0;36m[?]\033[0m    {message}", end="", flush=True)
    while True:
        ch = _getkey()
        if ch in ("\r", "\n"):
            print()
            return
        if ch == "\x03":
            print()
            _log.info("skipped")
            sys.exit(0)


def _prompt_done_or_recopy(copy_fn: Callable[[], None]) -> None:
    print("\n\033[0;36m[?]\033[0m    Press Enter when done, or 'r' to recopy ", end="", flush=True)
    while True:
        ch = _getkey()
        if ch in ("\r", "\n"):
            print()
            return
        if ch.lower() == "r":
            copy_fn()
            print()
            _log.log(_OK, "recopied to clipboard")
            print("\033[0;36m[?]\033[0m    Press Enter when done, or 'r' to recopy ", end="", flush=True)
        if ch == "\x03":
            print()
            _log.info("skipped")
            sys.exit(0)


def _prompt_prune_or_skip(copy_fn: Callable[[], None]) -> None:
    print("\n\033[0;33m[!]\033[0m    Press 'p' to copy PRUNE script, or Enter to skip removals ", end="", flush=True)
    while True:
        ch = _getkey()
        if ch in ("\r", "\n"):
            print()
            _log.info("skipped removals")
            return
        if ch.lower() == "p":
            copy_fn()
            print()
            _log.log(_OK, "prune script copied — paste into console to remove extras")
            _prompt_done_or_recopy(copy_fn)
            return
        if ch == "\x03":
            print()
            _log.info("skipped")
            sys.exit(0)


def _copy_to_clipboard(text: str) -> None:
    subprocess.run(["pbcopy"], input=text.encode(), check=True)


def main() -> None:
    """Entry point for chrome-sync CLI."""
    handler = logging.StreamHandler()
    handler.setFormatter(_ColorFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("toml_path", type=Path, help="Path to search-engines.toml")
    parser.add_argument("--dry-run", action="store_true", help="Print script without copying.")
    parser.add_argument("--no-open", action="store_true", help="Don't open Chrome settings page.")
    parser.add_argument("--prune", action="store_true", help="Show which shortcuts would be removed (dry-run).")
    parser.add_argument("--confirm", action="store_true", help="With --prune, actually execute removals.")
    args = parser.parse_args()

    if args.confirm and not args.prune:
        parser.error("--confirm requires --prune")

    toml_path: Path = args.toml_path
    if not toml_path.exists():
        _log.error("TOML not found: %s", toml_path)
        sys.exit(1)

    shortcuts = _parse_toml(toml_path)
    _log.info("%d shortcuts from %s", len(shortcuts), toml_path.name)

    if args.dry_run:
        script = _build_sync_script(shortcuts, prune=args.prune, confirm=args.confirm)
        print(script)
        return

    if args.prune and args.confirm:
        add_script = _build_sync_script(shortcuts, prune=True, confirm=False)
        prune_script = _build_sync_script(shortcuts, prune=True, confirm=True)

        _prompt_enter("Press Enter to copy ADD + PREVIEW script (Ctrl+C to skip)...")
        _copy_to_clipboard(add_script)
        _log.log(_OK, "copied — adds new entries, previews removals (WOULD-DEL)")

        if not args.no_open:
            _log.info("opening chrome://settings/searchEngines — paste into console (Cmd+Opt+J)")
            subprocess.run(["open", "-a", "Google Chrome", _CHROME_SETTINGS_URL], check=True)
        else:
            _log.info("paste clipboard into DevTools console on:\n  %s", _CHROME_SETTINGS_URL)

        _prompt_done_or_recopy(lambda: _copy_to_clipboard(add_script))
        _log.log(_OK, "adds applied — check WOULD-DEL entries in console")
        _log.warning("next step removes entries not in TOML")
        _prompt_prune_or_skip(lambda: _copy_to_clipboard(prune_script))
    else:
        script = _build_sync_script(shortcuts, prune=args.prune, confirm=args.confirm)

        _prompt_enter("Press Enter to copy sync script to clipboard (Ctrl+C to skip)...")
        _copy_to_clipboard(script)
        _log.log(_OK, "sync script copied to clipboard")

        if not args.no_open:
            _log.info("opening chrome://settings/searchEngines — paste into console (Cmd+Opt+J)")
            subprocess.run(["open", "-a", "Google Chrome", _CHROME_SETTINGS_URL], check=True)
        else:
            _log.info("paste clipboard into DevTools console on:\n  %s", _CHROME_SETTINGS_URL)

        _prompt_done_or_recopy(lambda: _copy_to_clipboard(script))

    _log.log(_OK, "done")


if __name__ == "__main__":
    main()
