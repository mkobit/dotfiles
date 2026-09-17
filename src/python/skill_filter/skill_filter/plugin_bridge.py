"""Reconcile declared agent plugins across Claude, Codex, and Cursor."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import NamedTuple


class BridgeError(RuntimeError):
    """Raised when a declared bridge resource cannot be reconciled."""


class PackageCleanup(NamedTuple):
    """Validated inventory for one generated plugin package."""

    stable_key: str
    root: Path
    expected_files: tuple[str, ...]
    preserved_directories: tuple[str, ...]


# Mirrors the `$tools` destinations in the authored and external skill templates.
_PACKAGE_SKILL_HOSTS = ("claude", "codex", "cursor")


def migrate_ownership(
    path: Path, declared_marketplaces: Mapping[tuple[str, str], str] | None = None
) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    resources = payload.get("resources", [])
    lines = []
    for resource in resources:
        kind = resource["kind"]
        host = resource["host"]
        resource_id = resource["id"]
        if kind == "plugin":
            plugin, separator, marketplace = resource_id.rpartition("@")
            if not separator:
                if host != "cursor":
                    raise ValueError(f"invalid legacy plugin identity: {resource_id}")
                marketplace = (declared_marketplaces or {}).get((host, resource_id), "")
                plugin = resource_id
        elif kind == "marketplace":
            marketplace, plugin = resource_id, ""
        else:
            raise ValueError(f"invalid legacy resource kind: {kind}")
        lines.append(f"{kind}\t{host}\t{marketplace}\t{plugin}")
    return "\n".join(lines) + ("\n" if lines else "")


def has_identity(stream: str, field: str, expected: str) -> bool:
    value = json.loads(stream)
    records = value.get("marketplaces", []) if isinstance(value, Mapping) else value
    if not isinstance(records, list):
        raise TypeError("plugin host returned invalid JSON")
    return any(
        isinstance(item, Mapping) and item.get(field) == expected for item in records
    )


def _identity(kind: str, host: str, marketplace: str, plugin: str) -> str:
    return f"{kind}\t{host}\t{marketplace}\t{plugin}"


def _read_ownership(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ownership = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        if len(line.split("\t")) != 4:
            raise BridgeError(f"invalid ownership record: {line!r}")
        ownership.add(line)
    return ownership


def _write_ownership(path: Path, records: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        "".join(f"{record}\n" for record in sorted(records)), encoding="utf-8"
    )
    os.replace(temporary, path)


def _checkpoint(path: Path, record: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as ownership:
        ownership.write(f"{record}\n")


def _run(host: str, *args: str) -> str:
    if host not in {"claude", "codex"}:
        raise BridgeError(f"unsupported plugin host: {host}")
    command = shutil.which(host)
    if command is None:
        raise BridgeError(f"required host command is unavailable: {host}")
    try:
        result = subprocess.run(
            [command, *args], capture_output=True, text=True, check=False
        )
    except OSError as error:
        if error.errno != 8:
            raise
        result = subprocess.run(
            ["/bin/sh", command, *args], capture_output=True, text=True, check=False
        )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise BridgeError(f"{host} {' '.join(args)} failed: {detail}")
    return result.stdout


def _marketplace_present(host: str, marketplace: str) -> bool:
    args = ["--json"] if host == "claude" else []
    output = _run(host, "plugin", "marketplace", "list", *args)
    if host == "claude":
        return has_identity(output, "name", marketplace)
    return any(
        line.split(maxsplit=1)[0] == marketplace for line in output.splitlines() if line
    )


def _plugin_present(host: str, marketplace: str, plugin: str) -> bool:
    expected = f"{plugin}@{marketplace}"
    args = ["--json"] if host == "claude" else ["-m", marketplace]
    output = _run(host, "plugin", "list", *args)
    if host == "claude":
        return has_identity(output, "id", expected)
    return any(
        line.split(maxsplit=1)[0] == expected for line in output.splitlines() if line
    )


def _claude_plugin_state(marketplace: str, plugin: str) -> tuple[bool, bool]:
    expected = f"{plugin}@{marketplace}"
    records = json.loads(_run("claude", "plugin", "list", "--json"))
    if isinstance(records, Mapping):
        records = records.get("plugins", [])
    if not isinstance(records, list):
        raise TypeError("plugin host returned invalid JSON")
    for item in records:
        if isinstance(item, Mapping) and item.get("id") == expected:
            return True, item.get("enabled") is True
    return False, False


def _validate_name(name: str) -> None:
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    if not name or name in {".", ".."} or any(c not in allowed for c in name):
        raise BridgeError(f"invalid cursor plugin name: {name}")


def _validate_bridge_path(
    destination: Path, relative_path: str, description: str
) -> Path:
    path = destination / relative_path
    expected = destination.resolve() / relative_path
    if path.resolve() != expected:
        raise BridgeError(
            f"{description} must not contain symlinks or resolve outside destination: {path}"
        )
    return path


def _has_desired_cursor_plugin(desired: set[str], plugin: str) -> bool:
    for record in desired:
        kind, host, _, desired_plugin = record.split("\t")
        if kind == "plugin" and host == "cursor" and desired_plugin == plugin:
            return True
    return False


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def _ensure_marketplace(
    host: str,
    name: str,
    source_type: str,
    source_locator: str,
    ownership_file: Path,
    desired: set[str],
    owned_desired: set[str],
) -> None:
    record = _identity("marketplace", host, name, "")
    if host == "cursor":
        return
    desired.add(record)
    if source_type == "host-provided":
        if not _marketplace_present(host, name):
            raise BridgeError(
                f"host-provided marketplace is unavailable: {name} ({host})"
            )
        return
    if not source_locator:
        raise BridgeError(f"marketplace has no source: {name}")
    present = _marketplace_present(host, name)
    if present and source_type != "generated":
        operation = "update" if host == "claude" else "upgrade"
        _run(host, "plugin", "marketplace", operation, name)
    elif not present:
        _run(host, "plugin", "marketplace", "add", source_locator)
    if not _marketplace_present(host, name):
        raise BridgeError(f"marketplace did not become available: {name}")
    owned_desired.add(record)
    _checkpoint(ownership_file, record)


def _ensure_plugin(
    host: str,
    marketplace: str,
    plugin: str,
    destination: Path,
    ownership_file: Path,
    desired: set[str],
    owned_desired: set[str],
) -> None:
    record = _identity("plugin", host, marketplace, plugin)
    desired.add(record)
    expected = f"{plugin}@{marketplace}"
    if host == "cursor":
        _validate_name(plugin)
        target = (
            destination
            / ".local/share/agent-plugins/marketplace/plugins"
            / plugin
            / "cursor"
        )
        cursor_root = _validate_bridge_path(
            destination, ".cursor/plugins/local", "cursor plugin root"
        )
        installed = cursor_root / plugin
        if not target.is_dir():
            raise BridgeError(f"cursor plugin package is unavailable: {target}")
        _remove(installed)
        installed.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(target, installed)
    elif host == "claude":
        present, enabled = _claude_plugin_state(marketplace, plugin)
        if present:
            _run(host, "plugin", "update", expected)
            _, enabled = _claude_plugin_state(marketplace, plugin)
            if not enabled:
                _run(host, "plugin", "enable", expected)
        else:
            _run(host, "plugin", "install", expected)
            _run(host, "plugin", "enable", expected)
        present, enabled = _claude_plugin_state(marketplace, plugin)
        if not present or not enabled:
            raise BridgeError(
                f"plugin did not become available and enabled: {expected}"
            )
    elif _plugin_present(host, marketplace, plugin):
        _run(host, "plugin", "add", expected)
    else:
        _run(host, "plugin", "add", expected)
    if host == "codex" and not _plugin_present(host, marketplace, plugin):
        raise BridgeError(f"plugin did not become available: {expected}")
    owned_desired.add(record)
    _checkpoint(ownership_file, record)


def _parse_package_cleanup(
    raw: object, generated_marketplace_root: Path
) -> PackageCleanup:
    if not isinstance(raw, Mapping):
        raise BridgeError("package cleanup must be a table")
    stable_key = raw.get("stable_key")
    root = raw.get("root")
    expected_files = raw.get("expected_files")
    preserved_directories = raw.get("preserved_directories", ())
    if not isinstance(stable_key, str) or not stable_key:
        raise BridgeError("package cleanup stable_key must be a non-empty string")
    if (
        stable_key in {".", ".."}
        or "/" in stable_key
        or "\\" in stable_key
        or "\0" in stable_key
    ):
        raise BridgeError("package cleanup stable_key must be a simple path name")
    if not isinstance(root, str) or not root:
        raise BridgeError("package cleanup root must be a non-empty string")
    if not os.path.isabs(root) or "\0" in root:
        raise BridgeError("package cleanup root must be absolute")
    if not isinstance(expected_files, (list, tuple)) or not all(
        isinstance(entry, str) for entry in expected_files
    ):
        raise BridgeError("package cleanup expected_files must be a list of strings")
    if not isinstance(preserved_directories, (list, tuple)) or not all(
        isinstance(entry, str) for entry in preserved_directories
    ):
        raise BridgeError(
            "package cleanup preserved_directories must be a list of strings"
        )

    entries = tuple(expected_files)
    preserved = tuple(preserved_directories)
    for entry in (*entries, *preserved):
        parts = entry.split("/")
        if (
            not entry
            or "\0" in entry
            or "\\" in entry
            or os.path.isabs(entry)
            or any(part in {"", ".", ".."} for part in parts)
        ):
            raise BridgeError(f"package cleanup expected file is unsafe: {entry!r}")
    if len(entries) != len(set(entries)):
        raise BridgeError("package cleanup expected_files contain a duplicate entry")
    if len(preserved) != len(set(preserved)):
        raise BridgeError(
            "package cleanup preserved_directories contain a duplicate entry"
        )

    sorted_entries = sorted(entries)
    for parent, child in zip(sorted_entries, sorted_entries[1:]):
        if child.startswith(f"{parent}/"):
            raise BridgeError(
                "package cleanup expected_files contain a file/directory conflict"
            )
    for preserved_root in preserved:
        if preserved_root in entries or any(
            preserved_root.startswith(f"{entry}/")
            or entry.startswith(f"{preserved_root}/")
            for entry in entries
        ):
            raise BridgeError(
                "package cleanup file and preserved directory inventories conflict"
            )

    expected_root = generated_marketplace_root / "plugins" / stable_key
    if root != str(expected_root) or root != os.path.normpath(root):
        raise BridgeError("package cleanup root is outside generated marketplace root")
    return PackageCleanup(stable_key, expected_root, entries, preserved)


def _cleanup_generated_package(
    generated_marketplace_root: Path, cleanup: PackageCleanup
) -> None:
    """Prune stale files from one validated generated plugin package."""
    package_root = cleanup.root
    expected_root = generated_marketplace_root / "plugins" / cleanup.stable_key
    if package_root != expected_root:
        raise BridgeError("package cleanup root is outside generated marketplace root")

    for ancestor in (package_root, *package_root.parents):
        if ancestor.is_symlink():
            raise BridgeError("package cleanup path contains a symlink")
    if not package_root.exists():
        return
    if not package_root.is_dir():
        raise BridgeError("package cleanup root is not a directory")

    expected_files = set(cleanup.expected_files)
    preserved_directories = set(cleanup.preserved_directories)

    def prune(directory: Path) -> None:
        for entry in os.scandir(directory):
            path = Path(entry.path)
            relative = path.relative_to(package_root).as_posix()
            if relative in preserved_directories:
                if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
                    raise BridgeError(
                        "package cleanup preserved path is not a directory: "
                        f"{relative!r}"
                    )
                continue
            if entry.is_symlink():
                if relative in expected_files:
                    raise BridgeError(
                        f"package cleanup expected file is a symlink: {relative!r}"
                    )
                path.unlink()
                continue
            if entry.is_dir(follow_symlinks=False):
                if relative in expected_files:
                    raise BridgeError(
                        f"package cleanup expected file is a directory: {relative!r}"
                    )
                prune(path)
                try:
                    path.rmdir()
                except OSError:
                    pass
                continue
            if not entry.is_file(follow_symlinks=False):
                raise BridgeError(
                    f"package cleanup encountered special file: {relative!r}"
                )
            if relative not in expected_files:
                path.unlink()

    prune(package_root)


def _source_files(root: Path, *, transform_target_names: bool = False) -> list[str]:
    if not root.is_dir():
        return []
    files = []
    for path in sorted(root.rglob("*")):
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(mode):
            continue
        relative = path.relative_to(root).as_posix()
        if transform_target_names:
            components = relative.split("/")
            if components[-1].endswith(".tmpl"):
                components[-1] = components[-1][:-5]
            relative = "/".join(
                f".{component[4:]}" if component.startswith("dot_") else component
                for component in components
            )
        files.append(relative)
    return files


def _package_cleanup_inventory(
    name: str,
    definition: Mapping[str, object],
    marketplaces: Mapping[str, object],
    skills: Mapping[str, object],
    source_dir: Path | None,
    working_tree: Path | None,
    generated_marketplace_root: Path,
    overlay_skills: Mapping[str, object] | None = None,
) -> dict[str, object] | None:
    if source_dir is None or working_tree is None:
        return None
    marketplace = str(definition.get("marketplace", ""))
    marketplace_definition = marketplaces.get(marketplace, {})
    if not isinstance(marketplace_definition, Mapping):
        marketplace_definition = {}
    hosts = definition.get("hosts", marketplace_definition.get("hosts", []))
    if not isinstance(hosts, (list, tuple)):
        hosts = []
    authored_source = definition.get("authored_skill_source", "")
    plugin_source = definition.get("source_dir", "")
    overlay_source = definition.get("overlay_skill_source", "")
    if not (
        (isinstance(authored_source, str) and authored_source)
        or (isinstance(plugin_source, str) and plugin_source)
        or (
            isinstance(overlay_source, str)
            and overlay_source
            and isinstance(overlay_skills, Mapping)
        )
    ):
        return None
    package_source_root = (
        source_dir / "dot_local/share/agent-plugins/marketplace/plugins" / name
    )
    if not package_source_root.is_dir():
        return None
    expected_files = _source_files(package_source_root, transform_target_names=True)
    preserved_directories = []
    if isinstance(authored_source, str) and authored_source:
        authored_root = working_tree / authored_source
        authored = skills.get("authored", {})
        if isinstance(authored, Mapping):
            for skill_name, state in authored.items():
                if not isinstance(skill_name, str) or not isinstance(state, str):
                    continue
                if state != "present" and state not in {"claude", "codex", "cursor"}:
                    continue
                package_roots = ["skills"] if state == "present" else []
                if state == "present":
                    package_roots.extend(
                        f"{host}/skills" for host in _PACKAGE_SKILL_HOSTS
                    )
                else:
                    package_roots.append(f"{state}/skills")
                skill_files = _source_files(authored_root / skill_name)
                expected_files.extend(
                    f"{package_root}/{skill_name}/{relative}"
                    for package_root in package_roots
                    for relative in skill_files
                )
        external = skills.get("external", {})
        if isinstance(external, Mapping):
            for source in external.values():
                if not isinstance(source, Mapping):
                    continue
                source_skills = source.get("skills", {})
                if not isinstance(source_skills, Mapping):
                    continue
                for skill_name, state in source_skills.items():
                    if not isinstance(skill_name, str) or not isinstance(state, str):
                        continue
                    if state == "present":
                        preserved_directories.append(f"skills/{skill_name}")
                        preserved_directories.extend(
                            f"{host}/skills/{skill_name}"
                            for host in _PACKAGE_SKILL_HOSTS
                        )
                    elif state in _PACKAGE_SKILL_HOSTS:
                        preserved_directories.append(f"{state}/skills/{skill_name}")
    if not (
        isinstance(overlay_source, str)
        and overlay_source
        and isinstance(overlay_skills, Mapping)
    ):
        overlay_source = ""
    if (
        not overlay_source
        and isinstance(plugin_source, str)
        and plugin_source
        and isinstance(overlay_skills, Mapping)
    ):
        overlay_source = plugin_source
    if overlay_source:
        authored = (overlay_skills or {}).get("authored", {})
        if isinstance(authored, Mapping):
            for skill_name, state in authored.items():
                if not isinstance(skill_name, str) or not isinstance(state, str):
                    continue
                if state == "present" or (
                    state == "local" and Path("/Applications/Santa.app").exists()
                ):
                    package_roots = [
                        "skills",
                        *(f"{host}/skills" for host in _PACKAGE_SKILL_HOSTS),
                    ]
                elif state in _PACKAGE_SKILL_HOSTS:
                    package_roots = [f"{state}/skills"]
                else:
                    continue
                skill_files = _source_files(working_tree / overlay_source / skill_name)
                expected_files.extend(
                    f"{package_root}/{skill_name}/{relative}"
                    for package_root in package_roots
                    for relative in skill_files
                )
    if isinstance(plugin_source, str) and plugin_source:
        plugin_skills = definition.get("skills", {})
        if isinstance(plugin_skills, Mapping):
            for skill_name, state in plugin_skills.items():
                if not isinstance(skill_name, str) or not isinstance(state, str):
                    continue
                if state != "present" and state not in hosts:
                    continue
                package_roots = ["skills"] if state == "present" else []
                if state == "present":
                    package_roots.extend(f"{host}/skills" for host in hosts)
                else:
                    package_roots.append(f"{state}/skills")
                skill_files = _source_files(
                    working_tree / plugin_source / "skills" / skill_name
                )
                expected_files.extend(
                    f"{package_root}/{skill_name}/{relative}"
                    for package_root in package_roots
                    for relative in skill_files
                )
    return {
        "stable_key": name,
        "root": str(generated_marketplace_root / "plugins" / name),
        "expected_files": sorted(set(expected_files)),
        "preserved_directories": sorted(set(preserved_directories)),
    }


def _collect_package_cleanups(
    bridge: Mapping[str, object],
    marketplaces: Mapping[str, object],
    plugins: Mapping[str, object],
    capabilities: Mapping[str, object],
    destination: Path,
    skills: Mapping[str, object] | None = None,
    source_dir: Path | None = None,
    working_tree: Path | None = None,
    generated_marketplace_root: Path | None = None,
    overlay_skills: Mapping[str, object] | None = None,
) -> tuple[Path, tuple[PackageCleanup, ...]]:
    raw_root = bridge.get("generated_marketplace_root")
    if raw_root is None and generated_marketplace_root is not None:
        raw_root = str(generated_marketplace_root)
    if raw_root is None:
        raw_root = str(destination / ".local/share/agent-plugins/marketplace")
    if not isinstance(raw_root, str) or not raw_root:
        raise BridgeError("generated marketplace root must be a non-empty string")
    generated_root = Path(raw_root)
    if not generated_root.is_absolute() or raw_root != os.path.normpath(raw_root):
        raise BridgeError("generated marketplace root is not canonical")
    try:
        generated_root.relative_to(destination.resolve())
    except ValueError as error:
        raise BridgeError(
            "generated marketplace root is outside destination"
        ) from error
    for ancestor in (generated_root, *generated_root.parents):
        if ancestor.is_symlink():
            raise BridgeError("generated marketplace root contains a symlink")

    raw_cleanups: list[object] = []
    for declarations in (plugins, marketplaces):
        for name, definition in declarations.items():
            if not isinstance(definition, Mapping):
                continue
            cleanup = definition.get("package_cleanup")
            if cleanup is not None:
                raw_cleanups.append(cleanup)
    for name, definition in capabilities.items():
        if not isinstance(definition, Mapping):
            continue
        cleanup = definition.get("package_cleanup")
        if cleanup is not None:
            raw_cleanups.append(cleanup)
        generated_cleanup = _package_cleanup_inventory(
            str(name),
            definition,
            marketplaces,
            skills or {},
            source_dir,
            working_tree,
            generated_root,
            overlay_skills=overlay_skills,
        )
        if generated_cleanup is not None:
            raw_cleanups.append(generated_cleanup)
    bridge_cleanups = bridge.get("package_cleanups", ())
    if isinstance(bridge_cleanups, Mapping):
        raw_cleanups.append(bridge_cleanups)
    elif isinstance(bridge_cleanups, (list, tuple)):
        raw_cleanups.extend(bridge_cleanups)
    elif bridge_cleanups:
        raise BridgeError("package_cleanups must be a list of tables")

    cleanups = []
    seen: dict[str, PackageCleanup] = {}
    for raw in raw_cleanups:
        cleanup = _parse_package_cleanup(raw, generated_root)
        prior = seen.get(cleanup.stable_key)
        if prior is not None and prior != cleanup:
            raise BridgeError(
                f"conflicting package cleanup inventory: {cleanup.stable_key}"
            )
        if prior is None:
            seen[cleanup.stable_key] = cleanup
            cleanups.append(cleanup)
    return generated_root, tuple(cleanups)


def reconcile(destination: Path, declaration: Mapping[str, object]) -> None:
    raw_bridge = declaration.get("plugin_bridge", declaration)
    if not isinstance(raw_bridge, Mapping):
        raise BridgeError("ai.plugin_bridge must be a table")
    bridge = dict(raw_bridge)
    if "generated_marketplace_root" not in bridge:
        metadata_root = declaration.get("generated_marketplace_root")
        if metadata_root is not None:
            bridge["generated_marketplace_root"] = metadata_root
    environment = bridge.get("environment", "default")
    marketplaces = bridge.get("marketplaces", {})
    plugins = bridge.get("plugins", {})
    capabilities = bridge.get("capabilities", {})
    if not all(
        isinstance(value, Mapping) for value in (marketplaces, plugins, capabilities)
    ):
        raise BridgeError("ai.plugin_bridge declarations must be tables")
    skills = declaration.get("skills", {})
    if not isinstance(skills, Mapping):
        skills = {}
    overlay_skills = declaration.get("overlay_skills", {})
    if not isinstance(overlay_skills, Mapping):
        overlay_skills = {}
    source_dir = declaration.get("source_dir")
    working_tree = declaration.get("working_tree")
    source_path = Path(source_dir) if isinstance(source_dir, str) else None
    working_path = Path(working_tree) if isinstance(working_tree, str) else None
    generated_root_metadata = declaration.get("generated_marketplace_root")
    generated_path = (
        Path(generated_root_metadata)
        if isinstance(generated_root_metadata, str)
        else None
    )
    generated_marketplace_root, package_cleanups = _collect_package_cleanups(
        bridge,
        marketplaces,
        plugins,
        capabilities,
        destination,
        skills,
        source_path,
        working_path,
        generated_path,
        overlay_skills,
    )

    declared_marketplaces = {}
    for declarations in (capabilities, plugins):
        for name, definition in declarations.items():
            if not isinstance(definition, Mapping):
                continue
            marketplace = str(definition.get("marketplace", ""))
            if marketplace:
                declared_marketplaces[("cursor", name)] = marketplace

    state = _validate_bridge_path(destination, ".local/state/dotfiles", "state root")
    ownership_file = state / "agent-plugin-ownership"
    legacy = state / "agent-plugin-ownership.json"
    if not ownership_file.exists() and legacy.exists():
        ownership_file.write_text(
            migrate_ownership(legacy, declared_marketplaces), encoding="utf-8"
        )
    previous = _read_ownership(ownership_file)
    desired: set[str] = set()
    owned_desired: set[str] = set()

    for cleanup in package_cleanups:
        _cleanup_generated_package(generated_marketplace_root, cleanup)

    marketplace_rows = []
    for name, definition in marketplaces.items():
        if not isinstance(definition, Mapping):
            raise BridgeError(f"marketplace {name} must be a table")
        source_type = str(definition.get("source_type", ""))
        locator = str(definition.get("source_locator", ""))
        if source_type == "generated" and not locator:
            locator = str(destination / ".local/share/agent-plugins/marketplace")
        for host in dict.fromkeys(definition.get("hosts", [])):
            marketplace_rows.append(
                (int(definition.get("order", 100)), name, host, source_type, locator)
            )
    for _, name, host, source_type, locator in sorted(
        marketplace_rows, key=lambda row: (row[0], row[1], row[2])
    ):
        _ensure_marketplace(
            host, name, source_type, locator, ownership_file, desired, owned_desired
        )

    def collect_plugin_rows(kind, declarations):
        rows = []
        for name, definition in declarations.items():
            if not isinstance(definition, Mapping):
                raise BridgeError(f"{kind}.{name} must be a table")
            environments = definition.get("environments")
            if (
                kind == "plugins"
                and environments is not None
                and environment not in environments
            ):
                continue
            marketplace = definition.get("marketplace", "")
            marketplace_definition = marketplaces.get(marketplace, {})
            hosts = definition.get("hosts", marketplace_definition.get("hosts", []))
            for host in dict.fromkeys(hosts):
                rows.append(
                    (int(definition.get("order", 200)), name, host, marketplace)
                )
        return sorted(rows, key=lambda row: (row[0], row[1], row[2]))

    for rows in (
        collect_plugin_rows("capabilities", capabilities),
        collect_plugin_rows("plugins", plugins),
    ):
        for _, name, host, marketplace in rows:
            _ensure_plugin(
                host,
                marketplace,
                name,
                destination,
                ownership_file,
                desired,
                owned_desired,
            )

    for record in sorted(
        previous - desired,
        key=lambda value: (value.split("\t")[0] != "plugin", value),
    ):
        kind, host, marketplace, plugin = record.split("\t")
        if kind == "plugin":
            if host == "cursor":
                _validate_name(plugin)
                if _has_desired_cursor_plugin(desired, plugin):
                    continue
                cursor_root = _validate_bridge_path(
                    destination, ".cursor/plugins/local", "cursor plugin root"
                )
                _remove(cursor_root / plugin)
            else:
                operation = "uninstall" if host == "claude" else "remove"
                _run(host, "plugin", operation, f"{plugin}@{marketplace}")
        elif kind == "marketplace":
            _run(host, "plugin", "marketplace", "remove", marketplace)
    _write_ownership(ownership_file, owned_desired)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    migrate = commands.add_parser("migrate-ownership")
    migrate.add_argument("path", type=Path)
    identity = commands.add_parser("has-identity")
    identity.add_argument("--field", required=True)
    identity.add_argument("--expected", required=True)
    reconcile_parser = commands.add_parser("reconcile")
    reconcile_parser.add_argument("--destination", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "migrate-ownership":
            sys.stdout.write(migrate_ownership(args.path))
        elif args.command == "has-identity":
            return 0 if has_identity(sys.stdin.read(), args.field, args.expected) else 1
        else:
            reconcile(args.destination, json.load(sys.stdin))
        return 0
    except (
        BridgeError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        OSError,
    ) as error:
        print(f"plugin-bridge: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
