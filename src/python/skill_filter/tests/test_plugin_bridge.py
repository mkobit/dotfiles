from __future__ import annotations

import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from skill_filter import plugin_bridge


def _valid_bridge() -> dict[str, object]:
    return {
        "plugin_bridge": {
            "environment": "local",
            "marketplaces": {
                "market": {
                    "source_type": "generated",
                    "hosts": ["claude", "codex", "cursor"],
                    "order": 100,
                }
            },
            "plugins": {
                "plugin": {
                    "marketplace": "market",
                    "hosts": ["claude", "codex", "cursor"],
                    "environments": ["local"],
                    "order": 200,
                }
            },
            "capabilities": {
                "capability": {
                    "marketplace": "market",
                    "hosts": ["claude", "codex", "cursor"],
                    "environments": ["local"],
                    "order": 300,
                }
            },
        }
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda bridge: bridge["marketplaces"].update({"bad/name": {}}),
            "marketplace name",
        ),
        (lambda bridge: bridge["plugins"].update({"bad/name": {}}), "plugin name"),
        (
            lambda bridge: bridge["capabilities"].update({"bad/name": {}}),
            "capability name",
        ),
        (
            lambda bridge: bridge["plugins"]["plugin"].update(
                {"marketplace": "missing"}
            ),
            "marketplace",
        ),
        (
            lambda bridge: bridge["capabilities"]["capability"].update(
                {"marketplace": "missing"}
            ),
            "marketplace",
        ),
        (
            lambda bridge: bridge["marketplaces"]["market"].update(
                {"hosts": ["cursorx"]}
            ),
            "host",
        ),
        (
            lambda bridge: bridge["plugins"]["plugin"].update({"hosts": ["cursorx"]}),
            "host",
        ),
        (
            lambda bridge: bridge["capabilities"]["capability"].update(
                {"hosts": ["cursorx"]}
            ),
            "host",
        ),
        (
            lambda bridge: bridge["marketplaces"]["market"].update(
                {"source_type": "unknown"}
            ),
            "source type",
        ),
        (
            lambda bridge: bridge["marketplaces"]["market"].update(
                {"source_type": "public"}
            ),
            "source locator",
        ),
        (lambda bridge: bridge["plugins"]["plugin"].update({"order": "200"}), "order"),
        (
            lambda bridge: bridge["plugins"]["plugin"].update(
                {"environments": ["bad environment"]}
            ),
            "environment",
        ),
        (
            lambda bridge: bridge["capabilities"]["capability"].update(
                {"package_path": "../outside"}
            ),
            "package_path",
        ),
        (
            lambda bridge: bridge["capabilities"]["capability"].update(
                {"package_path": "/absolute"}
            ),
            "package_path",
        ),
        (
            lambda bridge: bridge["capabilities"]["capability"].update(
                {"package_path": True}
            ),
            "package_path",
        ),
    ],
)
def test_reconcile_validates_all_declarations_before_side_effects(
    tmp_path, monkeypatch, mutation, message
):
    declaration = _valid_bridge()
    bridge = declaration["plugin_bridge"]
    assert isinstance(bridge, dict)
    mutation(bridge)
    monkeypatch.setattr(
        plugin_bridge,
        "_run",
        lambda *args: pytest.fail(f"unexpected host operation: {args}"),
    )

    with pytest.raises(plugin_bridge.BridgeError, match=message):
        plugin_bridge.reconcile(tmp_path, declaration)

    assert not (tmp_path / ".local").exists()


def test_reconcile_orders_native_registrations_and_filters_environment(
    tmp_path, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        plugin_bridge, "_repair_missing_codex_marketplaces", lambda _: None
    )
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_marketplace",
        lambda host, name, *args: calls.append(("marketplace", name, host)),
    )
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_plugin",
        lambda host, marketplace, name, *args, **kwargs: calls.append(
            ("plugin", name, host)
        ),
    )
    plugin_bridge.reconcile(
        tmp_path,
        {
            "plugin_bridge": {
                "environment": "remote",
                "marketplaces": {
                    "z": {
                        "source_type": "generated",
                        "hosts": ["cursor", "codex"],
                        "order": 10,
                    },
                    "a": {
                        "source_type": "generated",
                        "hosts": ["claude"],
                        "order": 10,
                    },
                },
                "capabilities": {
                    "z-cap": {
                        "marketplace": "a",
                        "hosts": ["claude"],
                        "order": 20,
                    }
                },
                "plugins": {
                    "skip": {
                        "marketplace": "a",
                        "hosts": ["claude"],
                        "environments": ["local"],
                    },
                    "active": {
                        "marketplace": "z",
                        "hosts": ["codex"],
                        "environments": ["remote"],
                    },
                },
            }
        },
    )
    assert calls == [
        ("marketplace", "a", "claude"),
        ("marketplace", "z", "codex"),
        ("plugin", "z-cap", "claude"),
        ("plugin", "active", "codex"),
    ]


def _marketplace_cli(host, source, *, missing_manifest=False, failure=None):
    state = {"source": source, "mutations": []}

    def run(command, *args):
        assert command == host
        if args[:3] == ("plugin", "marketplace", "list"):
            registered = state["source"]
            if registered is None:
                return '{"marketplaces": []}' if host == "codex" else "[]"
            if host == "codex" and missing_manifest and registered == source:
                raise plugin_bridge.BridgeError(
                    "codex plugin marketplace list --json failed: "
                    "Error: failed to load marketplace(s):\n"
                    f"- `market` at {registered}: marketplace root does not contain a supported manifest"
                )
            if host == "claude":
                return json.dumps(
                    [
                        {
                            "name": "market",
                            "source": "directory",
                            "path": registered,
                            "installLocation": registered,
                        }
                    ]
                )
            if args[-1] != "--json":
                return f"market  {registered}\n"
            return json.dumps(
                {
                    "marketplaces": [
                        {
                            "name": "market",
                            "root": registered,
                            "marketplaceSource": {
                                "sourceType": "local",
                                "source": registered,
                            },
                        }
                    ]
                }
            )
        state["mutations"].append(args)
        if args == ("plugin", "marketplace", "remove", "market"):
            state["source"] = None
        elif args[:3] == ("plugin", "marketplace", "add"):
            if failure == "add":
                raise plugin_bridge.BridgeError("marketplace add failed")
            state["source"] = source if failure == "wrong-source" else args[3]
        else:
            pytest.fail(f"unexpected host operation: {args}")
        return ""

    return state, run


