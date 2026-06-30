"""browser-sync: sync browser config via DevTools console paste.

Subcommands:
  shortcuts <toml>              Chrome site search shortcuts (SearchEnginesBrowserProxy).
  vimium <toml> <keymappings>   Vimium search engines + key mappings (chrome.storage.sync).
  bookmarklets <dir>            Bookmarklet JS files to Chrome bookmarks (chrome.bookmarks).

Browser targeting: --chrome (default) and/or --firefox (not yet supported).
"""

import argparse
import logging
from pathlib import Path

from browser_sync import _browser, _terminal, bookmarklets, shortcuts, vimium

_log = logging.getLogger(__name__)


def _add_browser_flags(parser: argparse.ArgumentParser) -> None:
    """Add the shared --chrome/--firefox target flags to a subparser."""
    parser.add_argument("--chrome", action="store_true", help="Target Google Chrome (default).")
    parser.add_argument("--firefox", action="store_true", help="Target Firefox (not yet supported).")


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser with one subparser per sync flow."""
    parser = argparse.ArgumentParser(prog="browser-sync", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    shortcuts_parser = sub.add_parser("shortcuts", help="Sync Chrome site search shortcuts.")
    shortcuts_parser.add_argument("toml_path", type=Path, help="Path to search-engines.toml")
    shortcuts_parser.add_argument("--prune", action="store_true", help="Show which shortcuts would be removed.")
    shortcuts_parser.add_argument("--confirm", action="store_true", help="With --prune, actually execute removals.")
    shortcuts_parser.add_argument("--dry-run", action="store_true", help="Print script without copying.")
    shortcuts_parser.add_argument("--no-open", action="store_true", help="Don't open the browser.")
    _add_browser_flags(shortcuts_parser)

    vimium_parser = sub.add_parser("vimium", help="Sync Vimium search engines and key mappings.")
    vimium_parser.add_argument("toml_path", type=Path, help="Path to search-engines.toml")
    vimium_parser.add_argument("keymappings_path", type=Path, help="Path to key-mappings.txt")
    vimium_parser.add_argument("--dry-run", action="store_true", help="Print script without copying.")
    vimium_parser.add_argument("--no-open", action="store_true", help="Don't open the browser.")
    _add_browser_flags(vimium_parser)

    bookmarklets_parser = sub.add_parser("bookmarklets", help="Sync bookmarklet JS files to Chrome bookmarks.")
    bookmarklets_parser.add_argument("dir_path", type=Path, help="Directory of *.js bookmarklet files")
    bookmarklets_parser.add_argument("--force", action="store_true", help="Run even if source matches Chrome's state.")
    bookmarklets_parser.add_argument("--dry-run", action="store_true", help="Print script without copying.")
    bookmarklets_parser.add_argument("--no-open", action="store_true", help="Don't open the browser.")
    _add_browser_flags(bookmarklets_parser)

    return parser


def main() -> None:
    """Entry point for the browser-sync CLI."""
    _terminal.setup_logging()
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "shortcuts" and args.confirm and not args.prune:
        parser.error("--confirm requires --prune")

    targets = _browser.resolve_targets(chrome=args.chrome, firefox=args.firefox)
    if _browser.Browser.FIREFOX in targets:
        _log.warning("firefox sync not yet supported — skipping")
    if _browser.Browser.CHROME not in targets:
        return

    if args.command == "shortcuts":
        shortcuts.run(
            args.toml_path,
            prune=args.prune,
            confirm=args.confirm,
            dry_run=args.dry_run,
            no_open=args.no_open,
        )
    elif args.command == "vimium":
        vimium.run(args.toml_path, args.keymappings_path, dry_run=args.dry_run, no_open=args.no_open)
    elif args.command == "bookmarklets":
        bookmarklets.run(args.dir_path, dry_run=args.dry_run, no_open=args.no_open, force=args.force)


if __name__ == "__main__":
    main()
