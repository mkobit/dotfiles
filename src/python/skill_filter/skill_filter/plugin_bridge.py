"""Reconcile native Claude and Codex plugin registrations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path


class BridgeError(RuntimeError):
    """Raised when a declared bridge resource cannot be reconciled."""


class HostUnavailableError(BridgeError):
    """Raised when a required host command is unavailable."""

    def __init__(self, host: str) -> None:
        super().__init__(f"required host command is unavailable: {host}")
        self.host = host


_NATIVE_HOSTS = frozenset({"claude", "codex"})
_ALL_HOSTS = frozenset({"claude", "codex", "cursor"})
_NAME_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)
_SOURCE_TYPES = frozenset({"generated", "host-provided", "internal", "public"})


def migrate_ownership(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    lines = []
    for resource in payload.get("resources", []):
        kind, host, resource_id = resource["kind"], resource["host"], resource["id"]
        if host not in _NATIVE_HOSTS:
            continue
        if kind == "plugin":
            plugin, separator, marketplace = resource_id.rpartition("@")
            if not separator:
                raise ValueError(f"invalid legacy plugin identity: {resource_id}")
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
    records = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        if len(line.split("\t")) != 4:
            raise BridgeError(f"invalid ownership record: {line!r}")
        records.add(line)
    return records


def _write_ownership(path: Path, records: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        "".join(f"{record}\n" for record in sorted(records)), encoding="utf-8"
    )
    temporary.replace(path)


def _checkpoint(path: Path, record: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as ownership:
        ownership.write(f"{record}\n")


def _run(host: str, *args: str) -> str:
    if host not in _NATIVE_HOSTS:
        raise BridgeError(f"unsupported plugin host: {host}")
    command = shutil.which(host)
    if command is None:
        raise HostUnavailableError(host)
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


def _generated_marketplace_source(host: str, name: str) -> Path | None:
    output = _run(host, "plugin", "marketplace", "list", "--json")
    response = json.loads(output)
    records = response
    if host == "codex":
        records = (
            response.get("marketplaces") if isinstance(response, Mapping) else None
        )
    if not isinstance(records, list):
        raise BridgeError("plugin host returned invalid marketplace JSON")
    for item in records:
        if not isinstance(item, Mapping) or item.get("name") != name:
            continue
        if host == "claude":
            path = item.get("path") if item.get("source") == "directory" else None
        else:
            source = item.get("marketplaceSource")
            path = (
                source.get("source")
                if isinstance(source, Mapping) and source.get("sourceType") == "local"
                else None
            )
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise BridgeError(
                f"plugin host returned no local source for marketplace: {name} ({host})"
            )
        return Path(path)
    return None


def _repair_missing_codex_marketplaces(sources: Mapping[str, str]) -> None:
    if not sources:
        return
    try:
        _generated_marketplace_source("codex", next(iter(sources)))
    except BridgeError as error:
        # A missing manifest blocks the global list, including healthy roots.
        repairs = {}
        suffix = ": marketplace root does not contain a supported manifest"
        for name, locator in sources.items():
            prefix = f"- `{name}` at "
            for line in str(error).splitlines():
                if line.startswith(prefix) and line.endswith(suffix):
                    path = Path(line[len(prefix) : -len(suffix)])
                    if path.is_absolute() and path.resolve() != Path(locator).resolve():
                        repairs[name] = locator
        if not repairs:
            raise
        for name, locator in repairs.items():
            _run("codex", "plugin", "marketplace", "remove", name)
            _run("codex", "plugin", "marketplace", "add", locator)


def _plugin_present(host: str, marketplace: str, plugin: str) -> bool:
    expected = f"{plugin}@{marketplace}"
    args = ["--json"] if host == "claude" else ["-m", marketplace]
    output = _run(host, "plugin", "list", *args)
    if host == "claude":
        return has_identity(output, "id", expected)
    for line in output.splitlines():
        parts = line.split()
        if parts and parts[0] == expected:
            return len(parts) > 1 and parts[1] != "not"
    return False


def _claude_plugin_state(
    marketplace: str, plugin: str
) -> tuple[bool, bool, str | None, Path | None]:
    expected = f"{plugin}@{marketplace}"
    records = json.loads(_run("claude", "plugin", "list", "--json"))
    if isinstance(records, Mapping):
        records = records.get("plugins", [])
    if not isinstance(records, list):
        raise TypeError("plugin host returned invalid JSON")
    for item in records:
        if isinstance(item, Mapping) and item.get("id") == expected:
            version = item.get("version")
            install_path = item.get("installPath")
            return (
                True,
                item.get("enabled") is True,
                version if isinstance(version, str) else None,
                Path(install_path) if isinstance(install_path, str) else None,
            )
    return False, False, None, None


def _package_fingerprint(root: Path) -> str:
    if not root.is_dir():
        raise BridgeError(f"plugin package is missing: {root}; run chezmoi apply again")
    fingerprint = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            entry = (relative, "symlink", Path(os.readlink(path)).as_posix())
        elif path.is_file():
            entry = (
                relative,
                "file",
                path.stat().st_mode & 0o111,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        elif path.is_dir():
            entry = (relative, "directory")
        else:
            raise BridgeError(f"unsupported plugin package entry: {path}")
        fingerprint.update(json.dumps(entry, ensure_ascii=True).encode("utf-8"))
        fingerprint.update(b"\n")
    return fingerprint.hexdigest()


def _ensure_package_plugin(
    host: str, marketplace: str, plugin: str, package_root: Path
) -> None:
    expected = f"{plugin}@{marketplace}"
    fingerprint = _package_fingerprint(package_root)
    if host == "claude":
        present, enabled, _, installed_root = _claude_plugin_state(marketplace, plugin)
        if present and (
            installed_root is None
            or not installed_root.is_dir()
            or _package_fingerprint(installed_root) != fingerprint
        ):
            _run(host, "plugin", "uninstall", expected)
            present = False
        if not present:
            _run(host, "plugin", "install", expected)
        _, enabled, _, installed_root = _claude_plugin_state(marketplace, plugin)
        if not enabled:
            _run(host, "plugin", "enable", expected)
        present, enabled, _, installed_root = _claude_plugin_state(marketplace, plugin)
    elif host == "codex":
        response = json.loads(_run(host, "plugin", "add", expected, "--json"))
        installed_path = (
            response.get("installedPath") if isinstance(response, Mapping) else None
        )
        installed_root = (
            Path(installed_path) if isinstance(installed_path, str) else None
        )
        present, enabled, _, _ = _codex_plugin_state(marketplace, plugin)
    else:
        raise BridgeError(f"unsupported plugin host: {host}")
    if not present or not enabled:
        raise BridgeError(f"plugin did not become available and enabled: {expected}")
    if installed_root is None:
        raise BridgeError(
            f"plugin host returned no installed path for {expected}; update {host} and run chezmoi apply again"
        )
    if _package_fingerprint(installed_root) != fingerprint:
        raise BridgeError(
            f"installed plugin content differs from {package_root}: {expected}; reinstall the plugin and run chezmoi apply again"
        )


def _claude_manifest_version(manifest_root: Path | None, plugin: str) -> str | None:
    if manifest_root is None:
        return None
    try:
        catalog = json.loads(
            (manifest_root / ".claude-plugin/marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        entry = next(
            (
                item
                for item in catalog["plugins"]
                if isinstance(item, Mapping) and item.get("name") == plugin
            ),
            {},
        )
        manifest = json.loads(
            (manifest_root / entry["source"] / ".claude-plugin/plugin.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if not isinstance(manifest, Mapping) or manifest.get("name") != plugin:
        return None
    version = manifest.get("version")
    return version if isinstance(version, str) and version else None


def _codex_plugin_state(
    marketplace: str, plugin: str
) -> tuple[bool, bool, str | None, Path | None]:
    expected = f"{plugin}@{marketplace}"
    response = json.loads(_run("codex", "plugin", "list", "-m", marketplace, "--json"))
    if not isinstance(response, Mapping):
        raise TypeError("plugin host returned invalid JSON")
    records = response.get("installed", [])
    if not isinstance(records, list):
        raise TypeError("plugin host returned invalid JSON")
    for item in records:
        if not isinstance(item, Mapping) or item.get("pluginId") != expected:
            continue
        source = item.get("source")
        source_path = source.get("path") if isinstance(source, Mapping) else None
        return (
            item.get("installed") is True,
            item.get("enabled") is True,
            item.get("version") if isinstance(item.get("version"), str) else None,
            Path(source_path) if isinstance(source_path, str) else None,
        )
    return False, False, None, None


def _codex_manifest_version(source_path: Path | None, plugin: str) -> str:
    if source_path is None:
        raise BridgeError(f"Codex plugin has no source path: {plugin}")
    manifest_path = source_path / ".codex-plugin/plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BridgeError(
            f"cannot read Codex plugin manifest: {manifest_path}"
        ) from error
    if not isinstance(manifest, Mapping) or manifest.get("name") != plugin:
        raise BridgeError(f"invalid Codex plugin manifest: {manifest_path}")
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        raise BridgeError(f"Codex plugin manifest has no version: {manifest_path}")
    return version


def _validate_state_root(destination: Path) -> Path:
    relative = Path(".local/state/dotfiles")
    path = destination / relative
    if path.resolve() != destination.resolve() / relative:
        raise BridgeError(
            f"state root must not contain symlinks or resolve outside destination: {path}"
        )
    return path


def _validate_name(value: object, description: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value in {".", ".."}
        or any(character not in _NAME_CHARS for character in value)
    ):
        raise BridgeError(f"invalid {description} name: {value!r}")
    return value


def _validate_hosts(raw: object, description: str) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)):
        raise BridgeError(f"{description} hosts must be a list")
    if any(not isinstance(host, str) for host in raw):
        raise BridgeError(f"{description} hosts must contain strings: {raw!r}")
    unsupported = tuple(host for host in raw if host not in _ALL_HOSTS)
    if unsupported:
        raise BridgeError(f"unsupported plugin host in {unsupported!r}")
    return tuple(dict.fromkeys(raw))


def _validate_order(
    definition: Mapping[str, object], default: int, description: str
) -> None:
    order = definition.get("order", default)
    if isinstance(order, bool) or not isinstance(order, int) or order < 0:
        raise BridgeError(f"{description} order must be a non-negative integer")


def _validate_marketplaces(marketplaces: Mapping[str, object]) -> None:
    for raw_name, raw_definition in marketplaces.items():
        name = _validate_name(raw_name, "marketplace")
        if not isinstance(raw_definition, Mapping):
            raise BridgeError(f"marketplace {name} must be a table")
        if "source_type" not in raw_definition:
            raise BridgeError(f"marketplace {name} source type is required")
        source_type = raw_definition["source_type"]
        if not isinstance(source_type, str) or source_type not in _SOURCE_TYPES:
            raise BridgeError(f"invalid marketplace source type: {source_type!r}")
        if "source_locator" in raw_definition and not isinstance(
            raw_definition["source_locator"], str
        ):
            raise BridgeError(f"marketplace {name} source locator must be a string")
        locator = raw_definition.get("source_locator", "")
        if source_type in {"internal", "public"} and not locator:
            raise BridgeError(f"marketplace {name} source locator is required")
        if source_type == "host-provided" and locator:
            raise BridgeError(
                f"marketplace {name} host-provided source cannot have a locator"
            )
        _validate_hosts(raw_definition.get("hosts", []), "marketplace")
        _validate_order(raw_definition, 100, f"marketplace {name}")


def _validate_plugins(
    kind: str,
    declarations: Mapping[str, object],
    marketplaces: Mapping[str, object],
) -> None:
    singular_kind = {"plugins": "plugin", "capabilities": "capability"}[kind]
    for raw_name, raw_definition in declarations.items():
        name = _validate_name(raw_name, singular_kind)
        if not isinstance(raw_definition, Mapping):
            raise BridgeError(f"{kind}.{name} must be a table")
        marketplace = raw_definition.get("marketplace")
        marketplace = _validate_name(marketplace, "marketplace")
        if marketplace not in marketplaces:
            raise BridgeError(
                f"undeclared marketplace {marketplace!r} for {kind}.{name}"
            )
        marketplace_definition = marketplaces[marketplace]
        if not isinstance(marketplace_definition, Mapping):
            raise BridgeError(f"marketplace {marketplace} must be a table")
        if "package_path" in raw_definition:
            package_path = raw_definition["package_path"]
            if (
                not isinstance(package_path, str)
                or not package_path
                or Path(package_path).is_absolute()
                or ".." in Path(package_path).parts
                or Path(package_path) == Path(".")
            ):
                raise BridgeError(
                    f"{kind}.{name} package_path must be a relative package directory inside its marketplace"
                )
            if marketplace_definition.get("source_type") != "generated":
                raise BridgeError(
                    f"{kind}.{name} package_path requires a generated marketplace"
                )
        marketplace_hosts = _validate_hosts(
            marketplace_definition.get("hosts", []), "marketplace"
        )
        resource_hosts = set(
            _validate_hosts(
                raw_definition.get("hosts", marketplace_hosts), f"{kind}.{name}"
            )
        )
        marketplace_hosts = set(marketplace_hosts)
        unsupported_hosts = (resource_hosts & _NATIVE_HOSTS) - (
            marketplace_hosts & _NATIVE_HOSTS
        )
        if unsupported_hosts:
            raise BridgeError(
                f"{kind}.{name} hosts must be a subset of marketplace hosts: {sorted(unsupported_hosts)!r}"
            )
        environments = raw_definition.get("environments")
        if environments is not None:
            if not isinstance(environments, (list, tuple)):
                raise BridgeError(f"{kind}.{name} environments must be a list")
            for environment in environments:
                _validate_name(environment, "environment")
        _validate_order(raw_definition, 200, f"{kind}.{name}")


def _validate_bridge_declaration(declaration: object) -> None:
    if not isinstance(declaration, Mapping):
        raise BridgeError("plugin bridge declaration must be a table")
    raw_bridge = declaration.get("plugin_bridge", declaration)
    if not isinstance(raw_bridge, Mapping):
        raise BridgeError("ai.plugin_bridge must be a table")
    environment = raw_bridge.get("environment", "default")
    _validate_name(environment, "environment")
    marketplaces, plugins, capabilities = (
        raw_bridge.get(key, {}) for key in ("marketplaces", "plugins", "capabilities")
    )
    if not all(
        isinstance(value, Mapping) for value in (marketplaces, plugins, capabilities)
    ):
        raise BridgeError("ai.plugin_bridge declarations must be tables")
    _validate_marketplaces(marketplaces)
    _validate_plugins("plugins", plugins, marketplaces)
    _validate_plugins("capabilities", capabilities, marketplaces)


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
    desired.add(record)
    if source_type == "host-provided":
        if not _marketplace_present(host, name):
            raise BridgeError(
                f"host-provided marketplace is unavailable: {name} ({host})"
            )
        return
    if not source_locator:
        raise BridgeError(f"marketplace has no source: {name}")
    if source_type == "generated":
        expected = Path(source_locator).resolve()
        registered = _generated_marketplace_source(host, name)
        if registered is not None and registered.resolve() != expected:
            _run(host, "plugin", "marketplace", "remove", name)
            registered = None
        if registered is None:
            _run(host, "plugin", "marketplace", "add", source_locator)
        registered = _generated_marketplace_source(host, name)
        if registered is None or registered.resolve() != expected:
            raise BridgeError(
                f"marketplace did not register expected source: {name} ({host}); expected {expected}"
            )
    else:
        if _marketplace_present(host, name):
            _run(
                host,
                "plugin",
                "marketplace",
                "update" if host == "claude" else "upgrade",
                name,
            )
        else:
            _run(host, "plugin", "marketplace", "add", source_locator)
        if not _marketplace_present(host, name):
            raise BridgeError(f"marketplace did not become available: {name}")
    owned_desired.add(record)
    _checkpoint(ownership_file, record)


def _ensure_plugin(
    host: str,
    marketplace: str,
    plugin: str,
    ownership_file: Path,
    desired: set[str],
    owned_desired: set[str],
    manifest_root: Path | None = None,
    package_root: Path | None = None,
) -> None:
    record = _identity("plugin", host, marketplace, plugin)
    desired.add(record)
    expected = f"{plugin}@{marketplace}"
    if package_root is not None:
        _ensure_package_plugin(host, marketplace, plugin, package_root)
    elif host == "claude":
        present, enabled, installed_version, _ = _claude_plugin_state(
            marketplace, plugin
        )
        deployed_version = _claude_manifest_version(manifest_root, plugin)
        current = deployed_version is not None and installed_version == deployed_version
        if not (present and enabled and current):
            if not present:
                _run(host, "plugin", "install", expected)
            elif not current:
                _run(host, "plugin", "update", expected)
            _, enabled, _, _ = _claude_plugin_state(marketplace, plugin)
            if not enabled:
                try:
                    _run(host, "plugin", "enable", expected)
                except BridgeError as error:
                    if "already enabled" not in str(error).lower():
                        raise
            present, enabled, _, _ = _claude_plugin_state(marketplace, plugin)
            if not present or not enabled:
                raise BridgeError(
                    f"plugin did not become available and enabled: {expected}"
                )
    elif host == "codex":
        installed, enabled, installed_version, source_path = _codex_plugin_state(
            marketplace, plugin
        )
        manifest_version = (
            _codex_manifest_version(source_path, plugin) if installed else None
        )
        if not installed:
            _run(host, "plugin", "add", expected)
        elif not enabled or installed_version != manifest_version:
            _run(host, "plugin", "remove", expected)
            _run(host, "plugin", "add", expected)
        installed, enabled, installed_version, source_path = _codex_plugin_state(
            marketplace, plugin
        )
        if not installed or not enabled:
            raise BridgeError(
                f"plugin did not become available and enabled: {expected}"
            )
        if installed_version != _codex_manifest_version(source_path, plugin):
            raise BridgeError(f"plugin did not refresh to deployed version: {expected}")
    else:
        raise BridgeError(f"unsupported plugin host: {host}")
    owned_desired.add(record)
    _checkpoint(ownership_file, record)


def _native_hosts(raw: object) -> tuple[str, ...]:
    hosts = _validate_hosts(raw, "plugin")
    return tuple(host for host in hosts if host in _NATIVE_HOSTS)


def _marketplace_rows(
    destination: Path, marketplaces: Mapping[str, object]
) -> list[tuple[int, str, str, str, str]]:
    rows = []
    for name, definition in marketplaces.items():
        if not isinstance(definition, Mapping):
            raise BridgeError(f"marketplace {name} must be a table")
        source_type = str(definition.get("source_type", ""))
        locator = str(definition.get("source_locator", ""))
        if source_type == "generated" and not locator:
            locator = str(destination / ".local/share/agent-plugins/marketplace")
        rows.extend(
            (int(definition.get("order", 100)), name, host, source_type, locator)
            for host in _native_hosts(definition.get("hosts", []))
        )
    return sorted(rows, key=lambda row: (row[0], row[1], row[2]))


def _plugin_rows(
    kind: str,
    declarations: Mapping[str, object],
    marketplaces: Mapping[str, object],
    environment: object,
) -> list[tuple[int, str, str, str]]:
    rows = []
    for name, definition in declarations.items():
        if not isinstance(definition, Mapping):
            raise BridgeError(f"{kind}.{name} must be a table")
        environments = definition.get("environments")
        if environments is not None and environment not in environments:
            continue
        marketplace = definition.get("marketplace", "")
        if not isinstance(marketplace, str):
            raise BridgeError(f"{kind}.{name} marketplace must be a string")
        marketplace_definition = marketplaces.get(marketplace, {})
        if not isinstance(marketplace_definition, Mapping):
            marketplace_definition = {}
        rows.extend(
            (int(definition.get("order", 200)), name, host, marketplace)
            for host in _native_hosts(
                definition.get("hosts", marketplace_definition.get("hosts", []))
            )
        )
    return sorted(rows, key=lambda row: (row[0], row[1], row[2]))


def _remove_stale_record(kind: str, host: str, marketplace: str, plugin: str) -> None:
    try:
        if kind == "plugin":
            if _plugin_present(host, marketplace, plugin):
                _run(
                    host,
                    "plugin",
                    "uninstall" if host == "claude" else "remove",
                    f"{plugin}@{marketplace}",
                )
                if _plugin_present(host, marketplace, plugin):
                    raise BridgeError(
                        f"plugin did not disappear: {plugin}@{marketplace}"
                    )
            return
        if kind != "marketplace":
            return
        if _marketplace_present(host, marketplace):
            _run(host, "plugin", "marketplace", "remove", marketplace)
            if _marketplace_present(host, marketplace):
                raise BridgeError(f"marketplace did not disappear: {marketplace}")
    except HostUnavailableError:
        return


def reconcile(destination: Path, declaration: Mapping[str, object]) -> None:
    _validate_bridge_declaration(declaration)
    raw_bridge = declaration.get("plugin_bridge", declaration)
    if not isinstance(raw_bridge, Mapping):
        raise BridgeError("ai.plugin_bridge must be a table")
    environment = raw_bridge.get("environment", "default")
    marketplaces, plugins, capabilities = (
        raw_bridge.get(key, {}) for key in ("marketplaces", "plugins", "capabilities")
    )
    if not all(
        isinstance(value, Mapping) for value in (marketplaces, plugins, capabilities)
    ):
        raise BridgeError("ai.plugin_bridge declarations must be tables")
    state = _validate_state_root(destination)
    ownership_file = state / "agent-plugin-ownership"
    legacy = state / "agent-plugin-ownership.json"
    if not ownership_file.exists() and legacy.exists():
        migrated = set(migrate_ownership(legacy).splitlines())
        _write_ownership(ownership_file, migrated)
    if ownership_file.exists() and legacy.exists():
        legacy.unlink()
    unavailable_hosts: set[str] = set()
    previous, desired, owned_desired = _read_ownership(ownership_file), set(), set()
    marketplace_rows = _marketplace_rows(destination, marketplaces)
    manifest_roots = {
        (name, host): Path(locator)
        for _, name, host, source_type, locator in marketplace_rows
        if source_type == "generated"
    }
    package_roots = {}
    for kind, declarations in (("capabilities", capabilities), ("plugins", plugins)):
        for _, name, host, marketplace in _plugin_rows(
            kind, declarations, marketplaces, environment
        ):
            definition = declarations[name]
            if not isinstance(definition, Mapping) or "package_path" not in definition:
                continue
            root = manifest_roots[marketplace, host]
            package_root = root / str(definition["package_path"])
            try:
                package_root.resolve().relative_to(root.resolve())
            except ValueError as error:
                raise BridgeError(
                    f"plugin package must resolve inside its marketplace: {package_root}"
                ) from error
            package_roots[kind, name, host] = package_root
    try:
        _repair_missing_codex_marketplaces(
            {
                name: locator
                for _, name, host, source_type, locator in marketplace_rows
                if host == "codex" and source_type == "generated"
            }
        )
    except HostUnavailableError:
        unavailable_hosts.add("codex")
    for _, name, host, source_type, locator in marketplace_rows:
        if host in unavailable_hosts:
            continue
        try:
            _ensure_marketplace(
                host, name, source_type, locator, ownership_file, desired, owned_desired
            )
        except HostUnavailableError:
            unavailable_hosts.add(host)

    for kind, declarations in (("capabilities", capabilities), ("plugins", plugins)):
        rows = _plugin_rows(kind, declarations, marketplaces, environment)
        for _, name, host, marketplace in rows:
            if host in unavailable_hosts:
                continue
            try:
                _ensure_plugin(
                    host,
                    marketplace,
                    name,
                    ownership_file,
                    desired,
                    owned_desired,
                    manifest_root=manifest_roots.get((marketplace, host)),
                    **(
                        {"package_root": package_roots[kind, name, host]}
                        if (kind, name, host) in package_roots
                        else {}
                    ),
                )
            except HostUnavailableError:
                unavailable_hosts.add(host)
    for record in sorted(
        previous - desired, key=lambda value: (value.split("\t")[0] != "plugin", value)
    ):
        kind, host, marketplace, plugin = record.split("\t")
        if host not in _NATIVE_HOSTS:
            previous.discard(record)
            continue
        if host in unavailable_hosts:
            continue
        try:
            _remove_stale_record(kind, host, marketplace, plugin)
        except HostUnavailableError:
            unavailable_hosts.add(host)
            continue
        previous.discard(record)
        _write_ownership(ownership_file, previous | owned_desired)
    retained_unavailable = {
        record for record in previous if record.split("\t")[1] in unavailable_hosts
    }
    _write_ownership(ownership_file, owned_desired | retained_unavailable)


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