def _generated_declaration(host):
    return {
        "plugin_bridge": {
            "marketplaces": {"market": {"source_type": "generated", "hosts": [host]}},
            "plugins": {"demo": {"marketplace": "market", "hosts": [host]}},
        }
    }


@pytest.mark.parametrize(
    ("host", "missing_manifest"),
    [("claude", False), ("codex", False), ("codex", True)],
)
def test_generated_marketplace_repairs_source_before_plugins_and_stays_current(
    tmp_path, monkeypatch, host, missing_manifest
):
    expected = str(tmp_path / ".local/share/agent-plugins/marketplace")
    stale = str(tmp_path / "removed-checkout/marketplace")
    state, run = _marketplace_cli(host, stale, missing_manifest=missing_manifest)
    monkeypatch.setattr(plugin_bridge, "_run", run)
    plugins = []

    def ensure_plugin(*args, **kwargs):
        assert state["source"] == expected
        plugins.append(args[2])

    monkeypatch.setattr(plugin_bridge, "_ensure_plugin", ensure_plugin)
    for _ in range(2):
        plugin_bridge.reconcile(tmp_path, _generated_declaration(host))

    assert state["source"] == expected
    assert state["mutations"] == [
        ("plugin", "marketplace", "remove", "market"),
        ("plugin", "marketplace", "add", expected),
    ]
    assert plugins == ["demo", "demo"]
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    assert ownership.read_text() == f"marketplace\t{host}\tmarket\t\n"


@pytest.mark.parametrize("stale_names", [("a", "b"), ("b",)])
def test_generated_codex_marketplaces_repair_all_missing_roots_before_plugins(
    tmp_path, monkeypatch, stale_names
):
    expected = {name: str(tmp_path / "deployed" / name) for name in ("a", "b")}
    stale = {name: str(tmp_path / "removed" / name) for name in expected}
    registered = {
        name: stale[name] if name in stale_names else path
        for name, path in expected.items()
    }
    mutations = []
    verified = set()
    plugins = []

    def run(host, *args):
        assert host == "codex"
        if args == ("plugin", "marketplace", "list", "--json"):
            missing = {
                name: path for name, path in registered.items() if path == stale[name]
            }
            if missing:
                raise plugin_bridge.BridgeError(
                    "Error: failed to load marketplace(s):\n"
                    + "\n".join(
                        f"- `{name}` at {path}: marketplace root does not contain a supported manifest"
                        for name, path in missing.items()
                    )
                )
            assert registered == expected
            verified.update(registered)
            return json.dumps(
                {
                    "marketplaces": [
                        {
                            "name": name,
                            "marketplaceSource": {
                                "sourceType": "local",
                                "source": path,
                            },
                        }
                        for name, path in registered.items()
                    ]
                }
            )
        mutations.append(args)
        if args[:3] == ("plugin", "marketplace", "remove"):
            del registered[args[3]]
        elif args[:3] == ("plugin", "marketplace", "add"):
            name = next(name for name, path in expected.items() if path == args[3])
            registered[name] = args[3]
        else:
            pytest.fail(f"unexpected host operation: {args}")
        return ""

    def ensure_plugin(host, marketplace, name, *args, **kwargs):
        assert registered == expected
        assert verified == set(expected)
        plugins.append((marketplace, name))

    monkeypatch.setattr(plugin_bridge, "_run", run)
    monkeypatch.setattr(plugin_bridge, "_ensure_plugin", ensure_plugin)
    declaration = {
        "plugin_bridge": {
            "marketplaces": {
                name: {
                    "source_type": "generated",
                    "hosts": ["codex"],
                    "source_locator": path,
                }
                for name, path in expected.items()
            },
            "plugins": {
                f"demo-{name}": {"marketplace": name, "hosts": ["codex"]}
                for name in expected
            },
        }
    }

    for _ in range(2):
        verified.clear()
        plugin_bridge.reconcile(tmp_path, declaration)

    assert registered == expected
    assert mutations == [
        mutation
        for name in stale_names
        for mutation in (
            ("plugin", "marketplace", "remove", name),
            ("plugin", "marketplace", "add", expected[name]),
        )
    ]
    assert plugins == [("a", "demo-a"), ("b", "demo-b")] * 2
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    assert ownership.read_text() == (
        "marketplace\tcodex\ta\t\nmarketplace\tcodex\tb\t\n"
    )


@pytest.mark.parametrize(
    ("host", "missing_manifest"),
    [("claude", False), ("codex", False), ("codex", True)],
)
@pytest.mark.parametrize("failure", ["add", "wrong-source"])
def test_generated_marketplace_failed_repair_stops_before_plugins(
    tmp_path, monkeypatch, host, missing_manifest, failure
):
    state, run = _marketplace_cli(
        host,
        str(tmp_path / "old"),
        missing_manifest=missing_manifest,
        failure=failure,
    )
    monkeypatch.setattr(plugin_bridge, "_run", run)
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_plugin",
        lambda *args, **kwargs: pytest.fail("plugin ran before source verification"),
    )

    with pytest.raises(plugin_bridge.BridgeError):
        plugin_bridge.reconcile(tmp_path, _generated_declaration(host))

    assert state["source"] != str(tmp_path / ".local/share/agent-plugins/marketplace")
    assert not (tmp_path / ".local/state/dotfiles/agent-plugin-ownership").exists()


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("present", [False, True])
def test_generated_marketplace_preserves_matching_and_missing_sources(
    tmp_path, monkeypatch, host, present
):
    expected = str(tmp_path / ".local/share/agent-plugins/marketplace")
    state, run = _marketplace_cli(host, expected if present else None)
    monkeypatch.setattr(plugin_bridge, "_run", run)
    declaration = _generated_declaration(host)
    declaration["plugin_bridge"]["plugins"].clear()

    plugin_bridge.reconcile(tmp_path, declaration)

    assert state["source"] == expected
    assert state["mutations"] == (
        [] if present else [("plugin", "marketplace", "add", expected)]
    )


@pytest.mark.parametrize(
    "detail",
    [
        "configuration is invalid",
        "Error: failed to load marketplace(s):\n- `other` at /removed: marketplace root does not contain a supported manifest",
    ],
)
def test_generated_codex_marketplace_does_not_repair_unrelated_cli_errors(
    tmp_path, monkeypatch, detail
):
    calls = []

    def run(host, *args):
        calls.append(args)
        raise plugin_bridge.BridgeError(detail)

    monkeypatch.setattr(plugin_bridge, "_run", run)
    with pytest.raises(plugin_bridge.BridgeError, match="invalid|other"):
        plugin_bridge.reconcile(tmp_path, _generated_declaration("codex"))

    assert len(calls) == 1


