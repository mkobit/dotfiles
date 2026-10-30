"""Validate plugin declarations and plan native host registrations."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path


class BridgeError(RuntimeError):
    """Raised when a declared bridge resource cannot be reconciled."""


_NATIVE_HOSTS = frozenset({"claude", "codex"})
_ALL_HOSTS = frozenset({"claude", "codex", "cursor"})
_NAME_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)
_SOURCE_TYPES = frozenset({"generated", "host-provided", "internal", "public"})


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


def _retired_plugin_rows(
    declarations: Mapping[str, object],
) -> list[tuple[str, str, str]]:
    rows = []
    for raw_name, definition in declarations.items():
        name = _validate_name(raw_name, "retired plugin")
        if not isinstance(definition, Mapping):
            raise BridgeError(f"retired_plugins.{name} must be a table")
        if set(definition) != {"marketplace", "hosts"}:
            raise BridgeError(
                f"retired_plugins.{name} requires only marketplace and hosts"
            )
        marketplace = _validate_name(definition["marketplace"], "marketplace")
        hosts = _validate_hosts(definition["hosts"], f"retired_plugins.{name}")
        if not hosts:
            raise BridgeError(f"retired_plugins.{name} requires hosts")
        rows.extend(
            (name, host, marketplace) for host in hosts if host in _NATIVE_HOSTS
        )
    return sorted(rows)


def _validate_bridge_declaration(declaration: object) -> None:
    if not isinstance(declaration, Mapping):
        raise BridgeError("plugin bridge declaration must be a table")
    raw_bridge = declaration.get("plugin_bridge", declaration)
    if not isinstance(raw_bridge, Mapping):
        raise BridgeError("ai.plugin_bridge must be a table")
    environment = raw_bridge.get("environment", "default")
    _validate_name(environment, "environment")
    marketplaces, plugins, capabilities, retired_plugins = (
        raw_bridge.get(key, {})
        for key in ("marketplaces", "plugins", "capabilities", "retired_plugins")
    )
    if not all(
        isinstance(value, Mapping)
        for value in (marketplaces, plugins, capabilities, retired_plugins)
    ):
        raise BridgeError("ai.plugin_bridge declarations must be tables")
    _validate_marketplaces(marketplaces)
    _validate_plugins("plugins", plugins, marketplaces)
    _validate_plugins("capabilities", capabilities, marketplaces)
    retired = set(_retired_plugin_rows(retired_plugins))
    for kind, declarations in (("plugins", plugins), ("capabilities", capabilities)):
        for _, name, host, marketplace in _plugin_rows(
            kind, declarations, marketplaces, environment
        ):
            if (name, host, marketplace) in retired:
                raise BridgeError(
                    f"plugin is both desired and retired: {name}@{marketplace} ({host})"
                )


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
