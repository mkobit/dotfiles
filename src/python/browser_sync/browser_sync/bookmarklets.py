"""Sync bookmarklet JS source files into Chrome via the chrome.bookmarks API.

Compares source JS files against Chrome's current Bookmarks file. If they
differ, generates a console script, copies it to clipboard, and opens
chrome://bookmarks. Paste into the DevTools console (Cmd+Option+I) to apply.
"""

import json
import logging
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from pydantic import BaseModel

from browser_sync import _browser, _clipboard, _terminal

_CHROME_BOOKMARKS = Path.home() / "Library/Application Support/Google/Chrome/Default/Bookmarks"
_FOLDER_TITLE = "bookmarklets"
_log = logging.getLogger(__name__)


class _Bookmarklet(BaseModel, frozen=True):
    """A bookmarklet entry: a display title and its `javascript:` URL."""

    title: str
    url: str


class _Update(_Bookmarklet, frozen=True):
    """A bookmarklet whose title or URL changed, with its prior title."""

    old_title: str


class _Diff(BaseModel, frozen=True):
    """The create/update/remove sets between desired and current state."""

    create: tuple[_Bookmarklet, ...]
    update: tuple[_Update, ...]
    remove: tuple[_Bookmarklet, ...]

    @property
    def has_changes(self) -> bool:
        """Whether any create/update/remove operations are pending."""
        return bool(self.create or self.update or self.remove)


def _get_title(js_file: Path, js_source: str) -> str:
    """Extract title from '// title: ...' directive, or fall back to filename."""
    match = re.match(r"^//\s*title:\s*(.+)", js_source)
    if match:
        return match.group(1).strip()
    return " ".join(word.capitalize() for word in js_file.stem.split("-"))


def _js_to_bookmarklet_url(js_source: str) -> str:
    """Convert JS source to a javascript: bookmarklet URL."""
    lines = js_source.strip().splitlines()
    body = lines[1:] if lines and re.match(r"^//\s*title:", lines[0]) else lines
    collapsed = re.sub(r"\s*\n\s*", " ", "\n".join(body).strip())
    return f"javascript:{collapsed}"


def _get_desired(dir_path: Path) -> Mapping[str, str]:
    """Return {title: url} from source JS files, sorted case-insensitively by title."""
    js_files = sorted(dir_path.glob("*.js"))
    if not js_files:
        _log.error("no .js files found in %s", dir_path)
        sys.exit(1)

    sources = {js_file: js_file.read_text() for js_file in js_files}
    entries = {_get_title(js_file, source): _js_to_bookmarklet_url(source) for js_file, source in sources.items()}
    return dict(sorted(entries.items(), key=lambda item: item[0].lower()))


def _get_chrome_bookmarklets() -> Mapping[str, str]:
    """Return {title: url} from Chrome's Bookmarks file for the target folder."""
    if not _CHROME_BOOKMARKS.exists():
        return {}

    bookmarks = json.loads(_CHROME_BOOKMARKS.read_text())

    def find_folder(node: dict[str, Any], name: str) -> dict[str, Any] | None:
        if node.get("name") == name and node.get("type") == "folder":
            return node
        return next((found for child in node.get("children", []) if (found := find_folder(child, name))), None)

    roots = (root for root in bookmarks.get("roots", {}).values() if isinstance(root, dict))
    folder = next((found for root in roots if (found := find_folder(root, _FOLDER_TITLE))), None)
    if folder is None:
        return {}
    return {child["name"]: unquote(child["url"]) for child in folder.get("children", []) if child.get("type") == "url"}


def _slugify(title: str) -> str:
    """Normalize a title to a comparable slug: lowercase, hyphens, no special chars."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _compute_diff(desired: Mapping[str, str], current: Mapping[str, str]) -> _Diff:
    """Compare desired vs current using slug matching."""
    desired_by_slug = {_slugify(t): (t, u) for t, u in desired.items()}
    current_by_slug = {_slugify(t): (t, u) for t, u in current.items()}
    return _Diff(
        create=tuple(
            _Bookmarklet(title=t, url=u) for slug, (t, u) in desired_by_slug.items() if slug not in current_by_slug
        ),
        update=tuple(
            _Update(title=t, url=u, old_title=current_by_slug[slug][0])
            for slug, (t, u) in desired_by_slug.items()
            if slug in current_by_slug and (t, u) != current_by_slug[slug]
        ),
        remove=tuple(
            _Bookmarklet(title=t, url=u) for slug, (t, u) in current_by_slug.items() if slug not in desired_by_slug
        ),
    )


def _build_sync_script(desired: Mapping[str, str]) -> str:
    """Build the chrome.bookmarks API console script."""
    desired_json = json.dumps([{"title": t, "url": u} for t, u in desired.items()], indent=2)
    return f"""\