@pytest.mark.parametrize(
    ("host", "response"),
    [("claude", '{"unknown": []}'), ("codex", '{"unknown": []}'), ("codex", "[]")],
)
def test_generated_marketplace_rejects_unknown_list_schema(
    tmp_path, monkeypatch, host, response
):
    calls = []

    def run(command, *args):
        calls.append(args)
        return response

    monkeypatch.setattr(plugin_bridge, "_run", run)
    with pytest.raises(plugin_bridge.BridgeError, match="marketplace JSON"):
        plugin_bridge.reconcile(tmp_path, _generated_declaration(host))

    assert calls == [("plugin", "marketplace", "list", "--json")]


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_repaired_generated_marketplace_restores_declared_plugin(
    tmp_path, monkeypatch, host
):
    expected = tmp_path / ".local/share/agent-plugins/marketplace"
    catalog = expected / ".claude-plugin/marketplace.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        json.dumps({"plugins": [{"name": "demo", "source": "plugins/demo"}]})
    )
    source = expected / "plugins/demo"
    manifest = source / f".{host}-plugin/plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"name": "demo", "version": "1.0.0"}')
    state, marketplace_run = _marketplace_cli(host, str(tmp_path / "removed-source"))
    installed = True

    def run(command, *args):
        nonlocal installed
        if args[:2] == ("plugin", "marketplace"):
            result = marketplace_run(command, *args)
            if args[2] == "remove":
                installed = False
            return result
        if args == ("plugin", "list", "--json"):
            return json.dumps(
                [{"id": "demo@market", "version": "1.0.0", "enabled": True}]
                if installed
                else []
            )
        if args == ("plugin", "list", "-m", "market", "--json"):
            return json.dumps(
                {
                    "installed": [
                        {
                            "pluginId": "demo@market",
                            "version": "1.0.0",
                            "installed": True,
                            "enabled": True,
                            "source": {"source": "local", "path": str(source)},
                        }
                    ]
                    if installed
                    else []
                }
            )
        if args in {
            ("plugin", "install", "demo@market"),
            ("plugin", "add", "demo@market"),
        }:
            assert state["source"] == str(expected)
            installed = True
            return ""
        pytest.fail(f"unexpected plugin operation: {args}")

    monkeypatch.setattr(plugin_bridge, "_run", run)
    plugin_bridge.reconcile(tmp_path, _generated_declaration(host))

    assert installed
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    assert (
        ownership.read_text()
        == f"marketplace\t{host}\tmarket\t\nplugin\t{host}\tmarket\tdemo\n"
    )


@pytest.mark.parametrize("kind", ["plugins", "capabilities"])
def test_reconcile_rejects_resource_host_outside_marketplace_before_side_effects(
    tmp_path, monkeypatch, kind
):
    declaration = _valid_bridge()
    bridge = declaration["plugin_bridge"]
    assert isinstance(bridge, dict)
    marketplace = bridge["marketplaces"]["market"]
    assert isinstance(marketplace, dict)
    marketplace["hosts"] = ["claude"]
    resource = bridge[kind]["plugin" if kind == "plugins" else "capability"]
    assert isinstance(resource, dict)
    resource["hosts"] = ["codex"]
    monkeypatch.setattr(
        plugin_bridge,
        "_run",
        lambda *args: pytest.fail(f"unexpected host operation: {args}"),
    )

    with pytest.raises(plugin_bridge.BridgeError, match="marketplace hosts"):
        plugin_bridge.reconcile(tmp_path, declaration)

    assert not (tmp_path / ".local").exists()


def test_reconcile_allows_cursor_capability_with_native_marketplace_hosts(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        plugin_bridge, "_repair_missing_codex_marketplaces", lambda _: None
    )
    declaration = _valid_bridge()
    bridge = declaration["plugin_bridge"]
    assert isinstance(bridge, dict)
    marketplaces = bridge["marketplaces"]
    capabilities = bridge["capabilities"]
    plugins = bridge["plugins"]
    assert isinstance(marketplaces, dict)
    assert isinstance(capabilities, dict)
    assert isinstance(plugins, dict)
    marketplaces["market"]["hosts"] = ["claude", "codex"]
    capabilities["capability"]["hosts"] = ["claude", "codex", "cursor"]
    plugins.clear()
    calls = []
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_marketplace",
        lambda host, name, *args: calls.append(("marketplace", host, name)),
    )
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_plugin",
        lambda host, marketplace, name, *args, **kwargs: calls.append(
            ("plugin", host, marketplace, name)
        ),
    )

    plugin_bridge.reconcile(tmp_path, declaration)

    assert calls == [
        ("marketplace", "claude", "market"),
        ("marketplace", "codex", "market"),
        ("plugin", "claude", "market", "capability"),
        ("plugin", "codex", "market", "capability"),
    ]


def test_reconcile_ignores_cursor_and_filesystem_metadata(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        plugin_bridge, "_repair_missing_codex_marketplaces", lambda _: None
    )
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_marketplace",
        lambda host, *args: calls.append(("marketplace", host)),
    )
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_plugin",
        lambda host, *args, **kwargs: calls.append(("plugin", host)),
    )
    plugin_bridge.reconcile(
        tmp_path,
        {
            "plugin_bridge": {
                "marketplaces": {
                    "market": {
                        "source_type": "generated",
                        "hosts": ["claude", "codex", "cursor"],
                        "package_cleanup": {"unsafe": "ignored"},
                    }
                },
                "capabilities": {
                    "demo": {
                        "marketplace": "market",
                        "hosts": ["claude", "codex", "cursor"],
                    }
                },
                "generated_marketplace_root": "../ignored",
            },
            "skills": {"ignored": True},
            "source_dir": "../ignored",
            "working_tree": "../ignored",
        },
    )
    assert calls == [
        ("marketplace", "claude"),
        ("marketplace", "codex"),
        ("plugin", "claude"),
        ("plugin", "codex"),
    ]
    assert not (tmp_path / ".cursor").exists()


