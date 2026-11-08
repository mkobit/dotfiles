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
A four-field host-provided plugin record migrates as owned only while it is declared.
Four-field lines (the earlier format) and the legacy JSON state are classified by
``_classify_legacy`` and rewritten before any host mutation.

Each run reads every host's plugins and marketplaces once.
A mutating host command discards that host's snapshot, and the next query reads it again.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple, cast

if TYPE_CHECKING or bool(__package__):
    from skill_filter.plugin_declarations import (
        _CLI_HOSTS,
        _NATIVE_HOSTS,
        BridgeError,
        _marketplace_rows,
        _plugin_rows,
        _validate_bridge_declaration,
    )
else:
    from plugin_declarations import (
        _CLI_HOSTS,
        _NATIVE_HOSTS,
        BridgeError,
        _marketplace_rows,
        _plugin_rows,
        _validate_bridge_declaration,
    )


logger = logging.getLogger(__name__)


class HostUnavailableError(BridgeError):
    """Raised when a required host command is unavailable."""

    def __init__(self, host: str) -> None:
        super().__init__(f"required host command is unavailable: {host}")


class MarketplaceUnavailableError(BridgeError):
    """Raised when a host-provided marketplace is not registered on a host."""


class _Record(NamedTuple):
    kind: str  # "plugin" or "marketplace"
    host: str
    marketplace: str
    plugin: str


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


def _classify_legacy(
    record: _Record,
    marketplaces: Mapping[str, Mapping[str, Any]],
    declared: frozenset[tuple[str, str]],
) -> str | None:
    """Return the provenance for a four-field record, or None to drop it.

    The earlier bridge installed every declared plugin, so a host-provided plugin
    that is still declared migrates as owned; other host-provided records drop.
    """
    source_type = marketplaces.get(record.marketplace, {}).get("source_type")
    if source_type == "generated":
        return "owned"
    if source_type == "host-provided":
        declared_plugin = (record.marketplace, record.plugin) in declared
        return "owned" if record.plugin and declared_plugin else None
    return "ambiguous"


class _Ownership:
    """Provenance by record, written after every change so a later failure keeps it."""

    def __init__(self, path: Path, records: dict[_Record, str]) -> None:
        self.path = path
        self.records = records

    def owns(self, record: _Record) -> bool:
        return self.records.get(record) == "owned"

    def claim(self, record: _Record) -> None:
        self.records[record] = "owned"
        self.save()

    def drop(self, record: _Record) -> None:
        self.records.pop(record, None)
        self.save()

    def save(self) -> None:
        text = "".join(
            "\t".join((*record, provenance)) + "\n"
            for record, provenance in sorted(self.records.items())
        )
        if self.path.exists() and self.path.read_text(encoding="utf-8") == text:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(self.path)


def _read_ownership(path: Path) -> list[str]:
    """Return the validated lines: four fields (earlier format) or five with a provenance."""
    lines = list(filter(None, path.read_text(encoding="utf-8").splitlines()))
    for line in lines:
        fields = line.split("\t")
        if len(fields) not in {4, 5} or (
            len(fields) == 5 and fields[4] not in _PROVENANCES
        ):
            raise BridgeError(f"invalid ownership record: {line!r}")
    return lines


def _load_ownership(
    state: Path,
    marketplaces: Mapping[str, Mapping[str, Any]],
    declared: frozenset[tuple[str, str]],
) -> _Ownership:
    """Load the ownership file, migrating the legacy JSON or four-field lines first."""
    path, legacy = (
        state / "agent-plugin-ownership",
        state / "agent-plugin-ownership.json",
    )
    if path.exists():
        lines = _read_ownership(path)
    else:
        lines = migrate_ownership(legacy).splitlines() if legacy.exists() else []
    records: dict[_Record, str] = {}
    for line in lines:
        *identity, provenance = (
            line.split("\t") if line.count("\t") == 4 else (*line.split("\t"), None)
        )
        record = _Record(*identity)
        if record.host not in _NATIVE_HOSTS | _CLI_HOSTS:
            continue
        provenance = provenance or _classify_legacy(record, marketplaces, declared)
        if provenance is not None and records.get(record) != "owned":
            records[record] = provenance
    ownership = _Ownership(path, records)
    ownership.save()  # persist classified records before any host mutation
    legacy.unlink(missing_ok=True)
    return ownership