(async () => {{
  const FOLDER_TITLE = {json.dumps(_FOLDER_TITLE)};
  const desired = {desired_json};

  const style = {{
    header: "font-weight:bold;font-size:13px;color:#1a73e8",
    create: "color:#1e8e3e;font-weight:bold",
    update: "color:#e8710a;font-weight:bold",
    remove: "color:#d93025;font-weight:bold",
    skip:   "color:#80868b",
    done:   "font-weight:bold;color:#1e8e3e;font-size:12px",
    noop:   "font-weight:bold;color:#80868b;font-size:12px",
  }};

  const slugify = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  const folders = await chrome.bookmarks.search({{ title: FOLDER_TITLE }});
  const folder = folders.find(f => !f.url);
  if (!folder) {{
    console.error(`%c✗ Folder "${{FOLDER_TITLE}}" not found — create it first`, style.remove);
    return;
  }}

  const existing = await chrome.bookmarks.getChildren(folder.id);
  const counts = {{ created: 0, updated: 0, removed: 0, unchanged: 0 }};

  for (const bm of existing) {{
    const match = desired.find(d => slugify(d.title) === slugify(bm.title));
    if (!match) {{
      await chrome.bookmarks.remove(bm.id);
      console.log(`%c  - ${{bm.title}}`, style.remove);
      counts.removed++;
    }}
  }}

  for (const d of desired) {{
    const match = existing.find(e => slugify(e.title) === slugify(d.title));
    if (match) {{
      const changes = {{}};
      if (match.title !== d.title) changes.title = d.title;
      if (decodeURIComponent(match.url) !== d.url) changes.url = d.url;
      if (Object.keys(changes).length > 0) {{
        await chrome.bookmarks.update(match.id, changes);
        console.log(`%c  ↻ ${{d.title}}`, style.update);
        counts.updated++;
      }} else {{
        console.log(`%c  · ${{d.title}}`, style.skip);
        counts.unchanged++;
      }}
    }} else {{
      await chrome.bookmarks.create({{ parentId: folder.id, title: d.title, url: d.url }});
      console.log(`%c  + ${{d.title}}`, style.create);
      counts.created++;
    }}
  }}

  const bySlug = {{}};
  for (const c of await chrome.bookmarks.getChildren(folder.id)) bySlug[slugify(c.title)] = c.id;
  for (let i = 0; i < desired.length; i++) {{
    const id = bySlug[slugify(desired[i].title)];
    if (id !== undefined) await chrome.bookmarks.move(id, {{ index: i }});
  }}

  const changed = counts.created + counts.updated + counts.removed;
  if (changed > 0) {{
    const parts = [];
    if (counts.created) parts.push(`+${{counts.created}}`);
    if (counts.updated) parts.push(`↻${{counts.updated}}`);
    if (counts.removed) parts.push(`-${{counts.removed}}`);
    console.log(`%c✓ ${{parts.join(" ")}} (${{counts.unchanged}} unchanged)`, style.done);
  }} else {{
    console.log("%c· already in sync", style.noop);
  }}
}})();"""


def _log_diff(diff: _Diff) -> None:
    """Print the pending create/update/remove operations."""
    _log.info("changes detected:")
    for bm in diff.create:
        _log.info("  \033[32m+\033[0m %s", bm.title)
    for up in diff.update:
        label = f"{up.old_title} → {up.title}" if up.old_title != up.title else up.title
        _log.info("  \033[33m~\033[0m %s", label)
    for bm in diff.remove:
        _log.info("  \033[31m-\033[0m %s", bm.title)


def run(dir_path: Path, *, dry_run: bool, no_open: bool, force: bool) -> None:
    """Sync bookmarklet JS files from the given directory into Chrome."""
    desired = _get_desired(dir_path)
    diff = _compute_diff(desired, _get_chrome_bookmarklets())

    if not diff.has_changes and not force:
        _log.log(_terminal.OK, "%d bookmarklets in sync", len(desired))
        return

    if diff.has_changes:
        _log_diff(diff)

    script = _build_sync_script(desired)
    if dry_run:
        print(script)
        return

    _terminal.prompt_enter("Press Enter to copy sync script to clipboard (Ctrl+C to skip)...")
    _clipboard.copy_to_clipboard(script)
    _log.log(_terminal.OK, "sync script copied to clipboard")

    if not no_open:
        _log.info("opening chrome://bookmarks — paste into DevTools console (Cmd+Option+I)")
        _browser.open_in_chrome("chrome://bookmarks")
    else:
        _log.info("paste clipboard into DevTools console on chrome://bookmarks (Cmd+Option+I)")

    _terminal.prompt_done_or_recopy(lambda: _clipboard.copy_to_clipboard(script))
    _log.log(_terminal.OK, "done")