def test_reconcile_removes_plugins_before_marketplaces(tmp_path, monkeypatch):
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    ownership.write_text(
        "marketplace\tcodex\tz-market\t\nplugin\tcodex\tb-market\tz-plugin\nmarketplace\tclaude\ta-market\t\nplugin\tclaude\ta-market\ta-plugin\n"
    )
    calls = []
    installed_plugins = {"a-plugin@a-market", "z-plugin@b-market"}
    installed_marketplaces = {"a-market", "z-market"}

    def run(host, *args):
        calls.append((host, *args))
        if args == ("plugin", "list", "--json"):
            return json.dumps(
                [
                    {"id": plugin, "enabled": True}
                    for plugin in sorted(installed_plugins)
                ]
            )
        if args == ("plugin", "list", "-m", "b-market"):
            return (
                "z-plugin@b-market  installed, enabled  1.0.0  /fixture/z-plugin\n"
                if "z-plugin@b-market" in installed_plugins
                else ""
            )
        if args == ("plugin", "marketplace", "list", "--json"):
            return json.dumps(
                [
                    {"name": marketplace}
                    for marketplace in sorted(installed_marketplaces)
                ]
            )
        if args == ("plugin", "marketplace", "list"):
            return "\n".join(
                f"{marketplace}  /fixture/{marketplace}"
                for marketplace in sorted(installed_marketplaces)
            )
        if args == ("plugin", "uninstall", "a-plugin@a-market"):
            installed_plugins.remove("a-plugin@a-market")
        elif args == ("plugin", "remove", "z-plugin@b-market"):
            installed_plugins.remove("z-plugin@b-market")
        elif args == ("plugin", "marketplace", "remove", "a-market"):
            installed_marketplaces.remove("a-market")
        elif args == ("plugin", "marketplace", "remove", "z-market"):
            installed_marketplaces.remove("z-market")
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})
    assert calls == [
        ("claude", "plugin", "list", "--json"),
        ("claude", "plugin", "uninstall", "a-plugin@a-market"),
        ("claude", "plugin", "list", "--json"),
        ("codex", "plugin", "list", "-m", "b-market"),
        ("codex", "plugin", "remove", "z-plugin@b-market"),
        ("codex", "plugin", "list", "-m", "b-market"),
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("claude", "plugin", "marketplace", "remove", "a-market"),
        ("claude", "plugin", "marketplace", "list", "--json"),
        ("codex", "plugin", "marketplace", "list"),
        ("codex", "plugin", "marketplace", "remove", "z-market"),
        ("codex", "plugin", "marketplace", "list"),
    ]


def test_successful_removal_is_checkpointed_before_later_failure(tmp_path, monkeypatch):
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    ownership.write_text(
        "plugin\tclaude\tmarket\ta-plugin\nplugin\tclaude\tmarket\tb-plugin\n",
        encoding="utf-8",
    )
    installed = {"a-plugin@market", "b-plugin@market"}
    fail_once = True

    def run(host, *args):
        nonlocal fail_once
        if args == ("plugin", "list", "--json"):
            return json.dumps(
                [{"id": plugin, "enabled": True} for plugin in sorted(installed)]
            )
        plugin = args[-1]
        if plugin == "b-plugin@market" and fail_once:
            fail_once = False
            raise plugin_bridge.BridgeError("later failure")
        if plugin not in installed:
            raise plugin_bridge.BridgeError(f"already removed: {plugin}")
        installed.remove(plugin)
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    with pytest.raises(plugin_bridge.BridgeError, match="later failure"):
        plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert ownership.read_text(encoding="utf-8") == (
        "plugin\tclaude\tmarket\tb-plugin\n"
    )

    plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert installed == set()
    assert ownership.read_text(encoding="utf-8") == ""


def test_reconcile_discards_cursor_ownership_without_removing_files(
    tmp_path, monkeypatch
):
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    ownership.write_text("plugin\tcursor\tmarket\tdemo\n", encoding="utf-8")
    marker = tmp_path / ".cursor/plugins/local/demo/marker"
    marker.parent.mkdir(parents=True)
    marker.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(
        plugin_bridge, "_run", lambda *args: pytest.fail(f"unexpected call: {args}")
    )
    plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})
    assert marker.read_text(encoding="utf-8") == "keep"
    assert ownership.read_text(encoding="utf-8") == ""


def test_reconcile_rejects_symlinked_state_root(tmp_path):
    redirected = tmp_path / "redirected"
    redirected.mkdir()
    state = tmp_path / ".local/state/dotfiles"
    state.parent.mkdir(parents=True)
    state.symlink_to(redirected, target_is_directory=True)
    with pytest.raises(plugin_bridge.BridgeError, match="state root"):
        plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})
    assert list(redirected.iterdir()) == []


def test_successful_registration_is_checkpointed_before_later_failure(
    tmp_path, monkeypatch
):
    calls = 0

    def ensure(host, marketplace, name, ownership_file, desired, owned, **kwargs):
        nonlocal calls
        calls += 1
        record = plugin_bridge._identity("plugin", host, marketplace, name)
        desired.add(record)
        if calls == 2:
            raise plugin_bridge.BridgeError("later failure")
        owned.add(record)
        plugin_bridge._checkpoint(ownership_file, record)

    monkeypatch.setattr(plugin_bridge, "_ensure_plugin", ensure)
    monkeypatch.setattr(plugin_bridge, "_ensure_marketplace", lambda *args: None)
    with pytest.raises(plugin_bridge.BridgeError, match="later failure"):
        plugin_bridge.reconcile(
            tmp_path,
            {
                "plugin_bridge": {
                    "marketplaces": {
                        "m": {"source_type": "generated", "hosts": ["claude"]}
                    },
                    "capabilities": {
                        "a": {"marketplace": "m", "hosts": ["claude"]},
                        "b": {"marketplace": "m", "hosts": ["claude"]},
                    },
                }
            },
        )
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    assert ownership.read_text() == "plugin\tclaude\tm\ta\n"


def test_existing_claude_plugin_is_adopted_and_enabled(tmp_path, monkeypatch):
    calls = []
    enabled = False

    def run(host, *args):
        nonlocal enabled
        calls.append((host, *args))
        if args == ("plugin", "list", "--json"):
            return json.dumps([{"id": "demo@market", "enabled": enabled}])
        if args == ("plugin", "enable", "demo@market"):
            enabled = True
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    desired, owned = set(), set()
    ownership = tmp_path / "ownership"
    plugin_bridge._ensure_plugin("claude", "market", "demo", ownership, desired, owned)
    assert ("claude", "plugin", "update", "demo@market") in calls
    assert ("claude", "plugin", "enable", "demo@market") in calls
    assert owned == {"plugin\tclaude\tmarket\tdemo"}


