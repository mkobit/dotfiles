"""Discover authored agent sources and describe them as an inventory.

Standard library only and Python 3.8 compatible: chezmoi runs this before
uv or mise exist.
Discovery reads sources and never writes.
Projection maps the inventory to chezmoi source entries, and ``prepare``
publishes them all-or-nothing into the source root.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence


class AgentSourceError(RuntimeError):
    """Raised when authored agent sources are invalid."""


SCHEMA = 1
GENERATOR = "skill_filter.agent_sources"
RESERVED_PLUGIN_NAME = "mkobit-dotfiles"
HOSTS = ("claude", "codex", "cursor")
_MARKETPLACE = ".local/share/agent-plugins/marketplace/plugins"
BARE_VIEWS = {
    "portable": f"{_MARKETPLACE}/{RESERVED_PLUGIN_NAME}/skills",
    "claude": f"{_MARKETPLACE}/{RESERVED_PLUGIN_NAME}/claude/skills",
    "codex": f"{_MARKETPLACE}/{RESERVED_PLUGIN_NAME}/codex/skills",
    "cursor": f"{_MARKETPLACE}/{RESERVED_PLUGIN_NAME}/cursor/skills",
    "cursor_local": f".cursor/plugins/local/{RESERVED_PLUGIN_NAME}/skills",
    "antigravity": ".gemini/antigravity-cli/skills",
}

_BARE_NAME = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]*$")
_PLUGIN_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_SEGMENT = r"[a-z0-9]+(-[a-z0-9]+)*"
_SOURCE_DIR = re.compile(rf"^src/{_SEGMENT}(/{_SEGMENT})*$")
_IDENTITY_KEYS = frozenset(
    {
        "description",
        "name",
        "skills_source_dir",
        "native_source",
        "native_wrappers",
        "author",
        "interface",
    }
)
_SKIPPED_NAMES = frozenset(
    {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".DS_Store"}
)
_SKIPPED_SUFFIXES = (".pyc", ".pyo")
# Chezmoi parses attribute prefixes in a fixed order, verified with a probe of
# chezmoi 2.72 against https://www.chezmoi.io/reference/source-state-attributes/.
# Each group matches at most once; a final dot_ or literal_ ends the parse.
_DIR_ORDER = (("remove_",), ("external_",), ("exact_",), ("private_",), ("readonly_",))
_FILE_ORDER = (
    ("create_", "modify_", "remove_", "run_", "symlink_"),
    ("once_", "onchange_"),
    ("before_", "after_"),
    ("encrypted_",),
    ("private_",),
    ("readonly_",),
    ("empty_",),
    ("executable_",),
)
_NATIVE_FORBIDDEN = (
    "create_",
    "modify_",
    "remove_",
    "run_",
    "symlink_",
    "external_",
    "encrypted_",
    "once_",
    "onchange_",
    "before_",
    "after_",
)


@dataclass(frozen=True)
class PluginIdentity:
    """Parsed ``plugin.json`` of one plugin directory."""

    directory: Path
    name: str
    description: str
    skills_source_dir: Optional[Path]
    native_source: bool
    native_wrappers: tuple[str, ...]
    author: Optional[dict[str, Any]]
    interface: Optional[dict[str, Any]]


@dataclass(frozen=True)
class Tree:
    """Files and directories of one source tree, keyed by target path."""

    dirs: tuple[str, ...]
    files: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class PluginSource:
    identity: PluginIdentity
    skills: dict[str, Tree]
    wrappers: dict[str, Tree]
    components: dict[str, dict[str, str]]


@dataclass
class Inventory:
    authored: Path
    bare_skills: dict[str, Tree] = field(default_factory=dict)
    plugins: dict[str, PluginSource] = field(default_factory=dict)

    @property
    def root(self) -> Path:
        """Directory that inventory paths are relative to: the parent of ``chezmoi/``.

        It is the authored root itself, so no path names the directory above it and a
        renamed candidate tree stays valid.
        """
        return self.authored


def _is_skipped(name: str) -> bool:
    return name in _SKIPPED_NAMES or name.endswith(_SKIPPED_SUFFIXES)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _check_target_name(name: str, path: Path) -> None:
    if not name:
        raise AgentSourceError(f"entry has an empty target name: {path}")
    if name.startswith(".chezmoi"):
        raise AgentSourceError(f"entry targets a reserved chezmoi name: {path}")


def _strip_ordered(name: str, is_dir: bool) -> tuple[str, list[str], bool]:
    """Strip chezmoi prefixes in chezmoi's fixed order.

    Return the remainder, the matched attribute prefixes, and whether a final
    ``dot_`` or ``literal_`` ended the parse, so the remainder is literal.
    """
    matched: list[str] = []
    remainder = name
    for group in _DIR_ORDER if is_dir else _FILE_ORDER:
        prefix = next((p for p in group if remainder.startswith(p)), None)
        if prefix is not None:
            matched.append(prefix)
            remainder = remainder[len(prefix) :]
    if remainder.startswith("dot_"):
        return "." + remainder[len("dot_") :], matched, True
    if remainder.startswith("literal_"):
        return remainder[len("literal_") :], matched, True
    return remainder, matched, False


def _parse_native_name(
    name: str, path: Path, is_dir: bool
) -> tuple[str, dict[str, bool]]:
    """Return the target name and attributes of a native chezmoi source name.

    Prefixes must follow chezmoi's order, so the parsed target always equals
    the target chezmoi deploys.
    """
    remainder, matched, literal = _strip_ordered(name, is_dir)
    leftover = (
        None
        if literal
        else next((p for p in _CHEZMOI_PREFIXES if remainder.startswith(p)), None)
    )
    if any(prefix in _NATIVE_FORBIDDEN for prefix in matched) or (
        leftover in _NATIVE_FORBIDDEN
    ):
        raise AgentSourceError(f"native entry uses a forbidden prefix: {path}")
    if leftover is not None:
        raise AgentSourceError(
            f"native entry prefixes are out of chezmoi order or invalid for a "
            f"{'directory' if is_dir else 'file'}: {path}"
        )
    flags = {
        "executable": "executable_" in matched,
        "empty": "empty_" in matched,
        "template": False,
    }
    if not is_dir:
        if remainder.endswith(".literal"):
            raise AgentSourceError(f"native entry uses a .literal suffix: {path}")
        if remainder.endswith(".tmpl"):
            remainder = remainder[: -len(".tmpl")]
            flags["template"] = True
    _check_target_name(remainder, path)
    return remainder, flags


def _scan_tree(root: Path, base: Path, native: bool) -> Tree:
    """Hash every file below ``root``; reject symlinks and special files."""
    dirs: list[str] = []
    files: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()

    def claim(target: str, entry: Path) -> None:
        if target in seen:
            raise AgentSourceError(f"two sources map to {target}: {entry}")
        seen.add(target)

    def walk(directory: Path, target_prefix: str) -> None:
        for entry in sorted(directory.iterdir(), key=lambda item: item.name):
            if _is_skipped(entry.name):
                continue
            mode = entry.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise AgentSourceError(f"source symlink is not allowed: {entry}")
            if stat.S_ISDIR(mode):
                if native:
                    name, _ = _parse_native_name(entry.name, entry, True)
                else:
                    name = entry.name
                    _check_target_name(name, entry)
                target = target_prefix + name
                claim(target, entry)
                dirs.append(target)
                walk(entry, target + "/")
            elif stat.S_ISREG(mode):
                if native and entry.name == ".keep":
                    continue
                template = False
                executable = False
                empty = False
                name = entry.name
                if native:
                    name, flags = _parse_native_name(entry.name, entry, False)
                    template = flags["template"]
                    executable = flags["executable"]
                    empty = flags["empty"]
                else:
                    executable = bool(mode & 0o111)
                    if name.endswith(".tmpl"):
                        name = name[: -len(".tmpl")]
                        template = True
                    empty = entry.stat().st_size == 0
                    _check_target_name(name, entry)
                target = target_prefix + name
                claim(target, entry)
                files[target] = {
                    "source": _relative(entry, base),
                    "sha256": hashlib.sha256(entry.read_bytes()).hexdigest(),
                    "executable": executable,
                    "template": template,
                    "empty": empty,
                }
            else:
                raise AgentSourceError(f"unsupported source file type: {entry}")

    walk(root, "")
    return Tree(dirs=tuple(sorted(dirs)), files=files)


def _reject_symlink(path: Path) -> None:
    if path.is_symlink():
        raise AgentSourceError(f"source symlink is not allowed: {path}")


def _is_real_dir(path: Path) -> bool:
    return path.is_dir() and not path.is_symlink()


def _scan_skills(
    skills_root: Path, base: Path, native: bool, name_re: Any
) -> dict[str, Tree]:
    skills: dict[str, Tree] = {}
    for child in sorted(skills_root.iterdir(), key=lambda item: item.name):
        if _is_skipped(child.name):
            continue
        _reject_symlink(child)
        if not child.is_dir():
            continue
        if native:
            name, _ = _parse_native_name(child.name, child, True)
        else:
            name = child.name
        if not name_re.match(name) or name in {".", ".."}:
            raise AgentSourceError(f"invalid skill name: {child}")
        tree = _scan_tree(child, base, native)
        if "SKILL.md" not in tree.files:
            raise AgentSourceError(f"skill directory missing SKILL.md: {child}")
        skills[name] = tree
    return skills


def _resolve_skills_source_dir(
    plugin_dir: Path, authored: Path, value: object
) -> Optional[Path]:
    if value is None:
        default = plugin_dir / "skills"
        _reject_symlink(default)
        return default if _is_real_dir(default) else None
    if not isinstance(value, str) or not _SOURCE_DIR.match(value):
        raise AgentSourceError(f"invalid skills_source_dir in {plugin_dir}: {value!r}")
    # The leading src/ names the authored root, which is not named src in an
    # assembled overlay tree, so the remainder resolves inside the authored root.
    current = authored
    for part in value.split("/")[1:]:
        current = current / part
        if current.is_symlink():
            raise AgentSourceError(f"skills_source_dir has a symlink: {current}")
    if not current.is_dir():
        raise AgentSourceError(f"skills_source_dir is not a directory: {current}")
    real_authored = authored.resolve()
    if (
        real_authored != current.resolve()
        and real_authored not in current.resolve().parents
    ):
        raise AgentSourceError(f"skills_source_dir escapes authored root: {value}")
    return current


def _json_object(
    raw: dict[str, Any], key: str, plugin_dir: Path
) -> Optional[dict[str, Any]]:
    value = raw.get(key)
    if value is not None and not isinstance(value, dict):
        raise AgentSourceError(f"{key} must be an object in {plugin_dir}")
    return value


def load_identity(plugin_dir: Path, authored: Path) -> PluginIdentity:
    """Parse and validate ``plugin_dir/plugin.json``."""
    identity_path = plugin_dir / "plugin.json"
    if not identity_path.is_file():
        raise AgentSourceError(f"missing plugin identity: {identity_path}")
    try:
        raw = json.loads(identity_path.read_text(encoding="utf-8"))
    except ValueError as error:
        raise AgentSourceError(f"invalid JSON in {identity_path}: {error}") from error
    if not isinstance(raw, dict):
        raise AgentSourceError(f"plugin identity must be an object: {identity_path}")
    unknown = sorted(set(raw) - _IDENTITY_KEYS)
    if unknown:
        raise AgentSourceError(f"unknown identity key {unknown} in {identity_path}")
    description = raw.get("description")
    if not isinstance(description, str) or not description.strip():
        raise AgentSourceError(f"description is required in {identity_path}")
    name = raw.get("name", plugin_dir.name)
    if not isinstance(name, str) or not _PLUGIN_NAME.match(name):
        raise AgentSourceError(f"invalid plugin name {name!r} in {identity_path}")
    if name == RESERVED_PLUGIN_NAME:
        raise AgentSourceError(f"plugin name {name} is reserved: {identity_path}")
    native_source = raw.get("native_source", False)
    if not isinstance(native_source, bool):
        raise AgentSourceError(f"native_source must be a bool in {identity_path}")
    wrappers = raw.get("native_wrappers", [])
    if (
        not isinstance(wrappers, list)
        or any(host not in HOSTS for host in wrappers)
        or len(set(wrappers)) != len(wrappers)
    ):
        raise AgentSourceError(
            f"native_wrappers must list unique hosts of {HOSTS} in {identity_path}"
        )
    return PluginIdentity(
        directory=plugin_dir,
        name=name,
        description=description,
        skills_source_dir=_resolve_skills_source_dir(
            plugin_dir, authored, raw.get("skills_source_dir")
        ),
        native_source=native_source,
        native_wrappers=tuple(wrappers),
        author=_json_object(raw, "author", plugin_dir),
        interface=_json_object(raw, "interface", plugin_dir),
    )


def _load_wrappers(
    identity: PluginIdentity, base: Path
) -> tuple[dict[str, Tree], dict[str, dict[str, str]]]:
    wrappers: dict[str, Tree] = {}
    components: dict[str, dict[str, str]] = {}
    root = identity.directory / "wrappers"
    _reject_symlink(root)
    if not root.is_dir():
        return wrappers, components
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        if _is_skipped(child.name):
            continue
        if child.name not in HOSTS or not _is_real_dir(child):
            raise AgentSourceError(f"unknown wrapper entry: {child}")
        native = identity.native_source or child.name in identity.native_wrappers
        tree = _scan_tree(child, base, native)
        wrappers[child.name] = tree
        found: dict[str, str] = {}
        if ".mcp.json" in tree.files:
            found["mcpServers"] = "./.mcp.json"
        if "rules" in tree.dirs:
            found["rules"] = "./rules"
        components[child.name] = found
    return wrappers, components


def _load_plugin(identity: PluginIdentity, base: Path) -> PluginSource:
    skills: dict[str, Tree] = {}
    if identity.skills_source_dir is not None:
        skills = _scan_skills(
            identity.skills_source_dir, base, identity.native_source, _PLUGIN_NAME
        )
    wrappers, components = _load_wrappers(identity, base)
    return PluginSource(identity, skills, wrappers, components)


def discover(source_root: Path) -> Inventory:
    """Discover authored roots beside ``source_root``; read only.

    A symlink anywhere in an authored tree, including root-level files, fails.
    """
    authored = source_root.parent
    base = authored
    inventory = Inventory(authored=authored)
    skills_root = authored / "ai" / "skills"
    _reject_symlink(skills_root)
    if skills_root.is_dir():
        inventory.bare_skills = _scan_skills(skills_root, base, False, _BARE_NAME)
    plugins_root = authored / "overlay-plugins"
    _reject_symlink(plugins_root)
    if plugins_root.is_dir():
        for child in sorted(plugins_root.iterdir(), key=lambda item: item.name):
            if _is_skipped(child.name):
                continue
            _reject_symlink(child)
            if not child.is_dir():
                continue
            if child.name.startswith("."):
                raise AgentSourceError(f"plugin directory name is hidden: {child}")
            identity = load_identity(child, authored)
            if identity.name in inventory.plugins:
                raise AgentSourceError(f"duplicate plugin name: {identity.name}")
            inventory.plugins[identity.name] = _load_plugin(identity, base)
    return inventory


def _digest(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _tree_digest(tree: Tree) -> str:
    """Digest target paths and content attributes, never source locations."""
    files = {
        target: [
            record["sha256"],
            record["executable"],
            record["empty"],
            record["template"],
        ]
        for target, record in tree.files.items()
    }
    return _digest({"dirs": list(tree.dirs), "files": files})


def _tree_document(tree: Tree) -> dict[str, Any]:
    return {
        "dirs": list(tree.dirs),
        "files": {target: tree.files[target] for target in sorted(tree.files)},
    }


def inventory_document(inventory: Inventory) -> dict[str, Any]:
    """Return the JSON document consumed by chezmoi templates."""
    base = inventory.root
    bare: dict[str, Any] = {}
    for name, tree in sorted(inventory.bare_skills.items()):
        bare[name] = {
            "source_dir": f"ai/skills/{name}",
            "native": False,
            **_tree_document(tree),
            "digest": _tree_digest(tree),
        }
    plugins: dict[str, Any] = {}
    for name, plugin in sorted(inventory.plugins.items()):
        identity = plugin.identity
        skills = {
            skill: {**_tree_document(tree), "digest": _tree_digest(tree)}
            for skill, tree in sorted(plugin.skills.items())
        }
        wrappers = {
            host: {
                **_tree_document(tree),
                "components": plugin.components[host],
            }
            for host, tree in sorted(plugin.wrappers.items())
        }
        content = {
            "description": identity.description,
            "author": identity.author,
            "interface": identity.interface,
            "native_source": identity.native_source,
            "native_wrappers": list(identity.native_wrappers),
            "skills": {skill: entry["digest"] for skill, entry in skills.items()},
            "wrappers": {
                host: [_tree_digest(plugin.wrappers[host]), entry["components"]]
                for host, entry in wrappers.items()
            },
        }
        root = f"{_MARKETPLACE}/{name}"
        plugins[name] = {
            "source_dir": _relative(identity.directory, base),
            "skills_source_dir": (
                None
                if identity.skills_source_dir is None
                else _relative(identity.skills_source_dir, base)
            ),
            "description": identity.description,
            "author": identity.author,
            "interface": identity.interface,
            "native_source": identity.native_source,
            "native_wrappers": list(identity.native_wrappers),
            "views": {
                "claude": f"{root}/claude",
                "codex": f"{root}/codex",
                "cursor": f"{root}/cursor",
                "cursor_local": f".cursor/plugins/local/{name}",
            },
            "skills": skills,
            "wrappers": wrappers,
            "digest": _digest(content),
        }
    body = {
        "bare_views": dict(BARE_VIEWS),
        "bare_skills": bare,
        "plugins": plugins,
    }
    digest_input = {
        "bare_views": body["bare_views"],
        "bare_skills": {name: entry["digest"] for name, entry in bare.items()},
        "plugins": {name: entry["digest"] for name, entry in plugins.items()},
    }
    return {
        "agent_source_inventory": {
            "schema": SCHEMA,
            "generator": GENERATOR,
            "source_digest": _digest(digest_input),
            **body,
        }
    }


# Projection: inventory to chezmoi source entries.

INVENTORY_PATH = ".chezmoidata/agent-source-inventory.json"
MANIFEST_NAME = ".agent-sources-manifest.json"
LOCK_NAME = ".agent-sources.lock"
STAGING_NAME = ".agent-sources.staging"
MANIFEST_SCHEMA = 1
_MARKETPLACE_SOURCE = "dot_local/share/agent-plugins/marketplace/plugins"
_CURSOR_LOCAL_SOURCE = "dot_cursor/plugins/local"
_ANTIGRAVITY_SOURCE = "dot_gemini/antigravity-cli/skills"
_BARE_PACKAGE_SOURCE = f"{_MARKETPLACE_SOURCE}/{RESERVED_PLUGIN_NAME}"
BARE_SOURCE_VIEWS = {
    "portable": f"{_BARE_PACKAGE_SOURCE}/skills",
    "claude": f"{_BARE_PACKAGE_SOURCE}/claude/skills",
    "codex": f"{_BARE_PACKAGE_SOURCE}/codex/skills",
    "cursor": f"{_BARE_PACKAGE_SOURCE}/cursor/skills",
    "cursor_local": f"{_CURSOR_LOCAL_SOURCE}/{RESERVED_PLUGIN_NAME}/skills",
    "antigravity": _ANTIGRAVITY_SOURCE,
}
_IGNORE_NAME = ".chezmoiignore.tmpl"
_CONTROL_NAMES = (".chezmoiignore", ".chezmoiignore.tmpl")
_FIXED_GENERATED = frozenset(
    {
        INVENTORY_PATH,
        f"{_MARKETPLACE_SOURCE}/{_IGNORE_NAME}",
        f"{_CURSOR_LOCAL_SOURCE}/{_IGNORE_NAME}",
        *BARE_SOURCE_VIEWS.values(),
    }
)
_GENERATED_PLUGIN_ROOT = re.compile(
    rf"^({re.escape(_MARKETPLACE_SOURCE)}|{re.escape(_CURSOR_LOCAL_SOURCE)})"
    r"/exact_[a-z0-9][a-z0-9-]*$"
)
_CHEZMOI_PREFIXES = (
    "after_",
    "before_",
    "create_",
    "dot_",
    "empty_",
    "encrypted_",
    "exact_",
    "executable_",
    "external_",
    "literal_",
    "modify_",
    "once_",
    "onchange_",
    "private_",
    "readonly_",
    "remove_",
    "run_",
    "symlink_",
)
_FILE_MODE = 0o644
_EXECUTABLE_MODE = 0o755
_DIR_MODE = 0o755


@dataclass(frozen=True)
class Entry:
    """One generated source entry: a directory, or a file with bytes and mode."""

    kind: str
    data: bytes = b""
    mode: int = _DIR_MODE


_DIR = Entry("dir")


def encode_name(
    target_name: str,
    *,
    kind: str,
    executable: bool = False,
    empty: bool = False,
    template: bool = False,
    exact: bool = False,
) -> str:
    """Return the chezmoi source name for a literal target name."""
    if kind not in ("file", "dir"):
        raise ValueError(f"unknown entry kind: {kind!r}")
    if (
        target_name in ("", ".", "..")
        or "/" in target_name
        or "\\" in target_name
        or target_name.endswith(".literal")
    ):
        raise AgentSourceError(f"unsafe target name: {target_name!r}")
    if kind == "file" and not template and target_name.endswith(".tmpl"):
        raise AgentSourceError(f"plain file target ends with .tmpl: {target_name!r}")
    if target_name.startswith("."):
        base = "dot_" + target_name[1:]
    elif target_name.startswith(_CHEZMOI_PREFIXES):
        base = "literal_" + target_name
    else:
        base = target_name
    if kind == "dir":
        return ("exact_" if exact else "") + base
    return (
        ("empty_" if empty else "")
        + ("executable_" if executable else "")
        + base
        + (".tmpl" if template else "")
    )


def source_target_name(source_name: str, *, is_dir: bool = False) -> str:
    """Return the target name chezmoi deploys for a source name.

    Prefixes are stripped in chezmoi's order; files also lose ``.literal`` or
    ``.tmpl`` (then ``.literal``), and directories keep their suffixes.
    """
    name, _, _ = _strip_ordered(source_name, is_dir)
    if is_dir:
        return name
    if name.endswith(".literal"):
        return name[: -len(".literal")]
    if name.endswith(".tmpl"):
        name = name[: -len(".tmpl")]
        if name.endswith(".literal"):
            name = name[: -len(".literal")]
    return name


def _source_target_path(path: str, is_dir: bool) -> str:
    parts = path.split("/")
    names = [source_target_name(part, is_dir=True) for part in parts[:-1]]
    return "/".join([*names, source_target_name(parts[-1], is_dir=is_dir)])


def is_generated_path(path: str) -> bool:
    """Return whether ``path`` is a top-level path that preparation may own."""
    return path in _FIXED_GENERATED or bool(_GENERATED_PLUGIN_ROOT.match(path))


def _add_dir(plan: dict[str, Entry], path: str) -> None:
    existing = plan.get(path)
    if existing is None:
        plan[path] = _DIR
    elif existing.kind != "dir":
        raise AgentSourceError(f"two sources map to {path}")


def _add_file(plan: dict[str, Entry], path: str, entry: Entry) -> None:
    if path in plan:
        raise AgentSourceError(f"two sources map to {path}")
    plan[path] = entry


def _text(text: str) -> Entry:
    return Entry("file", text.encode("utf-8"), _FILE_MODE)


def _ignore_entry(view: str) -> Entry:
    return _text(
        '{{- includeTemplate "ai/agent-source-ignore" '
        f'(dict "root" . "view" "{view}") -}}}}\n'
    )


def _manifest_entry(name: str, host: str) -> Entry:
    return _text(
        '{{- includeTemplate "ai/authored-plugin-manifest" '
        f'(dict "root" . "name" "{name}" "host" "{host}") -}}}}\n'
    )


def _encode_dirs(target: str) -> str:
    return "/".join(
        encode_name(part, kind="dir", exact=True) for part in target.split("/")
    )


def _source_bytes(base: Path, record: dict[str, Any]) -> bytes:
    data = (base / record["source"]).read_bytes()
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise AgentSourceError(f"source changed during preparation: {record['source']}")
    return data


def _add_literal_tree(
    plan: dict[str, Entry], root: str, tree: Tree, base: Path
) -> None:
    """Encode a literal tree; every directory at or below ``root`` is exact."""
    _add_dir(plan, root)
    for target in tree.dirs:
        _add_dir(plan, f"{root}/{_encode_dirs(target)}")
    for target, record in sorted(tree.files.items()):
        parent, _, name = target.rpartition("/")
        directory = f"{root}/{_encode_dirs(parent)}" if parent else root
        source_name = encode_name(
            name,
            kind="file",
            executable=record["executable"],
            empty=record["empty"] and not record["template"],
            template=record["template"],
        )
        mode = _EXECUTABLE_MODE if record["executable"] else _FILE_MODE
        _add_file(
            plan,
            f"{directory}/{source_name}",
            Entry("file", _source_bytes(base, record), mode),
        )


def _add_native_tree(plan: dict[str, Entry], root: str, source_dir: Path) -> None:
    """Copy a native tree verbatim, with modes; discovery already validated it."""
    _add_dir(plan, root)
    for entry in sorted(source_dir.iterdir(), key=lambda item: item.name):
        if _is_skipped(entry.name):
            continue
        mode = entry.lstat().st_mode
        path = f"{root}/{entry.name}"
        if stat.S_ISLNK(mode):
            raise AgentSourceError(f"source symlink is not allowed: {entry}")
        if stat.S_ISDIR(mode):
            _add_native_tree(plan, path, entry)
        elif stat.S_ISREG(mode):
            _add_file(plan, path, Entry("file", entry.read_bytes(), mode & 0o777))
        else:
            raise AgentSourceError(f"unsupported source file type: {entry}")


def _check_wrapper(plugin: PluginSource, host: str, tree: Tree) -> None:
    manifest = f".{host}-plugin/plugin.json"
    for target in (*tree.dirs, *tree.files):
        if target == "skills" or target.startswith("skills/"):
            raise AgentSourceError(
                f"wrapper entry under skills/ in {plugin.identity.name}/{host}: {target}"
            )
        if target == manifest:
            raise AgentSourceError(
                f"wrapper defines the generated manifest in "
                f"{plugin.identity.name}/{host}: {target}"
            )


def _add_plugin_view(
    plan: dict[str, Entry], root: str, plugin: PluginSource, host: str, base: Path
) -> None:
    identity = plugin.identity
    _add_dir(plan, root)
    wrapper = plugin.wrappers.get(host)
    if wrapper is not None:
        _check_wrapper(plugin, host, wrapper)
        if identity.native_source or host in identity.native_wrappers:
            _add_native_tree(plan, root, identity.directory / "wrappers" / host)
        else:
            _add_literal_tree(plan, root, wrapper, base)
    manifest_dir = f"{root}/{encode_name(f'.{host}-plugin', kind='dir', exact=True)}"
    _add_dir(plan, manifest_dir)
    _add_file(
        plan, f"{manifest_dir}/plugin.json.tmpl", _manifest_entry(identity.name, host)
    )
    if not plugin.skills:
        return
    skills_dir = f"{root}/{encode_name('skills', kind='dir', exact=True)}"
    _add_dir(plan, skills_dir)
    for skill, tree in sorted(plugin.skills.items()):
        if identity.native_source:
            source_dir = (base / tree.files["SKILL.md"]["source"]).parent
            name = source_dir.name
            emitted = name if name.startswith("exact_") else "exact_" + name
            _add_native_tree(plan, f"{skills_dir}/{emitted}", source_dir)
        else:
            encoded = encode_name(skill, kind="dir", exact=True)
            _add_literal_tree(plan, f"{skills_dir}/{encoded}", tree, base)


def _check_plan_targets(plan: dict[str, Entry]) -> None:
    seen: dict[str, str] = {}
    for path in sorted(plan):
        target = _source_target_path(path, plan[path].kind == "dir")
        other = seen.setdefault(target, path)
        if other != path:
            raise AgentSourceError(f"two sources map to {target}: {other} and {path}")


def inventory_text(inventory: Inventory) -> str:
    return json.dumps(inventory_document(inventory), indent=2, sort_keys=True) + "\n"


def plan_projection(source_root: Path, inventory: Inventory) -> dict[str, Entry]:
    """Map generated ``source_root``-relative paths to entries.

    Views exist only for discovered content: bare skill views when there is a
    bare skill, plugin views per plugin, and an ignore file per populated view.
    """
    del source_root  # Paths are relative; the argument fixes the contract.
    base = inventory.root
    plan: dict[str, Entry] = {INVENTORY_PATH: _text(inventory_text(inventory))}
    if inventory.bare_skills:
        for root in BARE_SOURCE_VIEWS.values():
            _add_dir(plan, root)
            for name, tree in sorted(inventory.bare_skills.items()):
                encoded = encode_name(name, kind="dir", exact=True)
                _add_literal_tree(plan, f"{root}/{encoded}", tree, base)
        _add_file(
            plan, f"{_ANTIGRAVITY_SOURCE}/{_IGNORE_NAME}", _ignore_entry("antigravity")
        )
    if inventory.bare_skills or inventory.plugins:
        _add_file(
            plan,
            f"{_MARKETPLACE_SOURCE}/{_IGNORE_NAME}",
            _ignore_entry("marketplace-plugins"),
        )
        _add_file(
            plan,
            f"{_CURSOR_LOCAL_SOURCE}/{_IGNORE_NAME}",
            _ignore_entry("cursor-local"),
        )
    for name, plugin in sorted(inventory.plugins.items()):
        encoded = encode_name(name, kind="dir", exact=True)
        market_root = f"{_MARKETPLACE_SOURCE}/{encoded}"
        _add_dir(plan, market_root)
        for host in HOSTS:
            host_root = f"{market_root}/{encode_name(host, kind='dir', exact=True)}"
            _add_plugin_view(plan, host_root, plugin, host, base)
        _add_plugin_view(
            plan, f"{_CURSOR_LOCAL_SOURCE}/{encoded}", plugin, "cursor", base
        )
    _check_plan_targets(plan)
    return plan


def top_level_paths(plan: dict[str, Entry]) -> list[str]:
    """Return the sorted generated paths that own every planned entry."""
    roots = sorted(path for path in plan if is_generated_path(path))
    for path in plan:
        if not any(path == root or path.startswith(root + "/") for root in roots):
            raise AgentSourceError(f"planned entry outside generated paths: {path}")
    return roots


def digest(plan: dict[str, Entry]) -> str:
    """Digest every planned path, kind, mode, and content."""
    hasher = hashlib.sha256()
    for path in sorted(plan):
        entry = plan[path]
        record = [path, entry.kind, entry.mode, hashlib.sha256(entry.data).hexdigest()]
        hasher.update(json.dumps(record).encode("utf-8") + b"\n")
    return hasher.hexdigest()


# Publication: all-or-nothing replacement of the generated paths.


def read_manifest(source_root: Path) -> Optional[dict[str, Any]]:
    """Return the validated previous manifest, or ``None`` when absent."""
    path = source_root / MANIFEST_NAME
    if path.is_symlink():
        raise AgentSourceError(f"manifest is a symlink: {path}")
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as error:
        raise AgentSourceError(f"invalid manifest {path}: {error}") from error
    if not isinstance(raw, dict) or raw.get("schema") != MANIFEST_SCHEMA:
        raise AgentSourceError(f"unsupported manifest schema: {path}")
    state = raw.get("state")
    paths = raw.get("paths")
    if state not in ("complete", "publishing"):
        raise AgentSourceError(f"unknown manifest state {state!r}: {path}")
    if (
        not isinstance(paths, list)
        or not all(isinstance(item, str) and is_generated_path(item) for item in paths)
        or len(set(paths)) != len(paths)
    ):
        raise AgentSourceError(f"manifest lists a path it cannot own: {path}")
    expected = str if state == "complete" else type(None)
    if not isinstance(raw.get("digest"), expected):
        raise AgentSourceError(f"invalid manifest digest: {path}")
    return raw


def _write_manifest(source_root: Path, document: dict[str, Any]) -> None:
    path = source_root / MANIFEST_NAME
    temporary = source_root / (MANIFEST_NAME + ".tmp")
    # Unlink a leftover entry, then create without following a symlink.
    if os.path.lexists(str(temporary)):
        temporary.unlink()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(str(temporary), flags, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(document, indent=2, sort_keys=True) + "\n")
    os.replace(str(temporary), str(path))


def _check_components(source_root: Path, path: str) -> None:
    """Fail on a symlink or non-directory component of a generated path."""
    parts = path.split("/")
    current = source_root
    for index, part in enumerate(parts):
        current = current / part
        if current.is_symlink():
            raise AgentSourceError(f"generated path has a symlink: {current}")
        if index < len(parts) - 1 and current.exists() and not current.is_dir():
            raise AgentSourceError(
                f"generated path parent is not a directory: {current}"
            )


def _check_canonical_targets(
    source_root: Path, path: str, is_dir: bool, owned: frozenset[str]
) -> None:
    """Fail when a canonical sibling of ``path`` or an ancestor has its target."""
    parts = path.split("/")
    for index, part in enumerate(parts):
        directory = source_root.joinpath(*parts[:index])
        if not directory.is_dir():
            return
        last = index == len(parts) - 1
        wanted = source_target_name(part, is_dir=is_dir or not last)
        for entry in directory.iterdir():
            relative = "/".join([*parts[:index], entry.name])
            if entry.name == part or entry.name.startswith(".") or relative in owned:
                continue
            if source_target_name(entry.name, is_dir=entry.is_dir()) == wanted:
                raise AgentSourceError(
                    f"canonical source {relative} has the same target as {path}"
                )


def _validate(
    source_root: Path,
    plan: dict[str, Entry],
    new_paths: list[str],
    old_paths: list[str],
) -> None:
    owned = frozenset(new_paths) | frozenset(old_paths)
    for path in old_paths:
        _check_components(source_root, path)
    for path in new_paths:
        _check_components(source_root, path)
        if os.path.lexists(str(source_root / path)) and path not in old_paths:
            raise AgentSourceError(
                f"generated path exists but is not in the manifest: {path}"
            )
        is_dir = plan[path].kind == "dir"
        _check_canonical_targets(source_root, path, is_dir, owned)
        if path.endswith("/" + _IGNORE_NAME):
            directory = source_root / path.rpartition("/")[0]
            for name in _CONTROL_NAMES:
                control = f"{path.rpartition('/')[0]}/{name}"
                if control not in owned and os.path.lexists(str(directory / name)):
                    raise AgentSourceError(
                        f"canonical control file at generated control path: {control}"
                    )


def _remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(str(path))
    elif os.path.lexists(str(path)):
        path.unlink()


def _write_plan(staging: Path, plan: dict[str, Entry]) -> None:
    for path in sorted(plan):
        entry = plan[path]
        target = staging / path
        if entry.kind == "dir":
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(entry.data)
        target.chmod(entry.mode)


def _prepare_locked(source_root: Path) -> bool:
    staging = source_root / STAGING_NAME
    _remove(staging)
    previous = read_manifest(source_root)
    old_paths: list[str] = [] if previous is None else list(previous["paths"])
    plan = plan_projection(source_root, discover(source_root))
    new_paths = top_level_paths(plan)
    _validate(source_root, plan, new_paths, old_paths)
    plan_digest = digest(plan)
    if (
        previous is not None
        and previous["state"] == "complete"
        and previous["digest"] == plan_digest
        and all(os.path.lexists(str(source_root / path)) for path in old_paths)
    ):
        return False
    _write_plan(staging, plan)
    _write_manifest(
        source_root,
        {
            "schema": MANIFEST_SCHEMA,
            "state": "publishing",
            "paths": sorted(set(old_paths) | set(new_paths)),
            "digest": None,
        },
    )
    for path in sorted(set(old_paths) | set(new_paths)):
        _remove(source_root / path)
    for path in new_paths:
        target = source_root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(staging / path), str(target))
    _remove(staging)
    _write_manifest(
        source_root,
        {
            "schema": MANIFEST_SCHEMA,
            "state": "complete",
            "paths": new_paths,
            "digest": plan_digest,
        },
    )
    return True


def prepare(source_root: Path) -> bool:
    """Publish the projection into ``source_root``; return whether it changed.

    An exclusive lock serializes runs. Every validation runs before the first
    mutation, so a failure keeps the previous generated set. A crash during
    publication leaves a ``publishing`` manifest that the next run recovers.
    """
    source_root = Path(source_root)
    if source_root.is_symlink() or not source_root.is_dir():
        raise AgentSourceError(f"source root is not a directory: {source_root}")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(str(source_root / LOCK_NAME), flags, 0o644)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        return _prepare_locked(source_root)
    finally:
        os.close(descriptor)


_COMMANDS = ("prepare", "list-generated")


def _run_command(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="agent_sources.py",
        description="Prepare or list generated agent source entries.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in _COMMANDS:
        command = commands.add_parser(name)
        command.add_argument(
            "--source-root", type=Path, required=True, help="chezmoi source root"
        )
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            prepare(args.source_root)
        else:
            manifest = read_manifest(args.source_root)
            for path in [] if manifest is None else manifest["paths"]:
                print(path)
    except (AgentSourceError, OSError) as error:
        print(f"agent-sources: {error}", file=sys.stderr)
        return 1
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] in _COMMANDS:
        return _run_command(arguments)
    parser = argparse.ArgumentParser(
        description="Print the agent source inventory for a chezmoi source root.",
        epilog="Subcommands: prepare --source-root S, list-generated --source-root S.",
    )
    parser.add_argument("source_root", type=Path, help="chezmoi source root")
    args = parser.parse_args(arguments)
    try:
        document = inventory_document(discover(args.source_root))
    except AgentSourceError as error:
        print(f"agent_sources: {error}", file=sys.stderr)
        return 2
    json.dump(document, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
