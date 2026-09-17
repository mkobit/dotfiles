"""Reconcile declared agent plugins across Claude, Codex, and Cursor."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path


class BridgeError(RuntimeError):
    """Raised when a declared bridge resource cannot be reconciled."""


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
        installed = destination / ".cursor/plugins/local" / plugin
        if not target.is_dir():
            raise BridgeError(f"cursor plugin package is unavailable: {target}")
        _remove(installed)
        installed.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(target, installed)
    elif host == "claude":
        present, enabled = _claude_plugin_state(marketplace, plugin)
        if present:
            _run(host, "plugin", "update", expected)
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


def reconcile(destination: Path, declaration: Mapping[str, object]) -> None:
    bridge = declaration.get("plugin_bridge", declaration)
    if not isinstance(bridge, Mapping):
        raise BridgeError("ai.plugin_bridge must be a table")
    environment = bridge.get("environment", "default")
    marketplaces = bridge.get("marketplaces", {})
    plugins = bridge.get("plugins", {})
    capabilities = bridge.get("capabilities", {})
    if not all(
        isinstance(value, Mapping) for value in (marketplaces, plugins, capabilities)
    ):
        raise BridgeError("ai.plugin_bridge declarations must be tables")

    declared_marketplaces = {}
    for declarations in (capabilities, plugins):
        for name, definition in declarations.items():
            if not isinstance(definition, Mapping):
                continue
            marketplace = str(definition.get("marketplace", ""))
            if marketplace:
                declared_marketplaces[("cursor", name)] = marketplace

    state = destination / ".local/state/dotfiles"
    ownership_file = state / "agent-plugin-ownership"
    legacy = state / "agent-plugin-ownership.json"
    if not ownership_file.exists() and legacy.exists():
        ownership_file.write_text(
            migrate_ownership(legacy, declared_marketplaces), encoding="utf-8"
        )
    previous = _read_ownership(ownership_file)
    desired: set[str] = set()
    owned_desired: set[str] = set()

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
                _remove(destination / ".cursor/plugins/local" / plugin)
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