def _claude_manifest_root(tmp_path, version):
    root = tmp_path / "marketplace"
    catalog = root / ".claude-plugin/marketplace.json"
    catalog.parent.mkdir(parents=True)
    catalog.write_text(
        json.dumps(
            {
                "name": "market",
                "plugins": [{"name": "demo", "source": "./plugins/demo/claude"}],
            }
        ),
        encoding="utf-8",
    )
    manifest = root / "plugins/demo/claude/.claude-plugin/plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"name": "demo", "version": version}), encoding="utf-8"
    )
    return root


def _claude_run(calls, version, enabled):
    def run(host, *args):
        calls.append((host, *args))
        if args == ("plugin", "list", "--json"):
            return json.dumps(
                [{"id": "demo@market", "version": version, "enabled": enabled}]
            )
        return ""

    return run


def test_current_claude_plugin_is_not_updated(tmp_path, monkeypatch):
    calls = []
    root = _claude_manifest_root(tmp_path, "1.0.0+abc")
    monkeypatch.setattr(plugin_bridge, "_run", _claude_run(calls, "1.0.0+abc", True))
    owned = set()
    plugin_bridge._ensure_plugin(
        "claude",
        "market",
        "demo",
        tmp_path / "ownership",
        set(),
        owned,
        manifest_root=root,
    )
    assert calls == [("claude", "plugin", "list", "--json")]
    assert owned == {"plugin\tclaude\tmarket\tdemo"}


def test_changed_claude_plugin_version_is_updated(tmp_path, monkeypatch):
    calls = []
    root = _claude_manifest_root(tmp_path, "1.0.0+new")
    monkeypatch.setattr(plugin_bridge, "_run", _claude_run(calls, "1.0.0+old", True))
    plugin_bridge._ensure_plugin(
        "claude",
        "market",
        "demo",
        tmp_path / "ownership",
        set(),
        set(),
        manifest_root=root,
    )
    assert ("claude", "plugin", "update", "demo@market") in calls


def test_claude_plugin_without_manifest_root_is_updated(tmp_path, monkeypatch):
    calls = []
    _claude_manifest_root(tmp_path, "1.0.0+abc")
    monkeypatch.setattr(plugin_bridge, "_run", _claude_run(calls, "1.0.0+abc", True))
    plugin_bridge._ensure_plugin(
        "claude", "market", "demo", tmp_path / "ownership", set(), set()
    )
    assert ("claude", "plugin", "update", "demo@market") in calls


def test_current_disabled_claude_plugin_is_enabled_without_update(
    tmp_path, monkeypatch
):
    calls = []
    enabled = False
    root = _claude_manifest_root(tmp_path, "1.0.0+abc")

    def run(host, *args):
        nonlocal enabled
        calls.append((host, *args))
        if args == ("plugin", "list", "--json"):
            return json.dumps(
                [{"id": "demo@market", "version": "1.0.0+abc", "enabled": enabled}]
            )
        if args == ("plugin", "enable", "demo@market"):
            enabled = True
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    plugin_bridge._ensure_plugin(
        "claude",
        "market",
        "demo",
        tmp_path / "ownership",
        set(),
        set(),
        manifest_root=root,
    )
    assert ("claude", "plugin", "enable", "demo@market") in calls
    assert ("claude", "plugin", "update", "demo@market") not in calls


def test_reconcile_passes_manifest_root_only_for_generated_marketplaces(
    tmp_path, monkeypatch
):
    roots = {}
    monkeypatch.setattr(plugin_bridge, "_ensure_marketplace", lambda *args: None)
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_plugin",
        lambda host, marketplace, name, *args, manifest_root=None: roots.update(
            {marketplace: manifest_root}
        ),
    )
    plugin_bridge.reconcile(
        tmp_path,
        {
            "plugin_bridge": {
                "marketplaces": {
                    "gen": {"source_type": "generated", "hosts": ["claude"]},
                    "up": {
                        "source_type": "public",
                        "source_locator": "owner/repo",
                        "hosts": ["claude"],
                    },
                },
                "plugins": {
                    "a": {"marketplace": "gen", "hosts": ["claude"]},
                    "b": {"marketplace": "up", "hosts": ["claude"]},
                },
            }
        },
    )
    assert roots == {
        "gen": tmp_path / ".local/share/agent-plugins/marketplace",
        "up": None,
    }


def test_existing_codex_plugin_is_not_added_again(tmp_path, monkeypatch):
    calls = []
    source = tmp_path / "marketplace/plugins/demo/codex"
    manifest = source / ".codex-plugin/plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"name": "demo", "version": "1.0.0"}), encoding="utf-8"
    )

    def run(host, *args):
        calls.append((host, *args))
        if args == ("plugin", "list", "-m", "market", "--json"):
            return json.dumps(
                {
                    "installed": [
                        {
                            "pluginId": "demo@market",
                            "installed": True,
                            "enabled": True,
                            "version": "1.0.0",
                            "source": {"source": "local", "path": str(source)},
                        }
                    ]
                }
            )
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    desired, owned = set(), set()
    plugin_bridge._ensure_plugin(
        "codex", "market", "demo", tmp_path / "ownership", desired, owned
    )

    assert ("codex", "plugin", "add", "demo@market") not in calls
    assert ("codex", "plugin", "remove", "demo@market") not in calls
    assert owned == {"plugin\tcodex\tmarket\tdemo"}


