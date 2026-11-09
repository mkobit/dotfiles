from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from skill_filter import plugin_bridge

HOSTS = ("claude", "codex")
BridgeError = plugin_bridge.BridgeError


class FakeHosts:
    """Stateful fake of the Claude and Codex plugin CLIs, installed as ``_run``."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.marketplaces: dict[str, dict[str, str]] = {h: {} for h in HOSTS}
        self.plugins: dict[str, dict[str, dict[str, Any]]] = {h: {} for h in HOSTS}
        self.sources: dict[str, str] = {}  # locator -> marketplace name for `add`
        self.versions: dict[str, str] = {}  # plugin id -> version a fresh install gets
        self.paths: dict[
            str, Path
        ] = {}  # plugin id -> install (Claude) or source (Codex)
        self.payloads: dict[str, Path] = {}  # plugin id -> directory copied on install
        self.unavailable: set[str] = set()
        self.fail: set[tuple[str, ...]] = set()
        self.broken: set[str] = set()  # Codex roots without a manifest
        self.sticky = False  # uninstall changes nothing
        self.never_enabled = False  # install and enable leave the plugin disabled
        self.on_refresh: Callable[[], None] = lambda: None

    @property
    def writes(self) -> list[tuple[str, ...]]:
        return [call for call in self.calls if "list" not in call[1:4]]

    @property
    def reads(self) -> list[tuple[str, ...]]:
        return [call for call in self.calls if "list" in call[1:4]]

    def add_plugin(self, host: str, plugin_id: str, version="1", enabled=True) -> None:
        self.plugins[host][plugin_id] = {
            "enabled": enabled,
            "version": version,
            "path": self.paths.get(plugin_id),
        }

    def __call__(self, host: str, *args: str) -> str:
        self.calls.append((host, *args))
        if host in self.unavailable:
            raise plugin_bridge.HostUnavailableError(host)
        if args in self.fail:
            raise BridgeError(f"{host} {' '.join(args)} failed")
        plugins = self.plugins[host]
        if args == ("plugin", "list", "--json"):
            return self._list_plugins(host)
        if args == ("plugin", "marketplace", "list", "--json"):
            return self._list_marketplaces(host)
        if args[:3] == ("plugin", "marketplace", "add"):
            self.marketplaces[host][self.sources[args[3]]] = args[3]
        elif args[:3] == ("plugin", "marketplace", "remove"):
            del self.marketplaces[host][args[3]]
        elif args[:3] in {
            ("plugin", "marketplace", "update"),
            ("plugin", "marketplace", "upgrade"),
        }:
            self.on_refresh()
        elif args[1] in {"install", "add", "update", "enable"}:
            expected = args[2]
            if args[1] == "enable" and expected not in plugins:
                raise BridgeError("not installed")
            old = plugins.get(expected, {})
            plugins[expected] = {
                "enabled": not self.never_enabled,
                "version": self.versions.get(expected, old.get("version", "1")),
                "path": self.paths.get(expected),
            }
            if expected in self.payloads:
                shutil.copytree(
                    self.payloads[expected], self.paths[expected], dirs_exist_ok=True
                )
            if args[-1] == "--json":
                return json.dumps({"installedPath": str(self.paths.get(expected))})
        elif args[1] in {"uninstall", "remove"}:
            if not self.sticky:
                plugins.pop(args[2], None)
        else:
            raise AssertionError(args)
        return ""

    def _list_plugins(self, host: str) -> str:
        items = [
            (plugin_id, state)
            for plugin_id, state in sorted(self.plugins[host].items())
        ]
        if host == "claude":
            return json.dumps(
                [
                    {
                        "id": plugin_id,
                        "enabled": state["enabled"],
                        "version": state["version"],
                        "installPath": str(state["path"]) if state["path"] else None,
                    }
                    for plugin_id, state in items
                ]
            )
        return json.dumps(
            {
                "installed": [
                    {
                        "pluginId": plugin_id,
                        "installed": True,
                        "enabled": state["enabled"],
                        "version": state["version"],
                        "source": {"path": str(state["path"])}
                        if state["path"]
                        else None,
                    }
                    for plugin_id, state in items
                ]
            }
        )

    def _list_marketplaces(self, host: str) -> str:
        registered = self.marketplaces[host]
        for name, locator in registered.items():
            if host == "codex" and locator in self.broken:
                raise BridgeError(
                    "codex plugin marketplace list --json failed: error loading:\n"
                    f"- `{name}` at {locator}: marketplace root does not contain a supported manifest"
                )
        local = {name: locator.startswith("/") for name, locator in registered.items()}
        if host == "claude":
            return json.dumps(
                [
                    {"name": n, "source": "directory" if local[n] else "git", "path": p}
                    for n, p in registered.items()
                ]
            )
        return json.dumps(
            {
                "marketplaces": [
                    {
                        "name": n,
                        "marketplaceSource": {
                            "sourceType": "local" if local[n] else "git",
                            "source": p,
                        },
                    }
                    for n, p in registered.items()
                ]
            }
        )


@pytest.fixture
def fake(monkeypatch) -> FakeHosts:
    hosts = FakeHosts()
    monkeypatch.setattr(plugin_bridge, "_run", hosts)
    return hosts


def _root(tmp_path: Path) -> Path:
    return tmp_path / ".local/share/agent-plugins/marketplace"


def _ownership_file(tmp_path: Path) -> Path:
    return tmp_path / ".local/state/dotfiles/agent-plugin-ownership"


def _records(tmp_path: Path) -> list[str]:
    path = _ownership_file(tmp_path)
    return path.read_text().splitlines() if path.exists() else []


def _write_records(tmp_path: Path, *lines: str) -> None:
    path = _ownership_file(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{line}\n" for line in lines))


def _declaration(
    marketplaces: dict[str, Any],
    plugins: dict[str, Any] | None = None,
    capabilities: dict[str, Any] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "plugin_bridge": {
            "marketplaces": marketplaces,
            "plugins": plugins or {},
            "capabilities": capabilities or {},
            **extra,
        }
    }


def _generated(*hosts: str) -> dict[str, Any]:
    return {"source_type": "generated", "hosts": list(hosts or HOSTS)}


def _deploy(tmp_path: Path, fake: FakeHosts, plugin: str, version: str | None) -> Path:
    """Write the deployed manifests of a generated plugin; the fake installs from it."""
    root = _root(tmp_path)
    directory = root / "plugins" / plugin
    manifest = {"name": plugin, **({"version": version} if version is not None else {})}
    for host in HOSTS:
        (directory / f".{host}-plugin").mkdir(parents=True, exist_ok=True)
        (directory / f".{host}-plugin/plugin.json").write_text(json.dumps(manifest))
    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (root / ".claude-plugin/marketplace.json").write_text(
        json.dumps({"plugins": [{"name": plugin, "source": f"./plugins/{plugin}"}]})
    )
    fake.sources[str(root)] = "market"
    fake.paths[f"{plugin}@market"] = directory
    if version is not None:
        fake.versions[f"{plugin}@market"] = version
    return directory


# --- declaration validation ---


def _valid_bridge() -> dict[str, Any]:
    return _declaration(
        {"market": {**_generated("claude", "codex", "cursor"), "order": 100}},
        {"plugin": {"marketplace": "market", "environments": ["local"]}},
        {
            "capability": {
                "marketplace": "market",
                "hosts": ["claude", "codex", "cursor"],
            }
        },
        environment="local",
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda b: b["marketplaces"].update({"bad/name": {}}), "marketplace name"),
        (lambda b: b["plugins"].update({"bad/name": {}}), "plugin name"),
        (lambda b: b["capabilities"].update({"bad/name": {}}), "capability name"),
        (lambda b: b["plugins"]["plugin"].update(marketplace="missing"), "marketplace"),
        (lambda b: b["marketplaces"]["market"].update(hosts=["cursorx"]), "host"),
        (lambda b: b["plugins"]["plugin"].update(hosts=["cursorx"]), "host"),
        (
            lambda b: b["marketplaces"]["market"].update(source_type="unknown"),
            "source type",
        ),
        (
            lambda b: b["marketplaces"]["market"].update(source_type="public"),
            "source locator",
        ),
        (lambda b: b["plugins"]["plugin"].update(order="200"), "order"),
        (
            lambda b: b["plugins"]["plugin"].update(environments=["bad env"]),
            "environment",
        ),
        (
            lambda b: b["capabilities"]["capability"].update(package_path="../out"),
            "package_path",
        ),
        (
            lambda b: b["capabilities"]["capability"].update(package_path="/abs"),
            "package_path",
        ),
        (lambda b: b["marketplaces"]["market"].update(hosts=["claude"]), "subset"),
    ],
)
def test_reconcile_validates_declarations_before_side_effects(
    tmp_path, fake, mutation, message
):
    declaration = _valid_bridge()
    mutation(declaration["plugin_bridge"])

    with pytest.raises(BridgeError, match=message):
        plugin_bridge.reconcile(tmp_path, declaration)

    assert fake.calls == []
    assert not (tmp_path / ".local").exists()


def test_package_path_requires_generated_marketplace(tmp_path, fake):
    declaration = _declaration(
        {
            "market": {
                "source_type": "public",
                "source_locator": "o/r",
                "hosts": ["claude"],
            }
        },
        capabilities={"demo": {"marketplace": "market", "package_path": "./p"}},
    )
    with pytest.raises(BridgeError, match="generated marketplace"):
        plugin_bridge.reconcile(tmp_path, declaration)


def test_package_path_cannot_resolve_outside_marketplace(tmp_path, fake):
    _root(tmp_path).mkdir(parents=True)
    (tmp_path / "outside").mkdir()
    (_root(tmp_path) / "link").symlink_to(tmp_path / "outside")
    declaration = _declaration(
        {"market": _generated("claude")},
        capabilities={"demo": {"marketplace": "market", "package_path": "./link"}},
    )
    with pytest.raises(BridgeError, match="inside its marketplace"):
        plugin_bridge.reconcile(tmp_path, declaration)
    assert fake.writes == []


def test_unknown_retired_plugins_key_is_ignored(tmp_path, fake):
    declaration = _declaration({}, retired_plugins={"gone": {"marketplace": "m"}})
    plugin_bridge.reconcile(tmp_path, declaration)
    assert fake.writes == []


# --- no-change runs ---


def test_no_change_reconcile_reads_each_host_once_and_writes_nothing(tmp_path, fake):
    package = _deploy(tmp_path, fake, "pkg", "4")
    _deploy(tmp_path, fake, "plain", "2")
    fake.payloads["pkg@market"] = package
    fake.paths["pkg@market"] = tmp_path / "cache"
    fake.sources.update({"owner/repo": "pub"})
    for host in HOSTS:
        fake.marketplaces[host]["wrapper"] = "https://example.test/wrapper.git"
        fake.add_plugin(host, "wrapped@wrapper")
        fake.add_plugin(host, "manual@other")
    declaration = _declaration(
        {
            "market": _generated(),
            "pub": {
                "source_type": "public",
                "source_locator": "owner/repo",
                "hosts": list(HOSTS),
            },
            "wrapper": {"source_type": "host-provided", "hosts": list(HOSTS)},
        },
        plugins={
            "plain": {"marketplace": "market"},
            "ext": {"marketplace": "pub"},
            "wrapped": {"marketplace": "wrapper"},
        },
        capabilities={
            "pkg": {"marketplace": "market", "package_path": "./plugins/pkg"}
        },
    )
    plugin_bridge.reconcile(tmp_path, declaration)
    assert fake.writes
    records = _records(tmp_path)
    fake.calls.clear()

    plugin_bridge.reconcile(tmp_path, declaration)

    assert len(fake.reads) == 4
    assert fake.writes == []
    assert _records(tmp_path) == records


# --- ordering and host handling ---


def test_reconcile_orders_registrations_and_filters_environment(tmp_path, fake):
    for locator, name in (("/z", "z"), ("/a", "a")):
        fake.sources[locator] = name
    declaration = _declaration(
        {
            "z": {
                "source_type": "generated",
                "source_locator": "/z",
                "hosts": ["codex", "cursor"],
                "order": 10,
            },
            "a": {
                "source_type": "generated",
                "source_locator": "/a",
                "hosts": ["claude"],
                "order": 10,
            },
        },
        plugins={
            "skip": {"marketplace": "a", "environments": ["local"]},
            "active": {"marketplace": "z", "environments": ["remote"]},
        },
        capabilities={"z-cap": {"marketplace": "a"}},
        environment="remote",
    )
    with pytest.raises(BridgeError):  # no manifests; only the order of calls matters
        plugin_bridge.reconcile(tmp_path, declaration)
    assert [call[:4] for call in fake.writes[:2]] == [
        ("claude", "plugin", "marketplace", "add"),
        ("claude", "plugin", "install", "z-cap@a"),
    ]


def test_unavailable_host_retains_records_and_other_hosts_proceed(tmp_path, fake):
    fake.unavailable.add("claude")
    _deploy(tmp_path, fake, "demo", "1")
    _write_records(
        tmp_path,
        "plugin\tclaude\tmarket\told\towned",
        "plugin\tclaude\tmarket\tman\tambiguous",
    )
    declaration = _declaration(
        {"market": _generated()}, plugins={"demo": {"marketplace": "market"}}
    )

    plugin_bridge.reconcile(tmp_path, declaration)

    assert "demo@market" in fake.plugins["codex"]
    assert _records(tmp_path) == [
        "marketplace\tcodex\tmarket\t\towned",
        "plugin\tclaude\tmarket\tman\tambiguous",
        "plugin\tclaude\tmarket\told\towned",
        "plugin\tcodex\tmarket\tdemo\towned",
    ]


def test_reconcile_rejects_symlinked_state_root(tmp_path):
    (tmp_path / "elsewhere").mkdir()
    (tmp_path / ".local").mkdir()
    (tmp_path / ".local/state").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(BridgeError, match="symlinks"):
        plugin_bridge.reconcile(tmp_path, _declaration({}))


# --- generated marketplaces ---


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize(
    ("registered", "expected_writes"),
    [
        (None, ["add"]),
        ("/old", ["remove", "add"]),
        ("current", []),
    ],
)
def test_generated_marketplace_converges_to_the_deployed_source(
    tmp_path, fake, host, registered, expected_writes
):
    root = str(_root(tmp_path))
    fake.sources.update({root: "market", "/old": "market"})
    if registered:
        fake.marketplaces[host]["market"] = (
            root if registered == "current" else registered
        )
    plugin_bridge.reconcile(tmp_path, _declaration({"market": _generated(host)}))
    assert [
        call[3] for call in fake.writes if call[0] == host and call[2] == "marketplace"
    ] == [w for w in expected_writes]
    assert fake.marketplaces[host] == {"market": root}
    assert f"marketplace\t{host}\tmarket\t\towned" in _records(tmp_path)


def test_generated_marketplace_with_non_local_source_is_an_error(tmp_path, fake):
    fake.marketplaces["claude"]["market"] = "https://example.test/m.git"
    with pytest.raises(BridgeError, match="no local source"):
        plugin_bridge.reconcile(
            tmp_path, _declaration({"market": _generated("claude")})
        )
    assert fake.writes == []


def test_failed_marketplace_add_stops_before_plugins(tmp_path, fake):
    root = str(_root(tmp_path))
    fake.sources[root] = "market"
    fake.fail.add(("plugin", "marketplace", "add", root))
    declaration = _declaration(
        {"market": _generated("claude")}, plugins={"d": {"marketplace": "market"}}
    )
    with pytest.raises(BridgeError, match="failed"):
        plugin_bridge.reconcile(tmp_path, declaration)
    assert all(call[2] == "marketplace" for call in fake.writes)


def test_codex_marketplace_with_missing_manifest_is_reregistered(tmp_path, fake):
    root = str(_root(tmp_path))
    fake.sources.update({root: "market", "/stale": "market"})
    fake.marketplaces["codex"]["market"] = "/stale"
    fake.broken.add("/stale")

    plugin_bridge.reconcile(tmp_path, _declaration({"market": _generated("codex")}))

    assert [call[3] for call in fake.writes] == ["remove", "add"]
    assert fake.marketplaces["codex"] == {"market": root}


def test_unrelated_codex_marketplace_errors_are_not_repaired(tmp_path, fake):
    fake.fail.add(("plugin", "marketplace", "list", "--json"))
    with pytest.raises(BridgeError, match="failed"):
        plugin_bridge.reconcile(tmp_path, _declaration({"market": _generated("codex")}))
    assert fake.writes == []


# --- generated plugins ---


@pytest.mark.parametrize(
    ("host", "installed", "deployed", "expected"),
    [
        ("claude", None, "2", ["install"]),
        ("claude", ("2", True), "2", []),
        ("claude", ("1", True), "2", ["update"]),
        ("claude", ("1", True), None, []),  # nothing to compare: never update
        ("claude", ("2", False), "2", ["enable"]),
        ("codex", None, "2", ["add"]),
        ("codex", ("2", True), "2", []),
        ("codex", ("1", True), "2", ["remove", "add"]),
        ("codex", ("2", False), "2", ["remove", "add"]),
    ],
)
def test_generated_plugin_matches_the_deployed_manifest(
    tmp_path, fake, host, installed, deployed, expected
):
    _deploy(tmp_path, fake, "demo", deployed)
    fake.marketplaces[host]["market"] = str(_root(tmp_path))
    if installed:
        fake.add_plugin(host, "demo@market", *installed)
    declaration = _declaration(
        {"market": _generated(host)}, plugins={"demo": {"marketplace": "market"}}
    )

    plugin_bridge.reconcile(tmp_path, declaration)

    assert [call[2] for call in fake.writes] == expected
    assert fake.plugins[host]["demo@market"]["enabled"]
    assert f"plugin\t{host}\tmarket\tdemo\towned" in _records(tmp_path)


@pytest.mark.parametrize("host", HOSTS)
def test_generated_plugin_that_stays_disabled_is_an_error(tmp_path, fake, host):
    _deploy(tmp_path, fake, "demo", "1")
    fake.never_enabled = True
    declaration = _declaration(
        {"market": _generated(host)}, plugins={"demo": {"marketplace": "market"}}
    )
    with pytest.raises(BridgeError, match="available and enabled"):
        plugin_bridge.reconcile(tmp_path, declaration)
    assert "plugin\t" + host + "\tmarket\tdemo\towned" not in _records(tmp_path)


def test_codex_plugin_without_a_readable_manifest_version_is_an_error(tmp_path, fake):
    directory = _deploy(tmp_path, fake, "demo", None)
    fake.marketplaces["codex"]["market"] = str(_root(tmp_path))
    fake.add_plugin("codex", "demo@market", "1")
    declaration = _declaration(
        {"market": _generated("codex")}, plugins={"demo": {"marketplace": "market"}}
    )
    with pytest.raises(BridgeError, match="cannot read Codex plugin version"):
        plugin_bridge.reconcile(tmp_path, declaration)
    assert directory.exists()


# --- package plugins ---


def _package(tmp_path: Path, version: str = "7.0.0") -> Path:
    package = tmp_path / "source"
    (package / ".codex-plugin").mkdir(parents=True)
    (package / ".codex-plugin/plugin.json").write_text(
        json.dumps({"name": "demo", "version": version})
    )
    (package / "payload").write_text("original\n")
    return package


@pytest.mark.parametrize("change", ["path", "bytes", "executable", "symlink"])
def test_package_fingerprint_tracks_content_without_absolute_paths(tmp_path, change):
    source, installed = tmp_path / "source", tmp_path / "cache"
    source.mkdir()
    (source / "payload").write_text("original\n", encoding="utf-8")
    (source / "link").symlink_to("payload")
    shutil.copytree(source, installed, symlinks=True)
    original = plugin_bridge._package_fingerprint(source)
    assert plugin_bridge._package_fingerprint(installed) == original

    if change == "path":
        (source / "payload").rename(source / "renamed")
    elif change == "bytes":
        (source / "payload").write_text("changed\n", encoding="utf-8")
    elif change == "executable":
        (source / "payload").chmod(0o755)
    else:
        (source / "link").unlink()
        (source / "link").symlink_to("other")

    assert plugin_bridge._package_fingerprint(source) != original


@pytest.fixture
def package_host(tmp_path, fake):
    """A package plugin ``demo@market`` deployed at version 7.0.0 on both hosts."""
    package = _root(tmp_path) / "plugins/demo"
    shutil.copytree(_package(tmp_path), package)
    fake.sources[str(_root(tmp_path))] = "market"
    fake.paths["demo@market"] = tmp_path / "cache"
    fake.payloads["demo@market"] = package
    fake.versions["demo@market"] = "7.0.0"
    for host in HOSTS:
        fake.marketplaces[host]["market"] = str(_root(tmp_path))
    return package


def _reconcile_package(tmp_path: Path, host: str) -> None:
    declaration = _declaration(
        {"market": _generated(host)},
        capabilities={
            "demo": {"marketplace": "market", "package_path": "./plugins/demo"}
        },
    )
    plugin_bridge.reconcile(tmp_path, declaration)


@pytest.mark.parametrize("host", HOSTS)
def test_package_plugin_installs_then_settles(tmp_path, fake, package_host, host):
    _reconcile_package(tmp_path, host)
    assert [call[2] for call in fake.writes] == [
        "install" if host == "claude" else "add"
    ]
    fake.calls.clear()

    _reconcile_package(tmp_path, host)

    assert fake.writes == []


def test_claude_package_plugin_with_changed_content_is_reinstalled(
    tmp_path, fake, package_host
):
    _reconcile_package(tmp_path, "claude")
    (package_host / "payload").write_text("changed\n")
    fake.calls.clear()

    _reconcile_package(tmp_path, "claude")

    assert [call[2] for call in fake.writes] == ["uninstall", "install"]
    assert plugin_bridge._package_fingerprint(
        tmp_path / "cache"
    ) == plugin_bridge._package_fingerprint(package_host)


@pytest.mark.parametrize(
    ("installed_version", "enabled", "adds"),
    [("7.0.0", True, 0), ("7.0.0", False, 1), ("6.0.0", True, 1)],
)
def test_codex_package_plugin_is_added_only_when_its_version_or_state_differs(
    tmp_path, fake, package_host, installed_version, enabled, adds
):
    (tmp_path / "cache").mkdir()
    fake.add_plugin("codex", "demo@market", installed_version, enabled)

    _reconcile_package(tmp_path, "codex")

    assert len(fake.writes) == adds


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("report_path", [False, True])
def test_package_plugin_rejects_unverified_cache(
    tmp_path, fake, package_host, host, report_path
):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "payload").write_text("stale\n")
    fake.payloads.clear()  # install leaves the stale cache in place
    fake.paths["demo@market"] = cache if report_path else None
    if not report_path and host == "codex":
        fake.paths["demo@market"] = None

    with pytest.raises(BridgeError, match="run chezmoi apply again"):
        _reconcile_package(tmp_path, host)

    assert f"plugin\t{host}\tmarket\tdemo\towned" not in _records(tmp_path)


# --- external marketplaces ---


def _external(source_type: str, host: str, plugin: bool = True) -> dict[str, Any]:
    market = {"source_type": source_type, "hosts": [host]}
    if source_type != "host-provided":
        market["source_locator"] = "owner/repo"
    return _declaration(
        {"market": market},
        plugins={"demo": {"marketplace": "market"}} if plugin else {},
    )


@pytest.fixture
def external(fake, tmp_path):
    fake.sources["owner/repo"] = "market"
    fake.paths["demo@market"] = tmp_path / "catalog"
    (tmp_path / "catalog/.codex-plugin").mkdir(parents=True)
    publish(tmp_path, "1.0.0")
    fake.versions["demo@market"] = "1.0.0"
    return fake


def publish(tmp_path: Path, version: str) -> None:
    (tmp_path / "catalog/.codex-plugin/plugin.json").write_text(
        json.dumps({"name": "demo", "version": version})
    )


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("source_type", ["public", "internal", "host-provided"])
def test_manual_plugin_is_never_recorded_or_removed(
    tmp_path, external, host, source_type
):
    external.marketplaces[host]["market"] = "https://example.test/m.git"
    external.add_plugin(host, "demo@market")

    plugin_bridge.reconcile(tmp_path, _external(source_type, host))
    plugin_bridge.reconcile(tmp_path, _external(source_type, host, plugin=False))

    assert external.writes == []
    assert _records(tmp_path) == []


@pytest.mark.parametrize("host", HOSTS)
def test_public_plugin_installed_by_the_bridge_is_owned_then_removed_when_undesired(
    tmp_path, external, host
):
    plugin_bridge.reconcile(tmp_path, _external("public", host))
    assert [call[2:] for call in external.writes] == [
        ("marketplace", "add", "owner/repo"),
        ("install" if host == "claude" else "add", "demo@market"),
    ]
    assert _records(tmp_path) == [
        f"marketplace\t{host}\tmarket\t\towned",
        f"plugin\t{host}\tmarket\tdemo\towned",
    ]
    external.calls.clear()

    plugin_bridge.reconcile(tmp_path, _declaration({}))

    assert [call[2:] for call in external.writes] == [
        ("uninstall" if host == "claude" else "remove", "demo@market"),
        ("marketplace", "remove", "market"),
    ]
    assert _records(tmp_path) == []


@pytest.mark.parametrize("host", HOSTS)
def test_host_provided_plugin_is_recorded_only_when_the_bridge_installs_it(
    tmp_path, external, host
):
    external.marketplaces[host]["market"] = "https://example.test/m.git"

    plugin_bridge.reconcile(tmp_path, _external("host-provided", host))

    assert _records(tmp_path) == [f"plugin\t{host}\tmarket\tdemo\towned"]
    assert not any(call[2] == "marketplace" for call in external.writes)


@pytest.mark.parametrize("host", HOSTS)
def test_missing_host_provided_marketplace_skips_only_its_plugins(
    tmp_path, external, host
):
    declaration = _declaration(
        {
            "wrapper": {"source_type": "host-provided", "hosts": [host]},
            "market": {
                "source_type": "public",
                "source_locator": "owner/repo",
                "hosts": [host],
            },
        },
        plugins={
            "wrapped": {"marketplace": "wrapper"},
            "demo": {"marketplace": "market"},
        },
    )
    plugin_bridge.reconcile(tmp_path, declaration)
    assert list(external.plugins[host]) == ["demo@market"]
    assert _records(tmp_path) == [
        f"marketplace\t{host}\tmarket\t\towned",
        f"plugin\t{host}\tmarket\tdemo\towned",
    ]


def test_disabled_host_provided_codex_plugin_is_not_re_enabled(
    tmp_path, external, caplog
):
    external.marketplaces["codex"]["market"] = "https://example.test/m.git"
    external.add_plugin("codex", "demo@market", enabled=False)
    caplog.set_level("INFO")

    plugin_bridge.reconcile(tmp_path, _external("host-provided", "codex"))

    assert external.writes == []
    assert "skip re-enable" in caplog.text
    assert _records(tmp_path) == []


@pytest.mark.parametrize("host", HOSTS)
def test_disabled_public_plugin_is_enabled(tmp_path, external, host):
    external.marketplaces[host]["market"] = "https://example.test/m.git"
    external.add_plugin(host, "demo@market", enabled=False)
    plugin_bridge.reconcile(tmp_path, _external("public", host))
    assert [call[2] for call in external.writes] == [
        "enable" if host == "claude" else "add"
    ]


def _owned(host: str) -> list[str]:
    return [
        f"marketplace\t{host}\tmarket\t\towned",
        f"plugin\t{host}\tmarket\tdemo\towned",
    ]


@pytest.mark.parametrize("host", HOSTS)
def test_refresh_updates_an_owned_marketplace_and_its_plugins(tmp_path, external, host):
    external.marketplaces[host]["market"] = "https://example.test/m.git"
    external.add_plugin(host, "demo@market", "1.0.0")
    _write_records(tmp_path, *_owned(host))
    external.versions["demo@market"] = "2.0.0"
    external.on_refresh = lambda: publish(tmp_path, "2.0.0")

    plugin_bridge.reconcile(tmp_path, _external("public", host), refresh=True)

    refresh = "update" if host == "claude" else "upgrade"
    reinstall = ["update"] if host == "claude" else ["remove", "add"]
    assert [
        call[2:] if call[2] != "marketplace" else call[3:] for call in external.writes
    ] == [
        (refresh, "market"),
        *[(verb, "demo@market") for verb in reinstall],
    ]


@pytest.mark.parametrize("host", HOSTS)
def test_apply_without_refresh_leaves_a_present_marketplace_alone(
    tmp_path, external, host
):
    external.marketplaces[host]["market"] = "https://example.test/m.git"
    external.add_plugin(host, "demo@market")
    _write_records(tmp_path, *_owned(host))
    plugin_bridge.reconcile(tmp_path, _external("public", host))
    assert external.writes == []


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("source_type", ["public", "host-provided"])
def test_refresh_never_touches_adopted_or_host_provided_catalogs(
    tmp_path, external, host, source_type
):
    external.marketplaces[host]["market"] = "https://example.test/m.git"
    external.add_plugin(host, "demo@market")
    plugin_bridge.reconcile(tmp_path, _external(source_type, host), refresh=True)
    assert external.writes == []


# --- ownership ---


def test_owned_undesired_records_are_removed_plugins_first_and_others_kept(
    tmp_path, fake
):
    for plugin_id in ("old@market", "manual@market", "amb@market"):
        fake.add_plugin("claude", plugin_id)
    fake.marketplaces["claude"]["market"] = "owner/repo"
    _write_records(
        tmp_path,
        "marketplace\tclaude\tmarket\t\towned",
        "plugin\tclaude\tmarket\told\towned",
        "plugin\tclaude\tmarket\tamb\tambiguous",
    )

    plugin_bridge.reconcile(tmp_path, _declaration({}))

    assert [call[2:] for call in fake.writes] == [
        ("uninstall", "old@market"),
        ("marketplace", "remove", "market"),
    ]
    assert _records(tmp_path) == ["plugin\tclaude\tmarket\tamb\tambiguous"]


def test_owned_record_for_an_absent_codex_plugin_is_removed_once_then_dropped(
    tmp_path, fake
):
    _write_records(tmp_path, "plugin\tcodex\tmarket\tgone\towned")
    fake.fail.add(("plugin", "remove", "gone@market"))  # not installed
    plugin_bridge.reconcile(tmp_path, _declaration({}))
    assert fake.writes == [("codex", "plugin", "remove", "gone@market")]
    assert _records(tmp_path) == []
    fake.calls.clear()
    plugin_bridge.reconcile(tmp_path, _declaration({}))
    assert fake.writes == []


def test_removal_requires_verified_absence(tmp_path, fake):
    fake.add_plugin("claude", "old@market")
    fake.sticky = True
    _write_records(tmp_path, "plugin\tclaude\tmarket\told\towned")

    with pytest.raises(BridgeError, match="did not disappear"):
        plugin_bridge.reconcile(tmp_path, _declaration({}))

    assert _records(tmp_path) == ["plugin\tclaude\tmarket\told\towned"]


def test_successful_registration_is_checkpointed_before_a_later_failure(tmp_path, fake):
    _deploy(tmp_path, fake, "first", "1")
    _deploy(tmp_path, fake, "second", "1")
    fake.fail.add(("plugin", "install", "second@market"))
    declaration = _declaration(
        {"market": _generated("claude")},
        plugins={
            "first": {"marketplace": "market", "order": 1},
            "second": {"marketplace": "market", "order": 2},
        },
    )

    with pytest.raises(BridgeError, match="failed"):
        plugin_bridge.reconcile(tmp_path, declaration)

    assert "plugin\tclaude\tmarket\tfirst\towned" in _records(tmp_path)


@pytest.mark.parametrize(
    "record",
    [
        "plugin\tclaude\tonly-three",
        "plugin\tclaude\tmarket\tdemo",
        "plugin\tclaude\tmarket\tdemo\tunknown",
    ],
)
def test_malformed_ownership_is_an_error(tmp_path, record):
    _write_records(tmp_path, record)
    with pytest.raises(BridgeError, match="invalid ownership record"):
        plugin_bridge.reconcile(tmp_path, _declaration({}))


# --- command line ---


@pytest.mark.parametrize(
    ("declaration", "expected_code"), [({}, 0), ({"environment": "bad/name"}, 2)]
)
def test_reconcile_standalone_without_site_packages(
    tmp_path, declaration, expected_code
):
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            str(plugin_bridge.__file__),
            "reconcile",
            "--destination",
            str(tmp_path),
        ],
        input=json.dumps(declaration),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == expected_code, result.stderr
    assert ("invalid environment name" in result.stderr) == bool(expected_code)


def test_main_refreshes_only_on_explicit_flags(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        plugin_bridge,
        "reconcile",
        lambda destination, declaration, *, refresh=False: calls.append(refresh),
    )
    stamp = tmp_path / ".local/state/dotfiles/agent-plugin-refresh"

    def run(env_args="chezmoi apply", extra=()):
        monkeypatch.setenv("CHEZMOI_ARGS", env_args)
        monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
        assert (
            plugin_bridge.main(["reconcile", "--destination", str(tmp_path), *extra])
            == 0
        )
        return calls[-1]

    assert run() is False
    assert not stamp.exists()
    assert run(extra=["--refresh"]) is True
    assert run("chezmoi apply -R") is True
    assert run("chezmoi --config c apply --refresh-externals --no-tty") is True
    assert run("chezmoi apply --refresh-externals=never") is False
    assert not stamp.exists()
    stamp.parent.mkdir(parents=True)
    stamp.touch()
    plugin_bridge.os.utime(stamp, (0, 0))
    assert run() is False
    assert stamp.stat().st_mtime == 0


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        ("chezmoi apply", False),
        ("chezmoi apply -R", True),
        ("chezmoi apply -vR", True),
        ("chezmoi apply -R=auto", False),
        ("chezmoi apply --refresh-externals=always", True),
        ("chezmoi apply -- -R", False),
        ("", False),
    ],
)
def test_refresh_requested_parses_chezmoi_arguments(arguments, expected):
    assert plugin_bridge._refresh_requested(arguments) is expected


# --- antigravity ---


class _FakeAgy:
    """Fake ``agy`` CLI: ``_cli_host_command`` answers from a mutable installed list."""

    def __init__(
        self, installed, *, list_output=None, probe_status=0, install_status=0
    ):
        self.installed = dict(installed)  # name -> version
        self.list_output = list_output
        self.probe_status = probe_status
        self.install_status = install_status
        self.commands = []

    def __call__(self, command):
        self.commands.append(command)
        if self.probe_status is None:
            return None
        if command[-1] == "--help":
            return self.probe_status, ""
        if command[2] == "list":
            if self.list_output is not None:
                return 0, self.list_output
            plugins = [{"name": n, "version": v} for n, v in self.installed.items()]
            return 0, json.dumps({"plugins": plugins})
        if command[2] == "install":
            if self.install_status == 0:
                directory = Path(command[3])
                manifest_path = directory / "plugin.json"
                if not manifest_path.exists():
                    manifest_path = directory / ".antigravity-plugin/plugin.json"
                manifest = json.loads(manifest_path.read_text())
                self.installed[manifest["name"]] = manifest.get("version")
            return self.install_status, ""
        if command[2] == "uninstall":
            self.installed.pop(command[3], None)
            return 0, ""
        raise AssertionError(command)

    def mutations(self):
        return [c for c in self.commands if c[2] in {"install", "uninstall"}]


def _agy_setup(tmp_path, monkeypatch, fake_agy, plugins):
    """Generate plugin dirs (name -> version) and reconcile with agy as the only CLI host."""
    marketplace = tmp_path / "m"
    for name, version in plugins.items():
        (marketplace / "plugins" / name).mkdir(parents=True, exist_ok=True)
        (marketplace / "plugins" / name / "plugin.json").write_text(
            json.dumps({"name": name, "version": version})
        )
    (marketplace / "plugins" / "no-manifest").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(plugin_bridge, "_cli_host_command", fake_agy)

    def reconcile():
        plugin_bridge.reconcile(
            tmp_path,
            _declaration(
                {
                    "dotfiles": {
                        "source_type": "generated",
                        "source_locator": str(marketplace),
                        "hosts": ["antigravity"],
                    },
                    "other": {
                        "source_type": "public",
                        "source_locator": "owner/repo",
                        "hosts": ["antigravity"],
                    },
                },
                cli_hosts=["antigravity"],
            ),
        )

    return marketplace, reconcile


def _agy_record(name):
    return f"plugin\tantigravity\tdotfiles\t{name}\towned"


def test_agy_installs_missing_plugins_records_ownership_and_settles(
    tmp_path, monkeypatch
):
    agy = _FakeAgy({})
    marketplace, reconcile = _agy_setup(
        tmp_path, monkeypatch, agy, {"a": "1", "b": "1"}
    )
    nested = marketplace / "plugins" / "upstream" / ".antigravity-plugin"
    nested.mkdir(parents=True)
    (nested / "plugin.json").write_text(
        json.dumps({"name": "upstream", "version": "7"})
    )

    reconcile()

    assert agy.mutations() == [
        ("agy", "plugin", "install", str(marketplace / "plugins" / name))
        for name in ("a", "b", "upstream")
    ]
    assert _records(tmp_path) == [_agy_record(n) for n in ("a", "b", "upstream")]
    reconcile()
    assert len(agy.mutations()) == 3


def test_agy_reinstalls_when_the_listed_version_differs(tmp_path, monkeypatch):
    agy = _FakeAgy({"a": "1"})
    marketplace, reconcile = _agy_setup(tmp_path, monkeypatch, agy, {"a": "2"})
    reconcile()
    assert agy.mutations() == [
        ("agy", "plugin", "uninstall", "a"),
        ("agy", "plugin", "install", str(marketplace / "plugins" / "a")),
    ]
    assert agy.installed == {"a": "2"}


def test_agy_uninstalls_owned_undesired_plugins_only(tmp_path, monkeypatch):
    agy = _FakeAgy({"gone": "1", "manual": "1", "keep": "1"})
    _, reconcile = _agy_setup(tmp_path, monkeypatch, agy, {"keep": "1"})
    _write_records(tmp_path, _agy_record("gone"), _agy_record("keep"))
    reconcile()
    assert agy.mutations() == [("agy", "plugin", "uninstall", "gone")]
    assert agy.installed == {"manual": "1", "keep": "1"}
    assert _records(tmp_path) == [_agy_record("keep")]


def test_agy_keeps_the_record_when_uninstall_is_not_confirmed(tmp_path, monkeypatch):
    agy = _FakeAgy({"gone": "1"})
    original = agy.__call__

    def failing(command):
        if command[2] == "uninstall":
            return 1, ""
        return original(command)

    _, reconcile = _agy_setup(tmp_path, monkeypatch, failing, {})
    _write_records(tmp_path, _agy_record("gone"))
    reconcile()
    assert _records(tmp_path) == [_agy_record("gone")]


@pytest.mark.parametrize("output", ["not json", '{"unknown": 1}', '[{"id": "x"}]', "3"])
def test_agy_skips_everything_when_the_list_is_unparseable(
    tmp_path, monkeypatch, output
):
    agy = _FakeAgy({"gone": "1"}, list_output=output)
    _, reconcile = _agy_setup(tmp_path, monkeypatch, agy, {"a": "1"})
    _write_records(tmp_path, _agy_record("gone"))
    reconcile()
    assert agy.mutations() == []
    assert _records(tmp_path) == [_agy_record("gone")]


@pytest.mark.parametrize("probe_status", [None, 1])
def test_agy_does_nothing_when_the_cli_is_unusable(
    tmp_path, monkeypatch, caplog, probe_status
):
    agy = _FakeAgy({}, probe_status=probe_status)
    _, reconcile = _agy_setup(tmp_path, monkeypatch, agy, {"a": "1"})
    caplog.set_level("INFO")
    reconcile()
    assert agy.mutations() == []
    assert "host=antigravity event=unavailable reason=no-plugin-cli" in caplog.text


def test_agy_failed_install_is_logged_and_not_recorded(tmp_path, monkeypatch, caplog):
    agy = _FakeAgy({}, install_status=3)
    _, reconcile = _agy_setup(tmp_path, monkeypatch, agy, {"a": "1"})
    caplog.set_level("INFO")
    reconcile()
    assert "host=antigravity plugin=a operation=plugin-install status=3" in caplog.text
    assert _agy_record("a") not in _records(tmp_path)


def test_cli_hosts_reject_unknown_hosts(tmp_path):
    with pytest.raises(BridgeError, match="cli_hosts"):
        plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {"cli_hosts": ["cursor"]}})
