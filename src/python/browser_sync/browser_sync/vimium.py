"""Sync Vimium config to Chrome via the chrome.storage.sync API.

Compiles a search-engines TOML file plus a key-mappings text file into
Vimium's storage format and generates a console script. Paste into the
DevTools console on the Vimium options page (Cmd+Option+I).
"""

import json
import logging
import tomllib
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel

from browser_sync import _browser, _clipboard, _devtools, _terminal

_VIMIUM_OPTIONS_URL = "chrome-extension://dbepggeogbaibhgnhhndojpepiihcmeb/pages/options.html"
_log = logging.getLogger(__name__)


class _Engine(BaseModel, frozen=True):
    """A single Vimium search engine entry."""

    key: str
    url: str
    description: str = ""

    def to_vimium_line(self) -> str:
        """Render as a `key: url description` Vimium config line."""
        suffix = f" {self.description}" if self.description else ""
        return f"{self.key}: {self.url}{suffix}"


class _EngineGroup(BaseModel, frozen=True):
    """A commented group of Vimium search engine entries."""

    comment: str
    entries: tuple[_Engine, ...]

    def to_vimium_lines(self) -> Sequence[str]:
        """Render the group's comment header followed by its entry lines."""
        return [f"# {self.comment}", *(e.to_vimium_line() for e in self.entries)]


def _parse_toml(toml_path: Path) -> Sequence[_EngineGroup]:
    """Parse search-engines.toml into engine groups."""
    data = tomllib.loads(toml_path.read_text())
    return tuple(
        _EngineGroup(
            comment=group["comment"],
            entries=tuple(
                _Engine(
                    key=entry["key"],
                    url=entry["url"],
                    description=entry.get("description", ""),
                )
                for entry in group.get("entries", [])
            ),
        )
        for group in data.get("engine", {}).values()
    )


def _compile_search_engines(groups: Sequence[_EngineGroup]) -> str:
    """Join engine groups into Vimium's searchEngines text block."""
    return "\n\n".join("\n".join(g.to_vimium_lines()) for g in groups)


def _load_key_mappings(path: Path) -> str:
    """Read non-comment, non-blank lines from the key-mappings file."""
    return "\n".join(
        stripped
        for line in path.read_text().splitlines()
        if (stripped := line.strip()) and not stripped.startswith("#")
    )


def _build_sync_script(search_engines: str, key_mappings: str) -> str:
    """Generate the chrome.storage.sync console script."""
    settings_json = json.dumps({"searchEngines": search_engines, "keyMappings": key_mappings}, indent=2)
    return f"""\
chrome.storage.sync.set({settings_json}, () => {{
  {_devtools.JS_TAG_HELPER}
  if (chrome.runtime.lastError) {{
    tag('#ef4444', 'ERROR', chrome.runtime.lastError.message);
  }} else {{
    tag('#22c55e', 'VIMIUM', 'settings synced — reload options page to verify');
  }}
}});"""


def run(toml_path: Path, keymappings_path: Path, *, dry_run: bool, no_open: bool) -> None:
    """Sync Vimium search engines and key mappings from the given files."""
    groups = _parse_toml(toml_path)
    search_engines = _compile_search_engines(groups)
    key_mappings = _load_key_mappings(keymappings_path)
    script = _build_sync_script(search_engines, key_mappings)

    if dry_run:
        print("=== Compiled search engines ===")
        print(search_engines)
        print("\n=== Key mappings ===")
        print(key_mappings)
        print("\n=== Console script ===")
        print(script)
        return

    _terminal.prompt_enter("Press Enter to copy sync script to clipboard (Ctrl+C to skip)...")
    _clipboard.copy_to_clipboard(script)
    _log.log(_terminal.OK, "Vimium sync script copied to clipboard")

    if not no_open:
        _log.info("opening Vimium options — paste into DevTools console (Cmd+Option+I)")
        _browser.open_in_chrome(_VIMIUM_OPTIONS_URL)
    else:
        _log.info("paste clipboard into DevTools console on:\n  %s", _VIMIUM_OPTIONS_URL)

    _terminal.prompt_done_or_recopy(lambda: _clipboard.copy_to_clipboard(script))
    _log.log(_terminal.OK, "done")