def test_stale_codex_plugin_version_is_reinstalled_from_deployed_manifest(
    tmp_path, monkeypatch
):
    source = tmp_path / "marketplace/plugins/demo/codex"
    manifest = source / ".codex-plugin/plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"name": "demo", "version": "2.0.0"}), encoding="utf-8"
    )
    installed, installed_version = True, "1.0.0"
    calls = []

    def run(host, *args):
        nonlocal installed, installed_version
        calls.append((host, *args))
        if args == ("plugin", "list", "-m", "market", "--json"):
            records = []
            if installed:
                records.append(
                    {
                        "pluginId": "demo@market",
                        "installed": True,
                        "enabled": True,
                        "version": installed_version,
                        "source": {"source": "local", "path": str(source)},
                    }
                )
            return json.dumps({"installed": records})
        if args == ("plugin", "remove", "demo@market"):
            installed = False
            installed_version = ""
        if args == ("plugin", "add", "demo@market"):
            installed = True
            installed_version = "2.0.0"
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    plugin_bridge._ensure_plugin(
        "codex", "market", "demo", tmp_path / "ownership", set(), set()
    )

    assert installed_version == "2.0.0"
    assert ("codex", "plugin", "remove", "demo@market") in calls
    assert ("codex", "plugin", "add", "demo@market") in calls


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


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_package_plugin_refreshes_same_version_content(tmp_path, monkeypatch, host):
    source, installed = tmp_path / "source", tmp_path / "cache"
    source.mkdir()
    (source / "payload").write_text("original\n", encoding="utf-8")
    manifest = source / f".{host}-plugin/plugin.json"
    manifest.parent.mkdir()
    manifest.write_text(json.dumps({"name": "demo", "version": "7.0.0"}))
    shutil.copytree(source, installed)
    (source / "payload").write_text("changed\n", encoding="utf-8")
    calls = []

    def run(command, *args):
        assert command == host
        calls.append(args)
        if args == ("plugin", "list", "--json"):
            return json.dumps(
                [
                    {
                        "id": "demo@market",
                        "version": "7.0.0",
                        "enabled": True,
                        "installPath": str(installed),
                    }
                ]
            )
        if args == ("plugin", "list", "-m", "market", "--json"):
            return json.dumps(
                {
                    "installed": [
                        {
                            "pluginId": "demo@market",
                            "version": "7.0.0",
                            "installed": True,
                            "enabled": True,
                        }
                    ]
                }
            )
        if args == ("plugin", "uninstall", "demo@market"):
            shutil.rmtree(installed)
        if args in {
            ("plugin", "install", "demo@market"),
            ("plugin", "add", "demo@market", "--json"),
        }:
            shutil.copytree(source, installed, dirs_exist_ok=True)
            return json.dumps({"installedPath": str(installed)})
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    ownership = tmp_path / "ownership"
    for _ in range(2):
        plugin_bridge._ensure_plugin(
            host, "market", "demo", ownership, set(), set(), package_root=source
        )
        assert plugin_bridge._package_fingerprint(installed) == (
            plugin_bridge._package_fingerprint(source)
        )
        assert json.loads(manifest.read_text())["version"] == "7.0.0"

    if host == "claude":
        assert calls.count(("plugin", "uninstall", "demo@market")) == 1
        assert calls.count(("plugin", "install", "demo@market")) == 1
    else:
        assert calls.count(("plugin", "add", "demo@market", "--json")) == 2


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("installed_path", [None, "stale"])
def test_package_plugin_rejects_unverified_cache(
    tmp_path, monkeypatch, host, installed_path
):
    source, installed = tmp_path / "source", tmp_path / "cache"
    source.mkdir()
    installed.mkdir()
    (source / "payload").write_text("expected\n", encoding="utf-8")
    (installed / "payload").write_text("stale\n", encoding="utf-8")

    def run(command, *args):
        if command == "claude":
            return json.dumps(
                [
                    {
                        "id": "demo@market",
                        "enabled": True,
                        **({"installPath": str(installed)} if installed_path else {}),
                    }
                ]
            )
        if args == ("plugin", "add", "demo@market", "--json"):
            return json.dumps(
                {"installedPath": str(installed)} if installed_path else {}
            )
        return json.dumps(
            {
                "installed": [
                    {"pluginId": "demo@market", "installed": True, "enabled": True}
                ]
            }
        )

    monkeypatch.setattr(plugin_bridge, "_run", run)
    ownership = tmp_path / "ownership"
    with pytest.raises(plugin_bridge.BridgeError, match="run chezmoi apply again"):
        plugin_bridge._ensure_plugin(
            host, "market", "demo", ownership, set(), set(), package_root=source
        )
    assert not ownership.exists()


def test_reconcile_passes_package_root_inside_generated_marketplace(
    tmp_path, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        plugin_bridge, "_repair_missing_codex_marketplaces", lambda _: None
    )
    declaration = _valid_bridge()
    bridge = declaration["plugin_bridge"]
    assert isinstance(bridge, dict)
    bridge["capabilities"]["capability"]["package_path"] = "./plugins/capability"
    monkeypatch.setattr(plugin_bridge, "_ensure_marketplace", lambda *args: None)
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_plugin",
        lambda host, marketplace, name, *args, **kwargs: calls.append((name, kwargs)),
    )
    plugin_bridge.reconcile(tmp_path, declaration)
    package_root = (
        tmp_path / ".local/share/agent-plugins/marketplace/plugins/capability"
    )
    capability_calls = [kwargs for name, kwargs in calls if name == "capability"]
    assert len(capability_calls) == 2
    assert all(kwargs["package_root"] == package_root for kwargs in capability_calls)
    assert all(
        "package_root" not in kwargs for name, kwargs in calls if name == "plugin"
    )


def test_package_path_requires_generated_marketplace(tmp_path, monkeypatch):
    declaration = _valid_bridge()
    bridge = declaration["plugin_bridge"]
    assert isinstance(bridge, dict)
    bridge["marketplaces"]["market"].update(
        {"source_type": "public", "source_locator": "owner/repo"}
    )
    bridge["capabilities"]["capability"]["package_path"] = "./plugins/capability"
    monkeypatch.setattr(
        plugin_bridge, "_run", lambda *args: pytest.fail("unexpected host operation")
    )
    with pytest.raises(plugin_bridge.BridgeError, match="generated marketplace"):
        plugin_bridge.reconcile(tmp_path, declaration)
    assert not (tmp_path / ".local").exists()


def test_package_path_cannot_resolve_outside_marketplace(tmp_path, monkeypatch):
    declaration = _valid_bridge()
    bridge = declaration["plugin_bridge"]
    assert isinstance(bridge, dict)
    bridge["capabilities"]["capability"]["package_path"] = "./plugins/capability"
    root = tmp_path / ".local/share/agent-plugins/marketplace/plugins"
    root.mkdir(parents=True)
    (root / "capability").symlink_to(tmp_path / "outside")
    monkeypatch.setattr(
        plugin_bridge, "_run", lambda *args: pytest.fail("unexpected host operation")
    )
    with pytest.raises(plugin_bridge.BridgeError, match="resolve inside"):
        plugin_bridge.reconcile(tmp_path, declaration)


