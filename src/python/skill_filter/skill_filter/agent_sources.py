"""Discover authored agent sources and describe them as an inventory.

Standard library only and Python 3.8 compatible: chezmoi runs this before
uv or mise exist.
This module reads sources and never writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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
_NATIVE_PREFIXES = ("exact_", "private_", "readonly_", "empty_", "executable_")
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
        return self.authored.parent


def _is_skipped(name: str) -> bool:
    return name in _SKIPPED_NAMES or name.endswith(_SKIPPED_SUFFIXES)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _check_target_name(name: str, path: Path) -> None:
    if not name:
        raise AgentSourceError(f"entry has an empty target name: {path}")
    if name.startswith(".chezmoi"):
        raise AgentSourceError(f"entry targets a reserved chezmoi name: {path}")


def _parse_native_name(name: str, path: Path) -> tuple[str, dict[str, bool]]:
    """Return the target name and attributes of a native chezmoi source name."""
    flags = {"executable": False, "empty": False, "template": False}
    remainder = name
    while True:
        if remainder.startswith(_NATIVE_FORBIDDEN):
            raise AgentSourceError(f"native entry uses a forbidden prefix: {path}")
        if remainder.startswith("dot_"):
            remainder = "." + remainder[len("dot_") :]
            break
        if remainder.startswith("literal_"):
            remainder = remainder[len("literal_") :]
            break
        prefix = next((p for p in _NATIVE_PREFIXES if remainder.startswith(p)), None)
        if prefix is None:
            break
        flags["executable"] |= prefix == "executable_"
        flags["empty"] |= prefix == "empty_"
        remainder = remainder[len(prefix) :]
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
                    name, _ = _parse_native_name(entry.name, entry)
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
                    name, flags = _parse_native_name(entry.name, entry)
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
            name, _ = _parse_native_name(child.name, child)
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
    base = authored.parent
    if value is None:
        default = plugin_dir / "skills"
        _reject_symlink(default)
        return default if _is_real_dir(default) else None
    if not isinstance(value, str) or not _SOURCE_DIR.match(value):
        raise AgentSourceError(f"invalid skills_source_dir in {plugin_dir}: {value!r}")
    current = base
    for part in value.split("/"):
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
    base = authored.parent
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
            "source_dir": f"src/ai/skills/{name}",
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


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print the agent source inventory for a chezmoi source root."
    )
    parser.add_argument("source_root", type=Path, help="chezmoi source root")
    args = parser.parse_args(argv)
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
