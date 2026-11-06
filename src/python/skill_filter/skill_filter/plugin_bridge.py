"""Reconcile native Claude and Codex plugin registrations.

Ownership state lives in ``<dest>/.local/state/dotfiles/agent-plugin-ownership``.
Each line is ``kind<TAB>host<TAB>marketplace<TAB>plugin<TAB>provenance``.
``kind`` is ``plugin`` or ``marketplace``; a marketplace line has an empty plugin.
``provenance`` is ``owned`` or ``ambiguous``.
Only ``owned`` records drive removal.
The bridge records ``owned`` only for what it installed (or registered), or for what
a previous ``owned`` record already covers.
It never adopts a manual or earlier install, including from a ``host-provided`` marketplace.
It never registers, updates, or records a ``host-provided`` marketplace itself.
Four-field lines (the earlier format) and the legacy JSON state are classified by
``_classify_legacy`` and rewritten before any host mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING or bool(__package__):
    from skill_filter.plugin_declarations import (
        _CLI_HOSTS,
        _NATIVE_HOSTS,
        BridgeError,
        _marketplace_rows,
        _plugin_rows,
        _retired_plugin_rows,
        _validate_bridge_declaration,
    )
else:
    from plugin_declarations import (
        _CLI_HOSTS,
        _NATIVE_HOSTS,
        BridgeError,
        _marketplace_rows,
        _plugin_rows,
        _retired_plugin_rows,
        _validate_bridge_declaration,
    )


logger = logging.getLogger(__name__)


class HostUnavailableError(BridgeError):
    """Raised when a required host command is unavailable."""

    def __init__(self, host: str) -> None:
        super().__init__(f"required host command is unavailable: {host}")
        self.host = host


class MarketplaceUnavailableError(BridgeError):
    """Raised when a host-provided marketplace is not registered on a host."""

    def __init__(self, host: str, name: str) -> None:
        super().__init__(f"host-provided marketplace is unavailable: {name} ({host})")
        self.host = host
        self.name = name


_PROVENANCES = frozenset({"owned", "ambiguous"})


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


def _owned_record(kind: str, host: str, marketplace: str, plugin: str) -> str:
    return f"{_identity(kind, host, marketplace, plugin)}\towned"


def _record_identity(record: str) -> str:
    return "\t".join(record.split("\t")[:4])


def _is_owned(record: str) -> bool:
    return record.endswith("\towned")


def _classify_legacy(record: str, marketplaces: Mapping[str, object]) -> str | None:
    """Return the provenance for a four-field record, or None to drop it."""
    marketplace = record.split("\t")[2]
    definition = marketplaces.get(marketplace)
    source_type = (
        definition.get("source_type") if isinstance(definition, Mapping) else None
    )
    if source_type == "generated":
        return "owned"
    if source_type == "host-provided":
        return None
    return "ambiguous"


def _read_ownership(path: Path) -> set[str]:
    """Read validated records; four-field lines are returned unclassified."""
    if not path.exists():
        return set()
    records = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        fields = line.split("\t")
        if len(fields) not in {4, 5} or (
            len(fields) == 5 and fields[4] not in _PROVENANCES
        ):
            raise BridgeError(f"invalid ownership record: {line!r}")
        records.add(line)
    return records


def _normalize_ownership(
    records: set[str], marketplaces: Mapping[str, object]
) -> set[str]:
    """Return five-field native-host records; ``owned`` wins over ``ambiguous``."""
    provenance: dict[str, str] = {}
    for record in records:
        identity = _record_identity(record)
        if identity.split("\t")[1] not in _NATIVE_HOSTS:
            continue
        kind = (
            record.split("\t")[4]
            if record.count("\t") == 4
            else _classify_legacy(record, marketplaces)
        )
        if kind is not None and provenance.get(identity) != "owned":
            provenance[identity] = kind
    return {f"{identity}\t{kind}" for identity, kind in provenance.items()}


def _merge_ownership(previous: set[str], owned_desired: set[str]) -> set[str]:
    """Union records, dropping a previous record superseded by a new owned one."""
    superseded = {_record_identity(record) for record in owned_desired}
    return owned_desired | {
        record for record in previous if _record_identity(record) not in superseded
    }


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
    operation = "-".join(
        args[:3] if args[:2] == ("plugin", "marketplace") else args[:2]
    )
    if operation not in {
        "plugin-marketplace-list",
        "plugin-marketplace-add",
        "plugin-marketplace-remove",
        "plugin-marketplace-update",
        "plugin-marketplace-upgrade",
        "plugin-list",
        "plugin-install",
        "plugin-uninstall",
        "plugin-add",
        "plugin-remove",
        "plugin-update",
        "plugin-enable",
        "plugin-disable",
    }:
        operation = "host-command"
    started = time.monotonic()
    status = "error"
    logger.info("host=%s operation=%s event=start", host, operation)
    try:
        command = shutil.which(host)
        if command is None:
            status = "unavailable"
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
        status = str(result.returncode)
        if result.returncode:
            detail = result.stderr.strip() or result.stdout.strip()
            raise BridgeError(f"{host} {' '.join(args)} failed: {detail}")
        return result.stdout
    finally:
        elapsed = time.monotonic() - started
        logger.info(
            "host=%s operation=%s event=end elapsed_seconds=%.3f status=%s",
            host,
            operation,
            elapsed,
            status,
        )


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


def _package_manifest_version(package_root: Path, host: str) -> str | None:
    """Return the version in the package's host manifest, or None when it has none."""
    try:
        manifest = json.loads(
            (package_root / f".{host}-plugin/plugin.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return None
    version = manifest.get("version") if isinstance(manifest, Mapping) else None
    return version if isinstance(version, str) and version else None


def _refresh_plugin(host: str, marketplace: str, plugin: str) -> None:
    """Update an owned plugin of a refreshed marketplace; Codex reinstalls on a new version."""
    expected = f"{plugin}@{marketplace}"
    if host == "claude":
        _run(host, "plugin", "update", expected)
        return
    # Codex has no update command. If `add` fails after `remove`, the plugin stays
    # uninstalled until the next refresh, and no ownership record is written for it.
    installed, _, installed_version, source_path = _codex_plugin_state(
        marketplace, plugin
    )
    if not installed or source_path is None:
        return
    try:
        available = _codex_manifest_version(source_path, plugin)
    except BridgeError:
        logger.info(
            "host=%s plugin=%s event=refresh-skipped reason=no-version", host, expected
        )
        return
    if available != installed_version:
        _run(host, "plugin", "remove", expected)
        _run(host, "plugin", "add", expected)


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
        installed, enabled, installed_version, _ = _codex_plugin_state(
            marketplace, plugin
        )
        deployed_version = _package_manifest_version(package_root, "codex")
        if (
            installed
            and enabled
            and deployed_version is not None
            and installed_version == deployed_version
        ):
            return  # the version is content-derived, so equal versions mean equal content
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


def _ensure_marketplace(
    host: str,
    name: str,
    source_type: str,
    source_locator: str,
    ownership_file: Path,
    desired: set[str],
    owned_desired: set[str],
    previous_owned: frozenset[str] = frozenset(),
    refresh: bool = False,
) -> bool:
    """Register the marketplace; return True when ``refresh`` updated an owned one."""
    identity = _identity("marketplace", host, name, "")
    desired.add(identity)
    if source_type == "host-provided":
        # Corporate wrappers own it: check presence only, never record.
        if not _marketplace_present(host, name):
            raise MarketplaceUnavailableError(host, name)
        return False
    if not source_locator:
        raise BridgeError(f"marketplace has no source: {name}")
    record = f"{identity}\towned"
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
        adopted = _marketplace_present(host, name)
        if adopted and identity not in previous_owned:
            return False  # adopted manual registration: never updated or recorded
        if not adopted:
            _run(host, "plugin", "marketplace", "add", source_locator)
        elif refresh:
            _run(
                host,
                "plugin",
                "marketplace",
                "update" if host == "claude" else "upgrade",
                name,
            )
        if not _marketplace_present(host, name):
            raise BridgeError(f"marketplace did not become available: {name}")
        owned_desired.add(record)
        _checkpoint(ownership_file, record)
        return refresh and adopted
    owned_desired.add(record)
    _checkpoint(ownership_file, record)
    return False


def _plugin_status(host: str, marketplace: str, plugin: str) -> tuple[bool, bool]:
    if host == "claude":
        present, enabled, _, _ = _claude_plugin_state(marketplace, plugin)
    elif host == "codex":
        present, enabled, _, _ = _codex_plugin_state(marketplace, plugin)
    else:
        raise BridgeError(f"unsupported plugin host: {host}")
    return present, enabled


def _ensure_installed_and_enabled(
    host: str, marketplace: str, plugin: str, *, reenable_codex: bool = True
) -> bool:
    """Install when absent and enable when disabled; never update or remove.

    Returns True when this call installed the plugin.
    With ``reenable_codex`` false, a disabled Codex plugin that this call did not
    install stays disabled and the skip is logged, because Codex can only enable
    by adding again.
    """
    expected = f"{plugin}@{marketplace}"
    present, enabled = _plugin_status(host, marketplace, plugin)
    installed = not present
    if not present:
        _run(host, "plugin", "install" if host == "claude" else "add", expected)
        present, enabled = _plugin_status(host, marketplace, plugin)
    if (
        present
        and not enabled
        and host == "codex"
        and not installed
        and not reenable_codex
    ):
        logger.info(
            "host=%s plugin=%s event=skip-reenable reason=host-provided", host, expected
        )
        return installed
    if present and not enabled:
        try:
            # Codex has no enable command; adding again enables it.
            _run(host, "plugin", "enable" if host == "claude" else "add", expected)
        except BridgeError as error:
            if "already enabled" not in str(error).lower():
                raise
        present, enabled = _plugin_status(host, marketplace, plugin)
    if not present or not enabled:
        raise BridgeError(f"plugin did not become available and enabled: {expected}")
    return installed


def _ensure_plugin(
    host: str,
    marketplace: str,
    plugin: str,
    ownership_file: Path,
    desired: set[str],
    owned_desired: set[str],
    manifest_root: Path | None = None,
    package_root: Path | None = None,
    source_type: str = "generated",
    previous_owned: frozenset[str] = frozenset(),
    refresh: bool = False,
) -> None:
    identity = _identity("plugin", host, marketplace, plugin)
    record = f"{identity}\towned"
    desired.add(identity)
    expected = f"{plugin}@{marketplace}"
    if source_type != "generated":
        # A disabled host-provided Codex plugin stays disabled: the host wrapper owns it.
        installed = _ensure_installed_and_enabled(
            host, marketplace, plugin, reenable_codex=source_type != "host-provided"
        )
        if not installed and identity not in previous_owned:
            return  # adopted manual install stays unrecorded
        if refresh and not installed:
            _refresh_plugin(host, marketplace, plugin)
        owned_desired.add(record)
        _checkpoint(ownership_file, record)
        return
    if package_root is not None:
        _ensure_package_plugin(host, marketplace, plugin, package_root)
    elif host == "claude":
        present, enabled, installed_version, _ = _claude_plugin_state(
            marketplace, plugin
        )
        deployed_version = _claude_manifest_version(manifest_root, plugin)
        # Without a deployed version there is nothing to compare: never update.
        current = deployed_version is None or installed_version == deployed_version
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


def _remove_stale_record(kind: str, host: str, marketplace: str, plugin: str) -> None:
    if kind == "plugin":
        # Codex lists marketplace entries, which can omit stale registrations.
        if host == "codex" or _plugin_present(host, marketplace, plugin):
            _run(
                host,
                "plugin",
                "uninstall" if host == "claude" else "remove",
                f"{plugin}@{marketplace}",
            )
            if host == "claude" and _plugin_present(host, marketplace, plugin):
                raise BridgeError(f"plugin did not disappear: {plugin}@{marketplace}")
        return
    if kind != "marketplace":
        return
    if _marketplace_present(host, marketplace):
        _run(host, "plugin", "marketplace", "remove", marketplace)
        if _marketplace_present(host, marketplace):
            raise BridgeError(f"marketplace did not disappear: {marketplace}")


# Minimal adapters for hosts whose plugin CLI commands are not verified yet.
# Each adapter names an availability probe and the command that registers a local
# marketplace directory. A failed probe means the host is unavailable. Nothing here
# fails apply, and plugin install and ownership are not wired for these hosts yet.
_CLI_HOST_ADAPTERS: dict[str, dict[str, tuple[str, ...]]] = {
    "cursor": {
        "probe": ("cursor-agent", "plugin", "--help"),
        "marketplace_add": ("cursor-agent", "plugin", "marketplace", "add"),
    },
    "antigravity": {
        "probe": ("agy", "plugin", "--help"),
        "marketplace_add": ("agy", "plugin", "marketplace", "add"),
    },
}


def _cli_host_command(command: tuple[str, ...]) -> int | None:
    """Run a CLI host command; return its exit status, or None when it cannot run."""
    executable = shutil.which(command[0])
    if executable is None:
        return None
    try:
        result = subprocess.run(
            [executable, *command[1:]], capture_output=True, text=True, check=False
        )
    except OSError:
        return None
    if result.returncode:
        detail = (result.stderr.strip() or result.stdout.strip()).splitlines()
        logger.info(
            "command=%s status=%s detail=%s",
            " ".join(command[:3]),
            result.returncode,
            detail[0] if detail else "",
        )
    return result.returncode


def _register_cli_hosts(
    hosts: object, marketplaces: Mapping[str, object], destination: Path
) -> None:
    """Register generated marketplaces with each available CLI host."""
    if not isinstance(hosts, (list, tuple)) or not set(hosts) <= _CLI_HOSTS:
        raise BridgeError(f"cli_hosts must list hosts from {sorted(_CLI_HOSTS)!r}")
    for host in hosts:
        adapter = _CLI_HOST_ADAPTERS[host]
        if _cli_host_command(adapter["probe"]) != 0:
            logger.info("host=%s event=unavailable reason=no-plugin-cli", host)
            continue
        for name, definition in sorted(marketplaces.items()):
            if not isinstance(definition, Mapping):
                continue
            marketplace_hosts = definition.get("hosts", [])
            if definition.get("source_type") != "generated" or host not in (
                marketplace_hosts if isinstance(marketplace_hosts, list) else []
            ):
                continue
            locator = str(
                definition.get("source_locator")
                or destination / ".local/share/agent-plugins/marketplace"
            )
            status = _cli_host_command((*adapter["marketplace_add"], locator))
            logger.info(
                "host=%s marketplace=%s operation=plugin-marketplace-add status=%s",
                host,
                name,
                "unavailable" if status is None else status,
            )


def reconcile(
    destination: Path, declaration: Mapping[str, object], *, refresh: bool = False
) -> None:
    """Register declared marketplaces and plugins; ``refresh`` also updates owned external catalogs."""
    _validate_bridge_declaration(declaration)
    raw_bridge = declaration.get("plugin_bridge", declaration)
    if not isinstance(raw_bridge, Mapping):
        raise BridgeError("ai.plugin_bridge must be a table")
    environment = raw_bridge.get("environment", "default")
    marketplaces, plugins, capabilities = (
        raw_bridge.get(key, {}) for key in ("marketplaces", "plugins", "capabilities")
    )
    if not (
        isinstance(marketplaces, Mapping)
        and isinstance(plugins, Mapping)
        and isinstance(capabilities, Mapping)
    ):
        raise BridgeError("ai.plugin_bridge declarations must be tables")
    marketplaces = cast("Mapping[str, object]", marketplaces)
    plugins = cast("Mapping[str, object]", plugins)
    capabilities = cast("Mapping[str, object]", capabilities)
    state = _validate_state_root(destination)
    ownership_file = state / "agent-plugin-ownership"
    legacy = state / "agent-plugin-ownership.json"
    if ownership_file.exists():
        raw = _read_ownership(ownership_file)
    elif legacy.exists():
        raw = set(migrate_ownership(legacy).splitlines())
    else:
        raw = set()
    previous = _normalize_ownership(raw, marketplaces)
    if previous != raw or (legacy.exists() and not ownership_file.exists()):
        # Persist the classified records before any host mutation.
        _write_ownership(ownership_file, previous)
    if ownership_file.exists() and legacy.exists():
        legacy.unlink()
    unavailable_hosts: set[str] = set()
    unavailable_marketplaces: set[tuple[str, str]] = set()
    desired: set[str] = set()
    owned_desired: set[str] = set()
    previous_owned = frozenset(
        _record_identity(record) for record in previous if _is_owned(record)
    )
    source_types = {
        name: str(definition.get("source_type", ""))
        for name, definition in marketplaces.items()
        if isinstance(definition, Mapping)
    }
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
    refreshed: set[tuple[str, str]] = set()
    for _, name, host, source_type, locator in marketplace_rows:
        if host in unavailable_hosts:
            continue
        try:
            if _ensure_marketplace(
                host,
                name,
                source_type,
                locator,
                ownership_file,
                desired,
                owned_desired,
                previous_owned,
                refresh,
            ):
                refreshed.add((host, name))
        except HostUnavailableError:
            unavailable_hosts.add(host)
        except MarketplaceUnavailableError:
            logger.info("host=%s marketplace=%s event=unavailable", host, name)
            unavailable_marketplaces.add((host, name))

    for kind, declarations in (("capabilities", capabilities), ("plugins", plugins)):
        rows = _plugin_rows(kind, declarations, marketplaces, environment)
        for _, name, host, marketplace in rows:
            if host in unavailable_hosts:
                continue
            if (host, marketplace) in unavailable_marketplaces:
                desired.add(_identity("plugin", host, marketplace, name))
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
                    source_type=source_types[marketplace],
                    previous_owned=previous_owned,
                    **({"refresh": True} if (host, marketplace) in refreshed else {}),
                    **(
                        {"package_root": package_roots[kind, name, host]}
                        if (kind, name, host) in package_roots
                        else {}
                    ),
                )
            except HostUnavailableError:
                unavailable_hosts.add(host)
    generated_marketplaces = {
        name for name, source_type in source_types.items() if source_type == "generated"
    }
    for name, host, marketplace in _retired_plugin_rows(
        cast("Mapping[str, object]", raw_bridge.get("retired_plugins", {}))
    ):
        if host in unavailable_hosts:
            continue
        identity = _identity("plugin", host, marketplace, name)
        if (host, marketplace) in unavailable_marketplaces:
            continue  # the wrapper-owned marketplace is not registered here
        if identity not in previous_owned and marketplace not in generated_marketplaces:
            continue  # not provably ours; keep any ambiguous record
        try:
            _remove_stale_record("plugin", host, marketplace, name)
        except HostUnavailableError:
            unavailable_hosts.add(host)
            continue
        remaining = {
            record for record in previous if _record_identity(record) != identity
        }
        if remaining != previous:
            previous = remaining
            _write_ownership(ownership_file, _merge_ownership(previous, owned_desired))
    stale = sorted(
        (
            record
            for record in previous
            if _is_owned(record) and _record_identity(record) not in desired
        ),
        key=lambda value: (value.split("\t")[0] != "plugin", value),
    )
    for record in stale:
        kind, host, marketplace, plugin, _ = record.split("\t")
        if host in unavailable_hosts:
            continue
        try:
            _remove_stale_record(kind, host, marketplace, plugin)
        except HostUnavailableError:
            unavailable_hosts.add(host)
            continue
        previous.discard(record)
        _write_ownership(ownership_file, _merge_ownership(previous, owned_desired))
    retained = {
        record
        for record in previous
        if not _is_owned(record)
        or record.split("\t")[1] in unavailable_hosts
        or (record.split("\t")[1], record.split("\t")[2]) in unavailable_marketplaces
    }
    _write_ownership(ownership_file, _merge_ownership(retained, owned_desired))
    _register_cli_hosts(raw_bridge.get("cli_hosts", []), marketplaces, destination)


_REFRESH_INTERVAL_SECONDS = 24 * 60 * 60


def _refresh_requested(arguments: str) -> bool:
    """Return True when chezmoi ran with ``-R`` or ``--refresh-externals[=always]``.

    ``arguments`` is ``CHEZMOI_ARGS``, the space-joined command line that chezmoi
    exports to scripts.
    """
    for token in arguments.split()[1:]:
        if token == "--":
            break
        flag, _, value = token.partition("=")
        if flag == "--refresh-externals" or (
            flag.startswith("-") and not flag.startswith("--") and flag.endswith("R")
        ):
            return value in {"", "always"}
    return False


def _refresh_stamp(destination: Path) -> Path:
    return _validate_state_root(destination) / "agent-plugin-refresh"


def _refresh_due(destination: Path, now: float | None = None) -> bool:
    """Return True when no refresh is recorded in the last 24 hours."""
    try:
        refreshed = _refresh_stamp(destination).stat().st_mtime
    except FileNotFoundError:
        return True
    return (time.time() if now is None else now) - refreshed >= (
        _REFRESH_INTERVAL_SECONDS
    )


def _mark_refreshed(destination: Path) -> None:
    stamp = _refresh_stamp(destination)
    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.touch()


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
    reconcile_parser.add_argument(
        "--refresh",
        action="store_true",
        help="update owned public and internal marketplaces and their owned plugins;"
        " also implied by chezmoi -R or a last refresh older than 24 hours",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    formatter = logging.Formatter(
        "plugin-bridge: utc=%(asctime)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ"
    )
    formatter.converter = time.gmtime
    stream = sys.stderr
    try:
        # Keep failed log writes out of stderr's interpreter-shutdown buffer.
        stream = open(  # noqa: SIM115 - The handler uses this stream until process shutdown.
            sys.stderr.fileno(), "w", buffering=1, closefd=False
        )
    except (AttributeError, OSError, ValueError):
        pass
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    logging.raiseExceptions = False
    args = _parser().parse_args(argv)
    try:
        if args.command == "migrate-ownership":
            sys.stdout.write(migrate_ownership(args.path))
        elif args.command == "has-identity":
            return 0 if has_identity(sys.stdin.read(), args.field, args.expected) else 1
        else:
            refresh = (
                args.refresh
                or _refresh_requested(os.environ.get("CHEZMOI_ARGS", ""))
                or _refresh_due(args.destination)
            )
            reconcile(args.destination, json.load(sys.stdin), refresh=refresh)
            if refresh:
                _mark_refreshed(args.destination)
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
