"""Remove agent source roots that earlier applies owned and the desired set no longer names.

Run as ``python3 -S agent_source_cleanup.py --destination D --state F [--legacy-state L]``.
Stdin is ``{"desired": [roots], "protected": [roots]}``; every root is relative to ``D``.
The state file holds ``{"version": 1, "roots": [...]}`` and records what the last
successful run owned.
Each run removes ``state + roots(legacy) - desired - protected``, deepest first, and
writes the new state only after every removal succeeds, so a failed run retries.

Removing a root deletes every file inside it, including files a user added.
Only the root patterns below are removable.
Shared host skill directories and marketplaces are never roots.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import sys
from pathlib import Path
from typing import Dict, Iterable, Mapping, NoReturn, Optional, Sequence, cast

_NAME = r"[A-Za-z0-9_-][A-Za-z0-9._-]*"
_PLUGIN = r"[a-z0-9][a-z0-9-]*"
_MARKETPLACE_PATH = ".local/share/agent-plugins/marketplace/plugins"
_MARKETPLACE = re.escape(_MARKETPLACE_PATH)
_BUNDLE = "mkobit-dotfiles"
_ALLOWED = (
    re.compile(
        rf"^{_MARKETPLACE}/(?!{_BUNDLE}(?:/|$)){_PLUGIN}(?:/(?:claude|codex|cursor)(?:/skills/{_NAME})?)?$"
    ),
    re.compile(
        rf"^{_MARKETPLACE}/{_BUNDLE}(?:/(?:claude|codex|cursor))?/skills/{_NAME}$"
    ),
    re.compile(
        rf"^\.cursor/plugins/local/(?!{_BUNDLE}(?:/|$)){_PLUGIN}(?:/skills/{_NAME})?$"
    ),
    re.compile(rf"^\.cursor/plugins/local/{_BUNDLE}/skills/{_NAME}$"),
    re.compile(rf"^\.gemini/antigravity-cli/skills/{_NAME}$"),
)
_LEGACY_PACKAGE = re.compile(
    rf"^({_MARKETPLACE}/({_PLUGIN})/(?:claude|codex|cursor))/(.+)$"
)
_LEGACY_CURSOR = re.compile(rf"^(\.cursor/plugins/local/({_PLUGIN}))/(.+)$")
_LEGACY_SKILL = re.compile(rf"^skills/({_NAME})(?:/|$)")


class CleanupError(Exception):
    """Raised when state, input, or a removal is unsafe or fails."""


def _fail(message: str) -> NoReturn:
    raise CleanupError(f"agent-source-cleanup: {message}")


def checked_root(value: object) -> str:
    """Return ``value`` when it is a relative POSIX path that matches an allowed root."""
    if not isinstance(value, str):
        _fail(f"root is not a string: {value!r}")
    parts = value.split("/")
    if value.startswith("/") or any(part in ("", ".", "..") for part in parts):
        _fail(f"unsafe root: {value!r}")
    if not any(pattern.match(value) for pattern in _ALLOWED):
        _fail(f"root outside the allowed patterns: {value!r}")
    return value


def _roots(values: object, description: str) -> set[str]:
    if not isinstance(values, list):
        _fail(f"{description} is not a list")
    return {checked_root(value) for value in values}


def _read_json(path: Path, description: str) -> Optional[object]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as error:
        _fail(f"cannot read {description}: {error}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        _fail(f"{description} is not valid JSON: {error}")


def _retire(value: object, reason: str) -> None:
    print(
        f"agent-source-cleanup: retiring legacy path {value!r}: {reason}",
        file=sys.stderr,
    )


def load_state(path: Path) -> set[str]:
    decoded = _read_json(path, "state")
    if decoded is None:
        return set()
    if (
        not isinstance(decoded, dict)
        or decoded.get("version") != 1
        or set(decoded) != {"version", "roots"}
    ):
        _fail("state has an unsupported format")
    return _roots(cast(Dict[str, object], decoded)["roots"], "state roots")


def legacy_roots(path: Optional[Path]) -> set[str]:
    """Map the capability ownership file paths to roots; keep only provable owned ones.

    A skill file maps to its skill root; a wrapper file maps to its host or Cursor
    plugin root.
    A wrapper file of the bare-skill bundle, or any path outside the host and Cursor
    patterns, has no removable root: it is retired from state with a log line and
    never blocks cleanup.
    """
    if path is None:
        return set()
    decoded = _read_json(path, "legacy state")
    if decoded is None:
        return set()
    if (
        not isinstance(decoded, dict)
        or decoded.get("version") != 1
        or not isinstance(decoded.get("paths"), list)
    ):
        _fail("legacy state has an unsupported format")
    paths = cast("dict[str, list[object]]", decoded)["paths"]
    roots: set[str] = set()
    for value in paths:
        if not isinstance(value, str) or any(
            part in ("", ".", "..") for part in value.split("/")
        ):
            _retire(value, "unsafe path")
            continue
        for pattern in (_LEGACY_PACKAGE, _LEGACY_CURSOR):
            match = pattern.match(value)
            if not match:
                continue
            host_root, plugin, rest = match.group(1), match.group(2), match.group(3)
            skill = _LEGACY_SKILL.match(rest)
            candidate = f"{host_root}/skills/{skill.group(1)}" if skill else host_root
            if skill is None and plugin == _BUNDLE:
                break
            if any(allowed.match(candidate) for allowed in _ALLOWED):
                roots.add(candidate)
            break
        else:
            _retire(value, "outside the host and Cursor plugin patterns")
    return roots


def _reject_symlink_components(destination: Path, relative: str) -> None:
    candidate = destination
    if destination.is_symlink():
        _fail(f"refusing symlinked destination: {destination}")
    for component in relative.split("/"):
        candidate = candidate / component
        try:
            mode = candidate.lstat().st_mode
        except FileNotFoundError:
            return
        if stat.S_ISLNK(mode):
            _fail(f"refusing symlinked cleanup path: {candidate}")


def _remove_entry(path: Path) -> None:
    mode = path.lstat().st_mode
    if stat.S_ISDIR(mode):
        shutil.rmtree(str(path))
    else:
        path.unlink()


def _remove_root(destination: Path, root: str, keep: Sequence[str]) -> None:
    """Remove ``root``, sparing the kept roots that lie inside it and their ancestors."""
    target = destination / root
    try:
        target.lstat()
    except FileNotFoundError:
        return
    inside = [kept for kept in keep if kept.startswith(root + "/")]
    if not inside:
        _remove_entry(target)
        return
    _remove_children(destination, root, inside)


def _prune_empty_parents(destination: Path, root: str, keep: Sequence[str]) -> None:
    """Remove empty directories above a removed plugin root, up to and including its plugin root."""
    parts = root.split("/")
    if root.startswith(_MARKETPLACE_PATH + "/"):
        plugin_length = len(_MARKETPLACE_PATH.split("/")) + 1
    elif root.startswith(".cursor/plugins/local/"):
        plugin_length = 4
    else:
        return
    if parts[plugin_length - 1] == _BUNDLE:
        return
    for length in range(len(parts) - 1, plugin_length - 1, -1):
        parent = "/".join(parts[:length])
        if parent in keep:
            return
        try:
            (destination / parent).rmdir()
        except OSError:
            return


def _remove_children(destination: Path, directory: str, keep: Sequence[str]) -> None:
    path = destination / directory
    if not stat.S_ISDIR(path.lstat().st_mode):
        _remove_entry(path)
        return
    for child in sorted(os.listdir(str(path))):
        relative = f"{directory}/{child}"
        if relative in keep:
            continue
        below = [kept for kept in keep if kept.startswith(relative + "/")]
        if below:
            _remove_children(destination, relative, below)
        else:
            _remove_entry(destination / relative)


def _write_state(destination: Path, state: Path, roots: Iterable[str]) -> None:
    relative = state.relative_to(destination).as_posix()
    _reject_symlink_components(destination, relative)
    state.parent.mkdir(parents=True, exist_ok=True)
    temporary = state.with_name(state.name + ".tmp")
    temporary.write_text(
        json.dumps({"version": 1, "roots": sorted(roots)}) + "\n", encoding="utf-8"
    )
    os.replace(str(temporary), str(state))


def cleanup(
    destination: Path,
    state: Path,
    legacy: Optional[Path],
    payload: Mapping[str, object],
) -> list[str]:
    """Remove stale roots, then commit the desired set; return the removed roots."""
    desired = _roots(payload.get("desired"), "desired")
    protected = _roots(payload.get("protected"), "protected")
    previous = load_state(state) | legacy_roots(legacy)
    stale = sorted(
        previous - desired - protected, key=lambda root: (-root.count("/"), root)
    )
    keep = sorted(desired | protected)
    for root in stale:
        _reject_symlink_components(destination, root)
    for root in stale:
        _remove_root(destination, root, keep)
        _prune_empty_parents(destination, root, keep)
    _write_state(destination, state, desired)
    if legacy is not None:
        try:
            legacy.unlink()
        except FileNotFoundError:
            pass
    return stale


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--legacy-state", type=Path)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            _fail("input is not an object")
        cleanup(args.destination, args.state, args.legacy_state, payload)
    except (CleanupError, OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
