"""Sync Chrome site search shortcuts via DevTools console paste.

Generates JavaScript that uses Chrome's internal SearchEnginesBrowserProxy
to add/remove shortcuts. Paste into DevTools console on chrome://settings/searchEngines.

Data source: a TOML file with Vimium search engine entries.
Every entry becomes a Chrome shortcut: key "sg" -> keyword "@sg".
"""

import json
import logging
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel

from browser_sync import _browser, _clipboard, _devtools, _terminal

_CHROME_SETTINGS_URL = "chrome://settings/searchEngines"
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
  {_devtools.JS_TAG_HELPER}

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


def run(toml_path: Path, *, prune: bool, confirm: bool, dry_run: bool, no_open: bool) -> None:
    """Sync Chrome site search shortcuts from the given TOML file."""
    if not toml_path.exists():
        _log.error("TOML not found: %s", toml_path)
        sys.exit(1)

    shortcuts = _parse_toml(toml_path)
    _log.info("%d shortcuts from %s", len(shortcuts), toml_path.name)

    if dry_run:
        print(_build_sync_script(shortcuts, prune=prune, confirm=confirm))
        return

    if prune and confirm:
        add_script = _build_sync_script(shortcuts, prune=True, confirm=False)
        prune_script = _build_sync_script(shortcuts, prune=True, confirm=True)

        _terminal.prompt_enter("Press Enter to copy ADD + PREVIEW script (Ctrl+C to skip)...")
        _clipboard.copy_to_clipboard(add_script)
        _log.log(_terminal.OK, "copied — adds new entries, previews removals (WOULD-DEL)")

        if not no_open:
            _log.info("opening chrome://settings/searchEngines — paste into console (Cmd+Option+J)")
            _browser.open_in_chrome(_CHROME_SETTINGS_URL)
        else:
            _log.info("paste clipboard into DevTools console on:\n  %s", _CHROME_SETTINGS_URL)

        _terminal.prompt_done_or_recopy(lambda: _clipboard.copy_to_clipboard(add_script))
        _log.log(_terminal.OK, "adds applied — check WOULD-DEL entries in console")
        _log.warning("next step removes entries not in TOML")
        _terminal.prompt_prune_or_skip(lambda: _clipboard.copy_to_clipboard(prune_script))
    else:
        script = _build_sync_script(shortcuts, prune=prune, confirm=confirm)

        _terminal.prompt_enter("Press Enter to copy sync script to clipboard (Ctrl+C to skip)...")
        _clipboard.copy_to_clipboard(script)
        _log.log(_terminal.OK, "sync script copied to clipboard")

        if not no_open:
            _log.info("opening chrome://settings/searchEngines — paste into console (Cmd+Option+J)")
            _browser.open_in_chrome(_CHROME_SETTINGS_URL)
        else:
            _log.info("paste clipboard into DevTools console on:\n  %s", _CHROME_SETTINGS_URL)

        _terminal.prompt_done_or_recopy(lambda: _clipboard.copy_to_clipboard(script))

    _log.log(_terminal.OK, "done")