def test_plugin_removal_requires_verified_absence(tmp_path, monkeypatch):
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    ownership.write_text("plugin\tclaude\tmarket\tdemo\n", encoding="utf-8")
    calls = []

    def run(host, *args):
        calls.append((host, *args))
        if args == ("plugin", "list", "--json"):
            return '[{"id":"demo@market","enabled":true}]'
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    with pytest.raises(plugin_bridge.BridgeError, match="did not disappear"):
        plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert ownership.read_text(encoding="utf-8") == ("plugin\tclaude\tmarket\tdemo\n")
    assert ("claude", "plugin", "uninstall", "demo@market") in calls


def test_reconcile_checkpoints_already_absent_plugin_without_removing(
    tmp_path, monkeypatch
):
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    ownership.write_text("plugin\tclaude\tmarket\tdemo\n", encoding="utf-8")
    calls = []

    def run(host, *args):
        calls.append((host, *args))
        if args == ("plugin", "list", "--json"):
            return "[]"
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert ownership.read_text(encoding="utf-8") == ""
    assert ("claude", "plugin", "uninstall", "demo@market") not in calls


def test_marketplace_removal_requires_verified_absence(tmp_path, monkeypatch):
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    ownership.write_text("marketplace\tclaude\tmarket\t\n", encoding="utf-8")
    calls = []

    def run(host, *args):
        calls.append((host, *args))
        if args == ("plugin", "marketplace", "list", "--json"):
            return '[{"name":"market"}]'
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    with pytest.raises(plugin_bridge.BridgeError, match="did not disappear"):
        plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert ownership.read_text(encoding="utf-8") == ("marketplace\tclaude\tmarket\t\n")
    assert ("claude", "plugin", "marketplace", "remove", "market") in calls


def test_claude_plugin_rejects_disabled_final_state(tmp_path, monkeypatch):
    monkeypatch.setattr(
        plugin_bridge,
        "_run",
        lambda host, *args: (
            '[{"id":"demo@market","enabled":false}]'
            if args == ("plugin", "list", "--json")
            else ""
        ),
    )
    with pytest.raises(
        plugin_bridge.BridgeError, match="did not become available and enabled"
    ):
        plugin_bridge._ensure_plugin(
            "claude", "market", "demo", tmp_path / "ownership", set(), set()
        )


def test_migrate_ownership_keeps_native_and_drops_cursor(tmp_path):
    legacy = tmp_path / "ownership.json"
    legacy.write_text(
        json.dumps(
            {
                "resources": [
                    {"kind": "plugin", "host": "claude", "id": "demo@market"},
                    {"kind": "marketplace", "host": "codex", "id": "market"},
                    {"kind": "plugin", "host": "cursor", "id": "local"},
                ]
            }
        )
    )
    assert (
        plugin_bridge.migrate_ownership(legacy)
        == "plugin\tclaude\tmarket\tdemo\nmarketplace\tcodex\tmarket\t\n"
    )


def test_reconcile_removes_legacy_ownership_after_durable_migration(tmp_path):
    state = tmp_path / ".local/state/dotfiles"
    state.mkdir(parents=True)
    legacy = state / "agent-plugin-ownership.json"
    legacy.write_text(
        json.dumps(
            {
                "resources": [
                    {"kind": "plugin", "host": "cursor", "id": "local"},
                    {"kind": "package", "host": "filesystem", "id": "generated"},
                ]
            }
        ),
        encoding="utf-8",
    )

    plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert not legacy.exists()
    assert (state / "agent-plugin-ownership").read_text(encoding="utf-8") == ""


def test_failed_legacy_migration_keeps_legacy_ownership(tmp_path, monkeypatch):
    state = tmp_path / ".local/state/dotfiles"
    state.mkdir(parents=True)
    legacy = state / "agent-plugin-ownership.json"
    legacy.write_text(
        json.dumps(
            {"resources": [{"kind": "plugin", "host": "cursor", "id": "local"}]}
        ),
        encoding="utf-8",
    )

    def fail_write(path, records):
        raise OSError("durable write failed")

    monkeypatch.setattr(plugin_bridge, "_write_ownership", fail_write)
    with pytest.raises(OSError, match="durable write failed"):
        plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert legacy.exists()
    assert not (state / "agent-plugin-ownership").exists()


def test_legacy_cleanup_recovers_after_unlink_failure(tmp_path, monkeypatch):
    state = tmp_path / ".local/state/dotfiles"
    state.mkdir(parents=True)
    legacy = state / "agent-plugin-ownership.json"
    legacy.write_text(
        json.dumps(
            {"resources": [{"kind": "plugin", "host": "cursor", "id": "local"}]}
        ),
        encoding="utf-8",
    )
    unlink = type(legacy).unlink
    fail_once = True

    def flaky_unlink(path, *args, **kwargs):
        nonlocal fail_once
        if path == legacy and fail_once:
            fail_once = False
            raise OSError("unlink failed")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(type(legacy), "unlink", flaky_unlink)
    with pytest.raises(OSError, match="unlink failed"):
        plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    ownership = state / "agent-plugin-ownership"
    assert ownership.read_text(encoding="utf-8") == ""
    assert legacy.exists()

    plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert not legacy.exists()
    assert ownership.read_text(encoding="utf-8") == ""


def test_has_identity_cli_uses_exact_json_identity():
    command = [
        sys.executable,
        "-S",
        str(plugin_bridge.__file__),
        "has-identity",
        "--field",
        "id",
        "--expected",
        "demo@market",
    ]
    present = subprocess.run(
        command,
        input='[{"id":"demo@market"}]',
        capture_output=True,
        text=True,
        check=False,
    )
    absent = subprocess.run(
        command,
        input='[{"id":"demographic@market"}]',
        capture_output=True,
        text=True,
        check=False,
    )
    assert (present.returncode, absent.returncode) == (0, 1)