def _run(host: str, *args: str) -> str:
    command = shutil.which(host)
    if command is None:
        raise HostUnavailableError(host)
    try:
        result = subprocess.run(
            [command, *args], capture_output=True, text=True, check=False
        )
    except OSError as error:
        if error.errno != errno.ENOEXEC:
            raise
        result = subprocess.run(
            ["/bin/sh", command, *args], capture_output=True, text=True, check=False
        )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise BridgeError(f"{host} {' '.join(args)} failed: {detail}")
    return result.stdout


@dataclass(frozen=True)
class _Plugin:
    enabled: bool
    version: str | None
    path: Path | None  # Claude: install path; Codex: source in the marketplace


def _text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _path(value: object) -> Path | None:
    return Path(value) if isinstance(value, str) else None


class _Host:
    """One host CLI with a cached snapshot of its plugins and marketplaces."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.claude = name == "claude"
        self.reads = 0
        self.writes = 0
        self._plugins: dict[str, _Plugin] | None = None
        self._marketplaces: dict[str, Path | None] | None = None

    @property
    def plugins(self) -> dict[str, _Plugin]:
        """Installed plugins by ``plugin@marketplace``."""
        if self._plugins is None:
            self.reads += 1
            output = json.loads(_run(self.name, "plugin", "list", "--json"))
            if self.claude:
                self._plugins = {
                    item["id"]: _Plugin(
                        item.get("enabled") is True,
                        _text(item.get("version")),
                        _path(item.get("installPath")),
                    )
                    for item in output
                }
            else:
                self._plugins = {
                    item["pluginId"]: _Plugin(
                        item.get("enabled") is True,
                        _text(item.get("version")),
                        _path((item.get("source") or {}).get("path")),
                    )
                    for item in output["installed"]
                    if item.get("installed") is True
                }
        return self._plugins

    @property
    def marketplaces(self) -> dict[str, Path | None]:
        """Registered marketplaces mapped to their local source directory, if any."""
        if self._marketplaces is None:
            self.reads += 1
            output = json.loads(
                _run(self.name, "plugin", "marketplace", "list", "--json")
            )
            if self.claude:
                self._marketplaces = {
                    item["name"]: _path(item.get("path"))
                    if item.get("source") == "directory"
                    else None
                    for item in output
                }
            else:
                self._marketplaces = {}
                for item in output["marketplaces"]:
                    source = item.get("marketplaceSource") or {}
                    local = source.get("sourceType") == "local"
                    self._marketplaces[item["name"]] = (
                        _path(source.get("source")) if local else None
                    )
        return self._marketplaces

    def run(self, *args: str) -> str:
        """Run a mutating command and discard the snapshot."""
        logger.info("%s %s", self.name, " ".join(args))
        self.writes += 1
        self._plugins = self._marketplaces = None
        return _run(self.name, *args)

    def install(self, expected: str) -> None:
        self.run("plugin", "install" if self.claude else "add", expected)

    def uninstall(self, expected: str) -> None:
        self.run("plugin", "uninstall" if self.claude else "remove", expected)

    def enable(self, expected: str) -> None:
        # Codex has no enable command; adding again enables it.
        try:
            self.run("plugin", "enable" if self.claude else "add", expected)
        except BridgeError as error:
            if "already enabled" not in str(error).lower():
                raise

    def require_enabled(self, expected: str) -> _Plugin:
        plugin = self.plugins.get(expected)
        if plugin is None or not plugin.enabled:
            raise BridgeError(
                f"plugin did not become available and enabled: {expected}"
            )
        return plugin


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


def _manifest_version(manifest: Path) -> str | None:
    """Return the version in a plugin manifest, or None when it has none."""
    try:
        version = json.loads(manifest.read_text(encoding="utf-8")).get("version")
    except (OSError, ValueError, AttributeError):
        return None
    return version if isinstance(version, str) and version else None


def _claude_deployed_version(marketplace_root: Path | None, plugin: str) -> str | None:
    if marketplace_root is None:
        return None
    try:
        catalog = json.loads(
            (marketplace_root / ".claude-plugin/marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        source = next(
            item["source"] for item in catalog["plugins"] if item["name"] == plugin
        )
        manifest = marketplace_root / source / ".claude-plugin/plugin.json"
    except (OSError, ValueError, KeyError, TypeError, StopIteration):
        return None
    return _manifest_version(manifest)


def _codex_deployed_version(source: Path | None, plugin: str) -> str:
    version = (
        _manifest_version(source / ".codex-plugin/plugin.json") if source else None
    )
    if version is None:
        raise BridgeError(f"cannot read Codex plugin version: {plugin}")
    return version


def _validate_state_root(destination: Path) -> Path:
    relative = Path(".local/state/dotfiles")
    path = destination / relative
    if path.resolve() != destination.resolve() / relative:
        raise BridgeError(
            f"state root must not contain symlinks or resolve outside destination: {path}"
        )
    return path


def _repair_missing_codex_marketplaces(host: _Host, sources: Mapping[str, str]) -> None:
    """Read the Codex marketplaces, re-registering generated roots that lost their manifest."""
    try:
        host.marketplaces  # noqa: B018 - reading raises while a root lacks its manifest
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
            host.run("plugin", "marketplace", "remove", name)
            host.run("plugin", "marketplace", "add", locator)


def _ensure_marketplace(
    host: _Host,
    own: _Ownership,
    name: str,
    source_type: str,
    locator: str,
    refresh: bool,
) -> bool:
    """Register the marketplace; return True when ``refresh`` updated an owned one."""
    record = _Record("marketplace", host.name, name, "")
    registered = name in host.marketplaces
    if source_type == "host-provided":
        # Corporate wrappers own it: check presence only, never record.
        if not registered:
            raise MarketplaceUnavailableError(f"{name} ({host.name})")
        return False
    if not locator:
        raise BridgeError(f"marketplace has no source: {name}")
    if source_type == "generated":
        expected = Path(locator).resolve()
        current = host.marketplaces.get(name)
        if registered and current is None:
            raise BridgeError(
                f"plugin host returned no local source for marketplace: {name} ({host.name})"
            )
        if current is None or current.resolve() != expected:
            if registered:
                host.run("plugin", "marketplace", "remove", name)
            host.run("plugin", "marketplace", "add", locator)
            current = host.marketplaces.get(name)
            if current is None or current.resolve() != expected:
                raise BridgeError(
                    f"marketplace did not register expected source: {name} ({host.name}); expected {expected}"
                )
        own.claim(record)
        return False
    if registered and not own.owns(record):
        return False  # adopted manual registration: never updated or recorded
    if not registered:
        host.run("plugin", "marketplace", "add", locator)
        if name not in host.marketplaces:
            raise BridgeError(f"marketplace did not become available: {name}")
    elif refresh:
        host.run(
            "plugin",
            "marketplace",
            "update" if host.claude else "upgrade",
            name,
        )
    own.claim(record)
    return refresh and registered


def _ensure_external_plugin(host: _Host, expected: str, reenable: bool) -> bool:
    """Install when absent and enable when disabled; never update or remove.

    Returns True when this call installed the plugin.
    With ``reenable`` false, a disabled Codex plugin that this call did not install
    stays disabled and the skip is logged, because Codex can only enable by adding again.
    """
    installed = expected not in host.plugins
    if installed:
        host.install(expected)
    current = host.plugins.get(expected)
    if current is not None and not current.enabled:
        if not (installed or reenable or host.claude):
            logger.info(
                "%s %s: skip re-enable of host-provided plugin", host.name, expected
            )
            return False
        host.enable(expected)
    host.require_enabled(expected)
    return installed


def _refresh_external_plugin(host: _Host, expected: str) -> None:
    """Update an owned plugin of a refreshed marketplace; Codex reinstalls on a new version."""
    if host.claude:
        host.run("plugin", "update", expected)
        return
    # Codex has no update command. If `add` fails after `remove`, the plugin stays
    # uninstalled until the next refresh, and no ownership record is written for it.
    current = host.plugins.get(expected)
    if current is None or current.path is None:
        return
    available = _manifest_version(current.path / ".codex-plugin/plugin.json")
    if available is None:
        logger.info("%s %s: refresh skipped, no deployed version", host.name, expected)
    elif available != current.version:
        host.uninstall(expected)
        host.install(expected)


def _ensure_generated_plugin(
    host: _Host, expected: str, plugin: str, marketplace_root: Path | None
) -> None:
    """Install, update, or enable a plugin so it matches its deployed manifest version."""
    current = host.plugins.get(expected)
    if host.claude:
        deployed = _claude_deployed_version(marketplace_root, plugin)
        # Without a deployed version there is nothing to compare: never update.
        stale = (
            deployed is not None and current is not None and current.version != deployed
        )
        if current is None:
            host.install(expected)
        elif stale:
            host.run("plugin", "update", expected)
        elif current.enabled:
            return
        fresh = host.plugins.get(expected)
        if fresh is not None and not fresh.enabled:
            host.enable(expected)
        host.require_enabled(expected)
        return
    deployed = _codex_deployed_version(current.path, plugin) if current else None
    if current is None:
        host.install(expected)
    elif not current.enabled or current.version != deployed:
        host.uninstall(expected)
        host.install(expected)
    else:
        return
    fresh = host.require_enabled(expected)
    if fresh.version != _codex_deployed_version(fresh.path, plugin):
        raise BridgeError(f"plugin did not refresh to deployed version: {expected}")


def _ensure_package_plugin(host: _Host, expected: str, package_root: Path) -> None:
    """Install a packaged plugin and verify the installed content equals the package."""
    fingerprint = _package_fingerprint(package_root)
    current = host.plugins.get(expected)
    if host.claude:
        installed_root = current.path if current else None
        matches = (
            installed_root is not None
            and installed_root.is_dir()
            and _package_fingerprint(installed_root) == fingerprint
        )
        if current is not None and not matches:
            host.uninstall(expected)
            current = None
        if current is None:
            host.install(expected)
        fresh = host.plugins.get(expected)
        if fresh is not None and not fresh.enabled:
            host.enable(expected)
        installed_root = host.require_enabled(expected).path
    else:
        deployed = _manifest_version(package_root / ".codex-plugin/plugin.json")
        if (
            current
            and current.enabled
            and deployed is not None
            and current.version == deployed
        ):
            return  # the version is content-derived, so equal versions mean equal content
        response = json.loads(host.run("plugin", "add", expected, "--json"))
        installed_root = _path(response.get("installedPath"))
        host.require_enabled(expected)
        matches = False
    if matches:
        return
    if installed_root is None:
        raise BridgeError(
            f"plugin host returned no installed path for {expected}; update {host.name} and run chezmoi apply again"
        )
    if _package_fingerprint(installed_root) != fingerprint:
        raise BridgeError(
            f"installed plugin content differs from {package_root}: {expected}; reinstall the plugin and run chezmoi apply again"
        )


def _remove_plugin(host: _Host, expected: str) -> None:
    if expected not in host.plugins:
        if not host.claude:
            # Codex lists can omit stale registrations that stay in its config.
            try:
                host.uninstall(expected)
            except BridgeError as error:
                logger.info("%s", error)  # not installed: nothing to remove
        return
    host.uninstall(expected)
    if expected in host.plugins:
        raise BridgeError(f"plugin did not disappear: {expected}")


def _remove_marketplace(host: _Host, name: str) -> None:
    if name in host.marketplaces:
        host.run("plugin", "marketplace", "remove", name)
        if name in host.marketplaces:
            raise BridgeError(f"marketplace did not disappear: {name}")


# Antigravity (agy) installs a plugin from a local directory with its own CLI; it has no
# ~/.gemini/config/plugins.json route. The commands are lightly verified, so every failure is
# logged and never fails apply. The same ownership file as the other hosts records installs
# (kind ``plugin``, host ``antigravity``). Cursor has no plugin install command; chezmoi
# converges it by copying plugins to ~/.cursor/plugins/local/<name>/ instead.
_AGY_HOST = "antigravity"
# Manifest paths relative to a generated plugin directory; the first existing one wins.
_AGY_MANIFESTS = ("plugin.json", ".antigravity-plugin/plugin.json")
# The ``list --json`` schema is unverified: accept a top-level list or an object holding one.
_AGY_LIST_KEYS = ("plugins", "installed", "items", "entries", "data")


def _cli_host_command(command: tuple[str, ...]) -> tuple[int, str] | None:
    """Run a CLI host command; return (exit status, stdout), or None when it cannot run."""
    executable = shutil.which(command[0])
    if executable is None:
        return None
    try:
        result = subprocess.run(
            [executable, *command[1:]],
            capture_output=True,
            text=True,
            check=False,
            stdin=subprocess.DEVNULL,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        detail = (result.stderr.strip() or result.stdout.strip()).splitlines()
        logger.info(
            "command=%s status=%s detail=%s",
            " ".join(command[:3]),
            result.returncode,
            detail[0] if detail else "",
        )
    return result.returncode, result.stdout


def _parse_agy_plugins(output: str) -> dict[str, str | None] | None:
    """Return installed agy plugin names with their version (None when not listed).

    Returns None when the output cannot be parsed, so the caller changes nothing.
    """
    try:
        payload = json.loads(output)
    except ValueError:
        return None
    if isinstance(payload, Mapping):
        payload = next(
            (
                payload[key]
                for key in _AGY_LIST_KEYS
                if isinstance(payload.get(key), list)
            ),
            None,
        )
    if not isinstance(payload, list):
        return None
    installed: dict[str, str | None] = {}
    for entry in payload:
        if isinstance(entry, str):
            installed[entry] = None
        elif isinstance(entry, Mapping) and isinstance(entry.get("name"), str):
            version = entry.get("version")
            installed[entry["name"]] = version if isinstance(version, str) else None
    if payload and not installed:
        return None
    return installed


def _agy(*command: str) -> tuple[int, str] | None:
    return _cli_host_command(("agy", "plugin", *command))


def _agy_mutate(name: str, *command: str) -> bool:
    """Run an agy plugin command; log the outcome and return True on exit status 0."""
    result = _agy(*command)
    logger.info(
        "host=antigravity plugin=%s operation=plugin-%s status=%s",
        name,
        command[0],
        "unavailable" if result is None else result[0],
    )
    return result is not None and result[0] == 0


def _desired_agy_plugins(
    marketplaces: Mapping[str, Mapping[str, Any]], destination: Path
) -> dict[str, tuple[str, Path, str | None]]:
    """Map plugin name to (marketplace, directory, manifest version) for agy."""
    desired: dict[str, tuple[str, Path, str | None]] = {}
    for marketplace, definition in sorted(marketplaces.items()):
        if definition.get(
            "source_type"
        ) != "generated" or _AGY_HOST not in definition.get("hosts", []):
            continue
        root = Path(
            definition.get("source_locator")
            or destination / ".local/share/agent-plugins/marketplace"
        )
        for plugin_dir in sorted(
            path for path in (root / "plugins").glob("*") if path.is_dir()
        ):
            manifest_path = next(
                (
                    plugin_dir / relative
                    for relative in _AGY_MANIFESTS
                    if (plugin_dir / relative).is_file()
                ),
                None,
            )
            if manifest_path is None:
                continue
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                manifest = {}
            if not isinstance(manifest, Mapping):
                manifest = {}
            name = manifest.get("name")
            version = manifest.get("version")
            desired[name if isinstance(name, str) else plugin_dir.name] = (
                marketplace,
                plugin_dir,
                version if isinstance(version, str) else None,
            )
    return desired


def _converge_agy(
    marketplaces: Mapping[str, Mapping[str, Any]], destination: Path, own: _Ownership
) -> None:
    """Install missing or changed plugins, uninstall owned and undesired ones.

    Plugins that the bridge did not install are never uninstalled. An unusable host or an
    unparseable list changes nothing. Failures are logged and never raised.
    """
    probe, listing = _agy("--help"), _agy("list", "--json")
    if probe is None or probe[0] or listing is None or listing[0]:
        logger.info("host=%s event=unavailable reason=no-plugin-cli", _AGY_HOST)
        return
    installed = _parse_agy_plugins(listing[1])
    if installed is None:
        logger.info("host=%s event=skipped reason=unparseable-plugin-list", _AGY_HOST)
        return
    desired = _desired_agy_plugins(marketplaces, destination)
    for name, (marketplace, plugin_dir, version) in sorted(desired.items()):
        if name in installed:
            listed_version = installed[name]
            if listed_version is None or version is None or listed_version == version:
                continue
            if not _agy_mutate(name, "uninstall", name):
                continue
        if _agy_mutate(name, "install", str(plugin_dir)):
            own.claim(_Record("plugin", _AGY_HOST, marketplace, name))
    for record in sorted(own.records):
        if record.host != _AGY_HOST or not own.owns(record):
            continue
        name = record.plugin
        if desired.get(name, ("",))[0] == record.marketplace:
            continue  # still desired: keep the record
        # A name desired from another marketplace keeps its install; only the record goes.
        if (
            name in desired
            or name not in installed
            or _agy_mutate(name, "uninstall", name)
        ):
            own.drop(record)


class _PluginRow(NamedTuple):
    name: str
    marketplace: str
    package_root: Path | None


@dataclass(frozen=True)
class _HostPlan:
    """What one native host should hold, in apply order."""

    marketplaces: Sequence[tuple[str, str, str]]  # name, source type, locator
    plugins: Sequence[_PluginRow]
    source_types: Mapping[str, str]
    marketplace_roots: Mapping[str, Path]  # generated marketplaces only


def _converge_host(
    host: _Host, own: _Ownership, plan: _HostPlan, *, refresh: bool
) -> None:
    """Install or update desired plugins, then remove owned-undesired ones.

    Plugins the bridge did not install (unowned) are never removed.
    """
    generated = {
        name: locator
        for name, source_type, locator in plan.marketplaces
        if source_type == "generated"
    }
    if not host.claude and generated:
        _repair_missing_codex_marketplaces(host, generated)
    refreshed: set[str] = set()
    unavailable: set[str] = set()
    for name, source_type, locator in plan.marketplaces:
        try:
            if _ensure_marketplace(host, own, name, source_type, locator, refresh):
                refreshed.add(name)
        except MarketplaceUnavailableError:
            logger.info(
                "%s %s: host-provided marketplace is unavailable", host.name, name
            )
            unavailable.add(name)
    for row in plan.plugins:
        if row.marketplace in unavailable:
            continue
        expected = f"{row.name}@{row.marketplace}"
        source_type = plan.source_types[row.marketplace]
        record = _Record("plugin", host.name, row.marketplace, row.name)
        if source_type != "generated":
            # A disabled host-provided Codex plugin stays disabled: the host wrapper owns it.
            installed = _ensure_external_plugin(
                host, expected, reenable=source_type != "host-provided"
            )
            if not installed and not own.owns(record):
                continue  # adopted manual install stays unrecorded
            if row.marketplace in refreshed and not installed:
                _refresh_external_plugin(host, expected)
        elif row.package_root is not None:
            _ensure_package_plugin(host, expected, row.package_root)
        else:
            _ensure_generated_plugin(
                host, expected, row.name, plan.marketplace_roots.get(row.marketplace)
            )
        own.claim(record)
    desired = {
        _Record("marketplace", host.name, name, "") for name, _, _ in plan.marketplaces
    }
    desired |= {
        _Record("plugin", host.name, row.marketplace, row.name) for row in plan.plugins
    }
    stale = sorted(
        (
            record
            for record in own.records
            if record.host == host.name and own.owns(record) and record not in desired
        ),
        key=lambda record: (record.kind != "plugin", record),
    )
    for record in stale:
        if record.kind == "plugin":
            _remove_plugin(host, f"{record.plugin}@{record.marketplace}")
        else:
            _remove_marketplace(host, record.marketplace)
        own.drop(record)


def reconcile(
    destination: Path, declaration: Mapping[str, object], *, refresh: bool = False
) -> None:
    """Register declared marketplaces and plugins; ``refresh`` also updates owned external catalogs."""
    _validate_bridge_declaration(declaration)
    bridge = cast("Mapping[str, Any]", declaration.get("plugin_bridge", declaration))
    environment = bridge.get("environment", "default")
    marketplaces, plugins, capabilities = (
        cast("Mapping[str, Mapping[str, Any]]", bridge.get(key, {}))
        for key in ("marketplaces", "plugins", "capabilities")
    )
    declared = frozenset(
        (str(definition.get("marketplace", "")), name)
        for table in (plugins, capabilities)
        for name, definition in table.items()
    )
    own = _load_ownership(_validate_state_root(destination), marketplaces, declared)
    source_types = {
        name: str(definition.get("source_type", ""))
        for name, definition in marketplaces.items()
    }
    marketplace_rows = _marketplace_rows(destination, marketplaces)
    marketplace_roots = {
        (name, host): Path(locator)
        for _, name, host, source_type, locator in marketplace_rows
        if source_type == "generated"
    }
    plugin_rows: list[tuple[str, _PluginRow]] = []  # host, row
    for declarations in (capabilities, plugins):
        for _, name, host, marketplace in _plugin_rows(
            declarations, marketplaces, environment
        ):
            package_path = declarations[name].get("package_path")
            package_root = None
            if package_path is not None:
                root = marketplace_roots[marketplace, host]
                package_root = root / package_path
                try:
                    package_root.resolve().relative_to(root.resolve())
                except ValueError as error:
                    raise BridgeError(
                        f"plugin package must resolve inside its marketplace: {package_root}"
                    ) from error
            plugin_rows.append((host, _PluginRow(name, marketplace, package_root)))
    hosts = [_Host(name) for name in sorted(_NATIVE_HOSTS)]
    for host in hosts:
        plan = _HostPlan(
            marketplaces=[
                (name, source_type, locator)
                for _, name, row_host, source_type, locator in marketplace_rows
                if row_host == host.name
            ],
            plugins=[row for row_host, row in plugin_rows if row_host == host.name],
            source_types=source_types,
            marketplace_roots={
                name: root
                for (name, root_host), root in marketplace_roots.items()
                if root_host == host.name
            },
        )
        try:
            _converge_host(host, own, plan, refresh=refresh)
        except HostUnavailableError as error:
            logger.info("%s", error)  # keep this host's records for a later run
    logger.info(
        "reconciled: %s",
        ", ".join(f"{h.name} reads={h.reads} writes={h.writes}" for h in hosts),
    )
    cli_hosts = bridge.get("cli_hosts", [])
    if not isinstance(cli_hosts, list) or not set(cli_hosts) <= _CLI_HOSTS:
        raise BridgeError(f"cli_hosts must list hosts from {sorted(_CLI_HOSTS)!r}")
    if _AGY_HOST in cli_hosts:
        _converge_agy(marketplaces, destination, own)


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


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="plugin-bridge: %(message)s")
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    reconcile_parser = commands.add_parser("reconcile")
    reconcile_parser.add_argument("--destination", required=True, type=Path)
    reconcile_parser.add_argument(
        "--refresh",
        action="store_true",
        help="update owned public and internal marketplaces and their owned plugins;"
        " also implied by chezmoi -R or a last refresh older than 24 hours",
    )
    args = parser.parse_args(argv)
    try:
        refresh = (
            args.refresh
            or _refresh_requested(os.environ.get("CHEZMOI_ARGS", ""))
            or _refresh_due(args.destination)
        )
        reconcile(args.destination, json.load(sys.stdin), refresh=refresh)
        if refresh:
            _mark_refreshed(args.destination)
    except (BridgeError, KeyError, TypeError, ValueError, OSError) as error:
        logger.error("%s", error)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