def test_reconcile_skips_unavailable_host_and_preserves_previous_ownership(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(plugin_bridge.shutil, "which", lambda cmd: None)

    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    previous_content = (
        "marketplace\tclaude\tkept-market\t\n"
        "marketplace\tclaude\tstale-market\t\n"
        "plugin\tclaude\tkept-market\tkept-plugin\n"
        "plugin\tclaude\tstale-market\tstale-plugin\n"
    )
    ownership.write_text(previous_content, encoding="utf-8")

    declaration = {
        "plugin_bridge": {
            "marketplaces": {
                "kept-market": {
                    "source_type": "generated",
                    "hosts": ["claude"],
                },
                "unregistered-market": {
                    "source_type": "generated",
                    "hosts": ["claude"],
                },
            },
            "plugins": {
                "kept-plugin": {
                    "marketplace": "kept-market",
                    "hosts": ["claude"],
                },
                "unregistered-plugin": {
                    "marketplace": "kept-market",
                    "hosts": ["claude"],
                },
            },
        }
    }

    plugin_bridge.reconcile(tmp_path, declaration)

    assert ownership.read_text(encoding="utf-8") == previous_content


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
    if expected_code:
        assert "invalid environment name" in result.stderr
    else:
        assert result.stderr == ""


@pytest.mark.parametrize("returncode", [0, 7])
def test_run_reports_timing_without_exposing_arguments_or_output(
    monkeypatch, caplog, capsys, returncode
):
    caplog.set_level(logging.INFO, logger=plugin_bridge.__name__)
    monkeypatch.setattr(plugin_bridge.shutil, "which", lambda _: "/host/claude")
    monkeypatch.setattr(
        plugin_bridge.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], returncode, "private stdout", "private stderr"
        ),
    )
    ticks = iter([10.0, 12.25])
    monkeypatch.setattr(plugin_bridge.time, "monotonic", lambda: next(ticks))

    if returncode:
        with pytest.raises(plugin_bridge.BridgeError, match="private stderr"):
            plugin_bridge._run("claude", "plugin", "install", "private-plugin-id")
    else:
        assert (
            plugin_bridge._run("claude", "plugin", "install", "private-plugin-id")
            == "private stdout"
        )

    captured = capsys.readouterr()
    assert captured.out == ""
    lines = caplog.messages
    assert len(lines) == 2
    assert "event=start" in lines[0]
    assert "event=end" in lines[1]
    assert f"status={returncode}" in lines[1]
    assert "elapsed_seconds=2.250" in lines[1]
    assert all("host=claude operation=plugin-install" in line for line in lines)
    assert "private" not in caplog.text


@pytest.mark.parametrize("returncode", [0, 9])
@pytest.mark.parametrize("stderr_failure", [BrokenPipeError, ValueError])
def test_run_preserves_outcome_when_timing_output_fails(
    monkeypatch, stderr_failure, returncode
):
    class UnavailableStderr:
        def write(self, _: str) -> None:
            raise stderr_failure("unavailable")

    monkeypatch.setattr(logging.getLogger(), "handlers", [])
    monkeypatch.setattr(logging, "raiseExceptions", True)
    monkeypatch.setattr(plugin_bridge.sys, "stderr", UnavailableStderr())
    monkeypatch.setattr(plugin_bridge.sys, "stdin", io.StringIO("[]"))
    assert (
        plugin_bridge.main(["has-identity", "--field", "id", "--expected", "unused"])
        == 1
    )
    monkeypatch.setattr(plugin_bridge.shutil, "which", lambda _: "/host/codex")
    monkeypatch.setattr(
        plugin_bridge.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], returncode, "result", "failure"
        ),
    )
    if returncode:
        with pytest.raises(plugin_bridge.BridgeError, match="failure"):
            plugin_bridge._run("codex", "plugin", "list")
    else:
        assert plugin_bridge._run("codex", "plugin", "list") == "result"


def test_run_uses_safe_label_for_unknown_operation(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=plugin_bridge.__name__)
    monkeypatch.setattr(plugin_bridge.shutil, "which", lambda _: "/host/codex")
    monkeypatch.setattr(
        plugin_bridge.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "", ""),
    )
    plugin_bridge._run("codex", "private-operation", "private-argument")
    output = caplog.text
    assert "operation=host-command" in output
    assert "private" not in output


def test_run_reports_launch_failure_and_preserves_exception(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=plugin_bridge.__name__)
    failure = PermissionError("launch failed")
    monkeypatch.setattr(plugin_bridge.shutil, "which", lambda _: "/host/codex")

    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(plugin_bridge.subprocess, "run", fail)
    with pytest.raises(PermissionError) as raised:
        plugin_bridge._run("codex", "plugin", "marketplace", "list")
    assert raised.value is failure
    output = caplog.text
    assert "event=end" in output
    assert "status=error" in output


def test_run_times_exec_format_fallback_as_one_operation(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=plugin_bridge.__name__)
    monkeypatch.setattr(plugin_bridge.shutil, "which", lambda _: "/host/codex")
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        if len(calls) == 1:
            raise OSError(8, "exec format error")
        return subprocess.CompletedProcess(command, 0, "fallback result", "")

    monkeypatch.setattr(plugin_bridge.subprocess, "run", run)
    assert plugin_bridge._run("codex", "plugin", "list") == "fallback result"
    assert calls == [
        ["/host/codex", "plugin", "list"],
        ["/bin/sh", "/host/codex", "plugin", "list"],
    ]
    assert len(caplog.records) == 2


def test_run_does_not_redirect_timing_to_stdout_without_stderr(monkeypatch, capsys):
    monkeypatch.setattr(plugin_bridge.sys, "stderr", None)
    monkeypatch.setattr(plugin_bridge.shutil, "which", lambda _: "/host/codex")
    monkeypatch.setattr(
        plugin_bridge.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, "result", ""),
    )
    assert plugin_bridge._run("codex", "plugin", "list") == "result"
    assert capsys.readouterr().out == ""


def test_cli_configures_utc_logging_without_exposing_host_output(tmp_path):
    command = tmp_path / "codex"
    command.write_text("#!/bin/sh\nprintf 'private output'\n", encoding="utf-8")
    command.chmod(0o755)
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-c",
            (
                "import sys; "
                "sys.path.insert(0, sys.argv[1]); "
                "import plugin_bridge; "
                "plugin_bridge.reconcile = lambda *_: "
                "plugin_bridge._run('codex', 'plugin', 'list', 'private-argument'); "
                "raise SystemExit(plugin_bridge.main(sys.argv[2:]))"
            ),
            str(Path(plugin_bridge.__file__).parent),
            "reconcile",
            "--destination",
            str(tmp_path),
        ],
        input="{}",
        env={**os.environ, "PATH": str(tmp_path), "TZ": "Pacific/Honolulu"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    lines = result.stderr.splitlines()
    assert len(lines) == 2
    for line in lines:
        match = re.match(
            r"plugin-bridge: utc=(\S+) host=codex operation=plugin-list event=", line
        )
        assert match, line
        timestamp = datetime.strptime(match[1], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        assert abs((datetime.now(timezone.utc) - timestamp).total_seconds()) < 10
    assert "event=start" in lines[0]
    assert "event=end" in lines[1]
    assert "status=0" in lines[1]
    assert "private" not in result.stderr
