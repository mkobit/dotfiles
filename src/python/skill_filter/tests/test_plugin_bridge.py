from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
from typing import Any

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
    assert ownership.read_text() == f"marketplace\t{host}\tmarket\t\towned\n"


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
        "marketplace\tcodex\ta\t\towned\nmarketplace\tcodex\tb\t\towned\n"
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
        == f"marketplace\t{host}\tmarket\t\towned\nplugin\t{host}\tmarket\tdemo\towned\n"
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
        "marketplace\tcodex\tz-market\t\towned\nplugin\tcodex\tb-market\tz-plugin\towned\nmarketplace\tclaude\ta-market\t\towned\nplugin\tclaude\ta-market\ta-plugin\towned\n"
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
        ("codex", "plugin", "remove", "z-plugin@b-market"),
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
        "plugin\tclaude\tmarket\ta-plugin\towned\nplugin\tclaude\tmarket\tb-plugin\towned\n",
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
        "plugin\tclaude\tmarket\tb-plugin\towned\n"
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
        desired.add(plugin_bridge._identity("plugin", host, marketplace, name))
        if calls == 2:
            raise plugin_bridge.BridgeError("later failure")
        record = plugin_bridge._owned_record("plugin", host, marketplace, name)
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
    assert ownership.read_text() == "plugin\tclaude\tm\ta\towned\n"


@pytest.mark.parametrize(
    ("source_type", "recorded"), [("generated", True), ("public", False)]
)
def test_existing_claude_plugin_is_adopted_and_enabled(
    tmp_path, monkeypatch, source_type, recorded
):
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
    plugin_bridge._ensure_plugin(
        "claude",
        "market",
        "demo",
        ownership,
        desired,
        owned,
        source_type=source_type,
    )
    assert enabled
    assert ("claude", "plugin", "enable", "demo@market") in calls
    assert ("claude", "plugin", "update", "demo@market") not in calls
    assert owned == ({"plugin\tclaude\tmarket\tdemo\towned"} if recorded else set())
    assert ownership.exists() == recorded


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
    assert owned == {"plugin\tclaude\tmarket\tdemo\towned"}


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


def test_claude_plugin_without_manifest_root_is_not_updated_on_apply(
    tmp_path, monkeypatch
):
    calls = []
    _claude_manifest_root(tmp_path, "1.0.0+abc")
    monkeypatch.setattr(plugin_bridge, "_run", _claude_run(calls, "1.0.0+abc", True))
    plugin_bridge._ensure_plugin(
        "claude", "market", "demo", tmp_path / "ownership", set(), set()
    )
    assert ("claude", "plugin", "update", "demo@market") not in calls
    assert not [call for call in calls if call[2] in {"install", "uninstall", "enable"}]


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
        lambda host, marketplace, name, *args, manifest_root=None, **kwargs: (
            roots.update({marketplace: manifest_root})
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
    assert owned == {"plugin\tcodex\tmarket\tdemo\towned"}


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
def test_package_plugin_same_version_content_follows_host_policy(
    tmp_path, monkeypatch, host
):
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
        assert json.loads(manifest.read_text())["version"] == "7.0.0"

    if host == "claude":
        assert plugin_bridge._package_fingerprint(installed) == (
            plugin_bridge._package_fingerprint(source)
        )
        assert calls.count(("plugin", "uninstall", "demo@market")) == 1
        assert calls.count(("plugin", "install", "demo@market")) == 1
    else:
        # Package versions derive from content, so an equal Codex version is current.
        assert ("plugin", "add", "demo@market", "--json") not in calls


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
    ownership.write_text("plugin\tclaude\tmarket\tdemo\towned\n", encoding="utf-8")
    calls = []

    def run(host, *args):
        calls.append((host, *args))
        if args == ("plugin", "list", "--json"):
            return '[{"id":"demo@market","enabled":true}]'
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    with pytest.raises(plugin_bridge.BridgeError, match="did not disappear"):
        plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert ownership.read_text(encoding="utf-8") == (
        "plugin\tclaude\tmarket\tdemo\towned\n"
    )
    assert ("claude", "plugin", "uninstall", "demo@market") in calls


def test_reconcile_checkpoints_already_absent_plugin_without_removing(
    tmp_path, monkeypatch
):
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    ownership.write_text("plugin\tclaude\tmarket\tdemo\towned\n", encoding="utf-8")
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
    ownership.write_text("marketplace\tclaude\tmarket\t\towned\n", encoding="utf-8")
    calls = []

    def run(host, *args):
        calls.append((host, *args))
        if args == ("plugin", "marketplace", "list", "--json"):
            return '[{"name":"market"}]'
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    with pytest.raises(plugin_bridge.BridgeError, match="did not disappear"):
        plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert ownership.read_text(encoding="utf-8") == (
        "marketplace\tclaude\tmarket\t\towned\n"
    )
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
        "marketplace\tclaude\tkept-market\t\towned\n"
        "marketplace\tclaude\tstale-market\t\towned\n"
        "plugin\tclaude\tkept-market\tkept-plugin\towned\n"
        "plugin\tclaude\tstale-market\tstale-plugin\towned\n"
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


def _retired_declaration(marketplace, hosts, source_type="generated"):
    """Declare ``marketplace`` without hosts so only retirement logic runs."""
    return {
        "marketplaces": {
            marketplace: {
                "source_type": source_type,
                "hosts": [],
                **({"source_locator": "owner/repo"} if source_type == "public" else {}),
            }
        },
        "retired_plugins": {"retired": {"marketplace": marketplace, "hosts": hosts}},
    }


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_retired_plugin_removes_unowned_exact_identity_and_retries(
    tmp_path, monkeypatch, host
):
    installed = {"retired@old-market", "retired@new-market", "unrelated@old-market"}
    unavailable = True
    removals = []

    def run(command, *args):
        if unavailable:
            raise plugin_bridge.HostUnavailableError(command)
        if args[:2] == ("plugin", "list"):
            if command == "claude":
                return json.dumps(
                    [{"id": name, "enabled": True} for name in sorted(installed)]
                )
            return "\n".join(f"{name} enabled" for name in sorted(installed))
        if args[:2] in (("plugin", "uninstall"), ("plugin", "remove")):
            removals.append(args[2])
            installed.discard(args[2])
            return ""
        pytest.fail(f"unexpected host operation: {command} {args}")

    monkeypatch.setattr(plugin_bridge, "_run", run)
    declaration = _retired_declaration("old-market", [host])
    plugin_bridge.reconcile(tmp_path, declaration)
    assert installed == {
        "retired@old-market",
        "retired@new-market",
        "unrelated@old-market",
    }
    unavailable = False
    plugin_bridge.reconcile(tmp_path, declaration)
    plugin_bridge.reconcile(tmp_path, declaration)
    assert installed == {"retired@new-market", "unrelated@old-market"}
    assert removals == ["retired@old-market"] * (2 if host == "codex" else 1)
    assert (tmp_path / ".local/state/dotfiles/agent-plugin-ownership").read_text() == ""
    # An unowned identity in a public marketplace is not removed.
    plugin_bridge.reconcile(
        tmp_path, _retired_declaration("new-market", [host], "public")
    )
    assert installed == {"retired@new-market", "unrelated@old-market"}


@pytest.mark.parametrize(
    "retired",
    [
        [],
        {"bad/name": {"marketplace": "old-market", "hosts": ["claude"]}},
        {"retired": []},
        {"retired": {"marketplace": "bad/name", "hosts": ["claude"]}},
        {"retired": {"marketplace": "old-market"}},
        {"retired": {"marketplace": "old-market", "hosts": []}},
        {"retired": {"marketplace": "old-market", "hosts": "claude"}},
        {"retired": {"marketplace": "old-market", "hosts": ["unknown"]}},
        {"retired": {"marketplace": "old-market", "hosts": ["claude"], "extra": True}},
    ],
)
def test_retired_plugin_rejects_invalid_declarations_before_mutation(
    tmp_path, monkeypatch, retired
):
    monkeypatch.setattr(
        plugin_bridge, "_run", lambda *args: pytest.fail("unexpected host operation")
    )
    with pytest.raises(plugin_bridge.BridgeError):
        plugin_bridge.reconcile(tmp_path, {"retired_plugins": retired})
    assert not (tmp_path / ".local").exists()


@pytest.mark.parametrize("kind", ["plugins", "capabilities"])
def test_retired_plugin_rejects_desired_identity_before_mutation(
    tmp_path, monkeypatch, kind
):
    declaration = _valid_bridge()
    name = "plugin" if kind == "plugins" else "capability"
    bridge = declaration["plugin_bridge"]
    assert isinstance(bridge, dict)
    bridge["retired_plugins"] = {name: {"marketplace": "market", "hosts": ["claude"]}}
    monkeypatch.setattr(
        plugin_bridge, "_run", lambda *args: pytest.fail("unexpected host operation")
    )
    with pytest.raises(plugin_bridge.BridgeError, match="desired and retired"):
        plugin_bridge.reconcile(tmp_path, declaration)
    assert not (tmp_path / ".local").exists()


def test_retired_codex_plugin_removes_registration_absent_from_catalog(
    tmp_path, monkeypatch
):
    registered = {"retired@old-market", "retired@new-market"}
    removals = []

    def run(host, *args):
        if args[:2] == ("plugin", "list"):
            return ""
        if args[:2] == ("plugin", "remove"):
            removals.append(args[2])
            registered.discard(args[2])
            return "Removed plugin"
        pytest.fail(f"unexpected host operation: {host} {args}")

    monkeypatch.setattr(plugin_bridge, "_run", run)
    declaration = _retired_declaration("old-market", ["codex"])
    plugin_bridge.reconcile(tmp_path, declaration)
    plugin_bridge.reconcile(tmp_path, declaration)
    assert registered == {"retired@new-market"}
    assert removals == ["retired@old-market", "retired@old-market"]


def test_retired_codex_plugin_propagates_removal_failure(tmp_path, monkeypatch):
    def run(host, *args):
        if args[:2] == ("plugin", "list"):
            return ""
        raise plugin_bridge.BridgeError("removal failed")

    monkeypatch.setattr(plugin_bridge, "_run", run)
    declaration = _retired_declaration("old-market", ["codex"])
    with pytest.raises(plugin_bridge.BridgeError, match="removal failed"):
        plugin_bridge.reconcile(tmp_path, declaration)


def test_retired_codex_plugin_removes_registration_without_marketplace(
    tmp_path, monkeypatch
):
    registered = {"retired@removed-market"}

    def run(host, *args):
        if args == ("plugin", "remove", "retired@removed-market"):
            registered.discard(args[2])
            return "Removed plugin"
        raise plugin_bridge.BridgeError("marketplace is unavailable")

    monkeypatch.setattr(plugin_bridge, "_run", run)
    declaration = _retired_declaration("removed-market", ["codex"])
    plugin_bridge.reconcile(tmp_path, declaration)
    assert registered == set()


@pytest.mark.parametrize("initially_unavailable", [False, True])
def test_retired_codex_plugin_clears_owned_registration_without_marketplace(
    tmp_path, monkeypatch, initially_unavailable
):
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    record = "plugin\tcodex\tremoved-market\tretired\towned\n"
    ownership.write_text(record)
    registered = {"retired@removed-market"}
    unavailable = initially_unavailable
    removals = []

    def run(host, *args):
        if unavailable:
            raise plugin_bridge.HostUnavailableError(host)
        if args == ("plugin", "remove", "retired@removed-market"):
            registered.discard(args[2])
            removals.append(args[2])
            return "Removed plugin"
        raise plugin_bridge.BridgeError("marketplace is unavailable")

    monkeypatch.setattr(plugin_bridge, "_run", run)
    declaration = _retired_declaration("removed-market", ["codex"])
    if unavailable:
        plugin_bridge.reconcile(tmp_path, declaration)
        assert ownership.read_text() == record
        assert registered == {"retired@removed-market"}
        unavailable = False
    plugin_bridge.reconcile(tmp_path, declaration)
    assert registered == set()
    assert ownership.read_text() == ""
    assert removals == ["retired@removed-market"]


@pytest.mark.parametrize("hosts", [["cursor"], ["claude", "codex", "cursor"]])
def test_retired_plugin_accepts_cursor_and_removes_only_native_registrations(
    tmp_path, monkeypatch, hosts
):
    installed = {"claude", "codex", "cursor"}

    def run(host, *args):
        assert host != "cursor"
        if args == ("plugin", "list", "--json"):
            return json.dumps(
                [{"id": "retired@market", "enabled": True}] if host in installed else []
            )
        if args in (
            ("plugin", "uninstall", "retired@market"),
            ("plugin", "remove", "retired@market"),
        ):
            installed.discard(host)
            return ""
        pytest.fail(f"unexpected host operation: {host} {args}")

    monkeypatch.setattr(plugin_bridge, "_run", run)
    plugin_bridge.reconcile(tmp_path, _retired_declaration("market", hosts))
    assert installed == (
        {"cursor"} if "codex" in hosts else {"claude", "codex", "cursor"}
    )


def test_stale_owned_codex_plugin_removes_registration_absent_from_catalog(
    tmp_path, monkeypatch
):
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    ownership.write_text("plugin\tcodex\told-market\tretired\towned\n")
    registered = {"retired@old-market", "retired@new-market"}

    def run(host, *args):
        if args[:2] == ("plugin", "list"):
            return ""
        if args == ("plugin", "remove", "retired@old-market"):
            registered.discard(args[2])
            return "Removed plugin"
        pytest.fail(f"unexpected host operation: {host} {args}")

    monkeypatch.setattr(plugin_bridge, "_run", run)
    plugin_bridge.reconcile(tmp_path, {})
    assert registered == {"retired@new-market"}
    assert ownership.read_text() == ""


def _plugin_cli(host, installed, *, enabled=True):
    """Fake host CLI tracking installed plugin ids and mutations."""
    mutations = []

    def run(command, *args):
        assert command == host
        if args[:2] == ("plugin", "list"):
            if host == "claude":
                return json.dumps(
                    [{"id": name, "enabled": enabled} for name in sorted(installed)]
                )
            return json.dumps(
                {
                    "installed": [
                        {"pluginId": name, "installed": True, "enabled": enabled}
                        for name in sorted(installed)
                    ]
                }
            )
        if args[:3] == ("plugin", "marketplace", "list"):
            return "[]" if host == "claude" else "market  /x\n"
        mutations.append(args)
        if args[:2] in {("plugin", "install"), ("plugin", "add")}:
            installed.add(args[2])
        elif args[:2] in {("plugin", "uninstall"), ("plugin", "remove")}:
            installed.discard(args[2])
        return ""

    return mutations, run


def _public_declaration(host, source_type="public"):
    return {
        "plugin_bridge": {
            "marketplaces": {
                "market": {
                    "source_type": source_type,
                    "source_locator": "owner/repo"
                    if source_type != "host-provided"
                    else "",
                    "hosts": [host],
                }
            },
            "plugins": {"demo": {"marketplace": "market", "hosts": [host]}},
        }
    }


def _ownership_file(tmp_path):
    return tmp_path / ".local/state/dotfiles/agent-plugin-ownership"


def test_manually_installed_public_plugin_is_not_owned_or_removed(
    tmp_path, monkeypatch
):
    mutations, run = _plugin_cli("claude", {"demo@market"})
    monkeypatch.setattr(plugin_bridge, "_run", run)
    monkeypatch.setattr(plugin_bridge, "_marketplace_present", lambda *args: True)
    declaration = _public_declaration("claude")

    plugin_bridge.reconcile(tmp_path, declaration)
    assert _ownership_file(tmp_path).read_text() == ""
    assert ("plugin", "install", "demo@market") not in mutations

    declaration["plugin_bridge"]["plugins"].clear()
    plugin_bridge.reconcile(tmp_path, declaration)
    assert ("plugin", "uninstall", "demo@market") not in mutations
    assert _ownership_file(tmp_path).read_text() == ""


def test_public_plugin_installed_by_bridge_is_owned_then_removed_when_undesired(
    tmp_path, monkeypatch
):
    installed = set()
    mutations, run = _plugin_cli("claude", installed)
    monkeypatch.setattr(plugin_bridge, "_run", run)
    monkeypatch.setattr(plugin_bridge, "_marketplace_present", lambda *args: True)
    declaration = _public_declaration("claude")

    plugin_bridge.reconcile(tmp_path, declaration)
    assert installed == {"demo@market"}
    assert "plugin\tclaude\tmarket\tdemo\towned" in (
        _ownership_file(tmp_path).read_text().splitlines()
    )
    plugin_bridge.reconcile(tmp_path, declaration)
    assert mutations.count(("plugin", "install", "demo@market")) == 1


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_host_provided_plugins_are_owned_only_when_the_bridge_installs_them(
    tmp_path, monkeypatch, host
):
    installed = {"demo@market"}
    state = {"enabled": False}
    mutations = []

    def run(command, *args):
        if args[:3] == ("plugin", "marketplace", "list"):
            return '[{"name":"market"}]' if host == "claude" else "market  /x\n"
        if args[:2] == ("plugin", "list"):
            records = [
                {"id": n, "pluginId": n, "installed": True, "enabled": state["enabled"]}
                for n in sorted(installed)
            ]
            return json.dumps(records if host == "claude" else {"installed": records})
        mutations.append(args)
        if args[:2] in {("plugin", "install"), ("plugin", "add")}:
            installed.add(args[2])
        elif args[:2] in {("plugin", "uninstall"), ("plugin", "remove")}:
            installed.discard(args[2])
        state["enabled"] = True
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    declaration = _public_declaration(host, "host-provided")
    declaration["plugin_bridge"]["plugins"]["other"] = {
        "marketplace": "market",
        "hosts": [host],
    }
    plugin_bridge.reconcile(tmp_path, declaration)
    plugin_bridge.reconcile(tmp_path, declaration)

    verbs = {args[:2] for args in mutations}
    assert verbs <= {("plugin", "install"), ("plugin", "add"), ("plugin", "enable")}
    assert _ownership_file(tmp_path).read_text() == (
        f"plugin\t{host}\tmarket\tother\towned\n"
    )

    declaration["plugin_bridge"]["plugins"].clear()
    mutations.clear()
    plugin_bridge.reconcile(tmp_path, declaration)
    removal = "uninstall" if host == "claude" else "remove"
    assert mutations == [("plugin", removal, "other@market")]
    assert installed == {"demo@market"}
    assert _ownership_file(tmp_path).read_text() == ""


def test_missing_host_provided_marketplace_is_unavailable_without_failing_other_marketplaces(
    tmp_path, monkeypatch, caplog
):
    mutations = []

    def run(command, *args):
        if args[:3] == ("plugin", "marketplace", "list"):
            return "[]"
        if args[:2] == ("plugin", "list"):
            return "[]"
        mutations.append(args)
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    registered = []
    monkeypatch.setattr(
        plugin_bridge,
        "_generated_marketplace_source",
        lambda host, name: registered[-1] if registered else None,
    )
    original_run = run

    def run(command, *args):
        if args[:3] == ("plugin", "marketplace", "add"):
            registered.append(plugin_bridge.Path(args[3]))
        return original_run(command, *args)

    monkeypatch.setattr(plugin_bridge, "_run", run)
    monkeypatch.setattr(
        plugin_bridge,
        "_claude_plugin_state",
        lambda *args: (True, True, "1", None),
    )
    declaration = {
        "plugin_bridge": {
            "marketplaces": {
                "corp": {
                    "source_type": "host-provided",
                    "hosts": ["claude"],
                    "order": 1,
                },
                "mine": {"source_type": "generated", "hosts": ["claude"], "order": 2},
            },
            "plugins": {
                "wrapped": {"marketplace": "corp", "hosts": ["claude"]},
                "own": {"marketplace": "mine", "hosts": ["claude"]},
            },
        }
    }
    caplog.set_level("INFO", logger=plugin_bridge.logger.name)
    monkeypatch.setattr(plugin_bridge, "_ensure_package_plugin", lambda *args: None)
    plugin_bridge.reconcile(tmp_path, declaration)

    assert "host=claude marketplace=corp event=unavailable" in caplog.text
    assert not any("corp" in " ".join(args) for args in mutations)
    assert any(args[:3] == ("plugin", "marketplace", "add") for args in mutations)
    assert _ownership_file(tmp_path).read_text() == (
        "marketplace\tclaude\tmine\t\towned\nplugin\tclaude\tmine\town\towned\n"
    )


def test_owned_record_removed_when_undesired_and_ambiguous_record_preserved(
    tmp_path, monkeypatch
):
    ownership = _ownership_file(tmp_path)
    ownership.parent.mkdir(parents=True)
    ownership.write_text(
        "plugin\tclaude\tmarket\tmine\towned\n"
        "plugin\tclaude\tmarket\ttheirs\tambiguous\n"
    )
    installed = {"mine@market", "theirs@market"}
    _, run = _plugin_cli("claude", installed)
    monkeypatch.setattr(plugin_bridge, "_run", run)

    plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert installed == {"theirs@market"}
    assert ownership.read_text() == "plugin\tclaude\tmarket\ttheirs\tambiguous\n"


@pytest.mark.parametrize(
    ("declared", "expected"),
    [
        ("generated", "owned"),
        ("host-provided", None),
        ("public", "ambiguous"),
        (None, "ambiguous"),
    ],
    ids=[
        "generated-owned",
        "host-provided-dropped",
        "public-ambiguous",
        "undeclared-ambiguous",
    ],
)
def test_v1_ownership_migration_classifies_records(
    tmp_path, monkeypatch, declared, expected
):
    ownership = _ownership_file(tmp_path)
    ownership.parent.mkdir(parents=True)
    ownership.write_text("plugin\tclaude\tmarket\tdemo\n")
    marketplaces = {}
    if declared:
        marketplaces["market"] = {
            "source_type": declared,
            "hosts": [],
            **({"source_locator": "o/r"} if declared == "public" else {}),
        }
    migrated = []

    def run(command, *args):
        # The first host call must already see the migrated file.
        migrated.append(ownership.read_text())
        raise plugin_bridge.HostUnavailableError(command)

    monkeypatch.setattr(plugin_bridge, "_run", run)
    plugin_bridge.reconcile(
        tmp_path,
        {
            "plugin_bridge": {
                "marketplaces": marketplaces,
                "retired_plugins": {"x": {"marketplace": "gone", "hosts": ["claude"]}},
            }
        },
    )
    # An unavailable host keeps every record, so the file shows the migration.
    wanted = "" if expected is None else f"plugin\tclaude\tmarket\tdemo\t{expected}\n"
    assert ownership.read_text() == wanted


def test_retired_plugin_removal_requires_ownership_or_generated_marketplace(
    tmp_path, monkeypatch
):
    ownership = _ownership_file(tmp_path)
    ownership.parent.mkdir(parents=True)
    ambiguous = "plugin\tclaude\tpub\tretired\tambiguous\n"
    ownership.write_text(ambiguous)
    installed = {"retired@pub", "retired@gen"}
    _, run = _plugin_cli("claude", installed)
    monkeypatch.setattr(plugin_bridge, "_run", run)
    declaration = {
        "plugin_bridge": {
            "marketplaces": {
                "pub": {"source_type": "public", "hosts": [], "source_locator": "o/r"},
                "gen": {"source_type": "generated", "hosts": []},
            },
            "retired_plugins": {"retired": {"marketplace": "pub", "hosts": ["claude"]}},
        }
    }
    retired = declaration["plugin_bridge"]["retired_plugins"]["retired"]

    plugin_bridge.reconcile(tmp_path, declaration)
    assert installed == {"retired@pub", "retired@gen"}
    assert ownership.read_text() == ambiguous

    retired["marketplace"] = "gen"
    plugin_bridge.reconcile(tmp_path, declaration)
    assert installed == {"retired@pub"}
    assert ownership.read_text() == ambiguous

    retired["marketplace"] = "pub"
    ownership.write_text("plugin\tclaude\tpub\tretired\towned\n")
    plugin_bridge.reconcile(tmp_path, declaration)
    assert installed == set()
    assert ownership.read_text() == ""


def test_unavailable_host_retains_owned_and_ambiguous_records(tmp_path, monkeypatch):
    monkeypatch.setattr(plugin_bridge.shutil, "which", lambda command: None)
    ownership = _ownership_file(tmp_path)
    ownership.parent.mkdir(parents=True)
    content = (
        "plugin\tclaude\tmarket\tmine\towned\n"
        "plugin\tclaude\tmarket\ttheirs\tambiguous\n"
    )
    ownership.write_text(content)

    plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert ownership.read_text() == content


def _catalog_host(
    host,
    tmp_path,
    *,
    marketplace=True,
    installed_version=None,
    enabled=True,
    install_path=None,
):
    """Fake host CLI for an external marketplace whose catalog moves from 1.0.0 to 2.0.0 on refresh."""
    state: dict[str, Any] = {
        "marketplace": marketplace,
        "available": "1.0.0",
        "installed": installed_version,
        "enabled": enabled,
        "calls": [],
    }
    source = tmp_path / "catalog"
    manifest = source / ".codex-plugin/plugin.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)

    def publish():
        manifest.write_text(json.dumps({"name": "demo", "version": state["available"]}))

    publish()

    def run(command, *args):
        assert command == host
        state["calls"].append(args)
        if args[:3] == ("plugin", "marketplace", "list"):
            if not state["marketplace"]:
                return "[]" if host == "claude" else ""
            return '[{"name": "market"}]' if host == "claude" else "market  /x\n"
        if args[:2] == ("plugin", "list"):
            if state["installed"] is None:
                return "[]" if host == "claude" else '{"installed": []}'
            if host == "claude":
                return json.dumps(
                    [
                        {
                            "id": "demo@market",
                            "version": state["installed"],
                            "enabled": state["enabled"],
                            **(
                                {"installPath": str(install_path)}
                                if install_path
                                else {}
                            ),
                        }
                    ]
                )
            return json.dumps(
                {
                    "installed": [
                        {
                            "pluginId": "demo@market",
                            "installed": True,
                            "enabled": state["enabled"],
                            "version": state["installed"],
                            "source": {"path": str(source)},
                        }
                    ]
                }
            )
        if args[:3] == ("plugin", "marketplace", "add"):
            state["marketplace"] = True
        elif args[:3] in {
            ("plugin", "marketplace", "update"),
            ("plugin", "marketplace", "upgrade"),
        }:
            state["available"] = "2.0.0"
            publish()
        elif args[:2] in {
            ("plugin", "install"),
            ("plugin", "add"),
            ("plugin", "update"),
        }:
            state["installed"] = state["available"]
            state["enabled"] = True
        elif args[:2] in {("plugin", "uninstall"), ("plugin", "remove")}:
            state["installed"] = None
        elif args[:2] == ("plugin", "enable"):
            state["enabled"] = True
        return ""

    return state, run


def _mutations(state):
    return [
        args
        for args in state["calls"]
        if args[:2] != ("plugin", "list")
        and args[:3] != ("plugin", "marketplace", "list")
    ]


def _owned_records(host):
    return "".join(
        f"{kind}\t{host}\tmarket\t{plugin}\towned\n"
        for kind, plugin in (("marketplace", ""), ("plugin", "demo"))
    )


def _write_owned(tmp_path, host):
    _ownership_file(tmp_path).parent.mkdir(parents=True)
    _ownership_file(tmp_path).write_text(_owned_records(host))


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_apply_does_not_refresh_present_public_marketplace(tmp_path, monkeypatch, host):
    state, run = _catalog_host(
        host, tmp_path, marketplace=True, installed_version="1.0.0"
    )
    monkeypatch.setattr(plugin_bridge, "_run", run)
    _write_owned(tmp_path, host)

    plugin_bridge.reconcile(tmp_path, _public_declaration(host))

    assert _mutations(state) == []
    assert state["available"] == "1.0.0"


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_apply_adds_absent_public_marketplace_and_installs_plugin(
    tmp_path, monkeypatch, host
):
    state, run = _catalog_host(host, tmp_path, marketplace=False)
    monkeypatch.setattr(plugin_bridge, "_run", run)

    plugin_bridge.reconcile(tmp_path, _public_declaration(host))

    verb = "install" if host == "claude" else "add"
    assert _mutations(state) == [
        ("plugin", "marketplace", "add", "owner/repo"),
        ("plugin", verb, "demo@market"),
    ]
    assert set(_ownership_file(tmp_path).read_text().splitlines()) == set(
        _owned_records(host).splitlines()
    )


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_refresh_updates_owned_public_marketplace_then_plugins(
    tmp_path, monkeypatch, host
):
    state, run = _catalog_host(
        host, tmp_path, marketplace=True, installed_version="1.0.0"
    )
    monkeypatch.setattr(plugin_bridge, "_run", run)
    _write_owned(tmp_path, host)

    plugin_bridge.reconcile(tmp_path, _public_declaration(host), refresh=True)

    refresh = "update" if host == "claude" else "upgrade"
    expected: list[tuple[str, ...]] = [("plugin", "marketplace", refresh, "market")]
    expected += (
        [("plugin", "update", "demo@market")]
        if host == "claude"
        else [("plugin", "remove", "demo@market"), ("plugin", "add", "demo@market")]
    )
    assert _mutations(state) == expected
    assert state["installed"] == "2.0.0"

    state["calls"].clear()
    plugin_bridge.reconcile(tmp_path, _public_declaration(host), refresh=True)
    if host == "codex":
        assert _mutations(state) == [("plugin", "marketplace", "upgrade", "market")]


def test_refresh_does_not_touch_adopted_public_marketplace_or_plugin(
    tmp_path, monkeypatch
):
    state, run = _catalog_host(
        "claude", tmp_path, marketplace=True, installed_version="1.0.0"
    )
    monkeypatch.setattr(plugin_bridge, "_run", run)

    plugin_bridge.reconcile(tmp_path, _public_declaration("claude"), refresh=True)

    assert _mutations(state) == []
    assert _ownership_file(tmp_path).read_text() == ""


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_refresh_never_touches_host_provided_or_generated_marketplaces(
    tmp_path, monkeypatch, host
):
    state, run = _catalog_host(
        host, tmp_path, marketplace=True, installed_version="1.0.0"
    )
    monkeypatch.setattr(plugin_bridge, "_run", run)

    plugin_bridge.reconcile(
        tmp_path, _public_declaration(host, "host-provided"), refresh=True
    )
    assert _mutations(state) == []

    generated = _public_declaration(host, "generated")
    generated["plugin_bridge"]["marketplaces"]["market"]["source_locator"] = ""
    root = tmp_path / ".local/share/agent-plugins/marketplace"
    monkeypatch.setattr(
        plugin_bridge, "_generated_marketplace_source", lambda *args: root
    )
    plugin_bridge.reconcile(tmp_path, generated, refresh=True)
    assert not [args for args in _mutations(state) if {"update", "upgrade"} & set(args)]
    assert state["available"] == "1.0.0"


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_refresh_does_not_change_pinned_archive_marketplace(
    tmp_path, monkeypatch, host
):
    """A generated archive marketplace changes only through its catalog pin, never through refresh."""
    root = tmp_path / ".local/share/agent-plugins/marketplace"
    package = root / "plugins/demo"
    state, run = _catalog_host(
        host,
        tmp_path,
        marketplace=True,
        installed_version="1.0.0",
        install_path=package,
    )
    monkeypatch.setattr(plugin_bridge, "_run", run)
    monkeypatch.setattr(
        plugin_bridge, "_generated_marketplace_source", lambda *args: root
    )
    declaration = _generated_declaration(host)
    declaration["plugin_bridge"]["plugins"]["demo"]["package_path"] = "./plugins/demo"
    (package / f".{host}-plugin").mkdir(parents=True)
    (package / f".{host}-plugin/plugin.json").write_text(
        json.dumps({"name": "demo", "version": "1.0.0"})
    )
    monkeypatch.setattr(plugin_bridge, "_package_fingerprint", lambda path: "same")

    plugin_bridge.reconcile(tmp_path, declaration, refresh=True)

    assert not [args for args in _mutations(state) if {"update", "upgrade"} & set(args)]
    assert state["available"] == "1.0.0"


def _codex_package(tmp_path, version):
    package = tmp_path / "package"
    (package / ".codex-plugin").mkdir(parents=True)
    (package / ".codex-plugin/plugin.json").write_text(
        json.dumps({"name": "demo", "version": version})
    )
    return package


@pytest.mark.parametrize(
    ("enabled", "installed_version", "adds"),
    [(True, "3.0.0", 0), (False, "3.0.0", 1), (True, "2.0.0", 1)],
)
def test_unchanged_codex_package_plugin_is_not_added_again(
    tmp_path, monkeypatch, enabled, installed_version, adds
):
    package = _codex_package(tmp_path, "3.0.0")
    calls = []

    def run(command, *args):
        calls.append(args)
        if args == ("plugin", "list", "-m", "market", "--json"):
            return json.dumps(
                {
                    "installed": [
                        {
                            "pluginId": "demo@market",
                            "installed": True,
                            "enabled": enabled
                            or ("plugin", "add", "demo@market", "--json") in calls,
                            "version": installed_version,
                        }
                    ]
                }
            )
        if args == ("plugin", "add", "demo@market", "--json"):
            return json.dumps({"installedPath": str(package)})
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    monkeypatch.setattr(plugin_bridge, "_package_fingerprint", lambda path: "same")

    plugin_bridge._ensure_package_plugin("codex", "market", "demo", package)

    assert calls.count(("plugin", "add", "demo@market", "--json")) == adds


def test_disabled_host_provided_codex_plugin_is_not_re_enabled(
    tmp_path, monkeypatch, caplog
):
    state, run = _catalog_host(
        "codex", tmp_path, marketplace=True, installed_version="1.0.0", enabled=False
    )
    monkeypatch.setattr(plugin_bridge, "_run", run)

    with caplog.at_level("INFO"):
        plugin_bridge.reconcile(tmp_path, _public_declaration("codex", "host-provided"))

    assert _mutations(state) == []
    assert "event=skip-reenable" in caplog.text
    assert _ownership_file(tmp_path).read_text() == ""


def test_second_unchanged_reconcile_issues_only_list_calls(tmp_path, monkeypatch):
    """Generated package plugins on both hosts settle after one reconcile."""
    root = tmp_path / ".local/share/agent-plugins/marketplace"
    package = root / "plugins/demo"
    for host in ("claude", "codex"):
        (package / f".{host}-plugin").mkdir(parents=True)
        (package / f".{host}-plugin/plugin.json").write_text(
            json.dumps({"name": "demo", "version": "4.0.0"})
        )
    (package / "payload").write_text("content\n")
    hosts: dict[str, dict[str, Any]] = {
        host: {"registered": None, "installed": False, "calls": []}
        for host in ("claude", "codex")
    }

    def run(host, *args):
        state = hosts[host]
        state["calls"].append(args)
        if args[:3] == ("plugin", "marketplace", "list"):
            registered = state["registered"]
            if registered is None:
                return "[]" if host == "claude" else '{"marketplaces": []}'
            if host == "claude":
                return json.dumps(
                    [{"name": "market", "source": "directory", "path": registered}]
                )
            return json.dumps(
                {
                    "marketplaces": [
                        {
                            "name": "market",
                            "marketplaceSource": {
                                "sourceType": "local",
                                "source": registered,
                            },
                        }
                    ]
                }
            )
        if args[:3] == ("plugin", "marketplace", "add"):
            state["registered"] = args[3]
        elif args[:2] == ("plugin", "list"):
            if not state["installed"]:
                return "[]" if host == "claude" else '{"installed": []}'
            if host == "claude":
                return json.dumps(
                    [
                        {
                            "id": "demo@market",
                            "version": "4.0.0",
                            "enabled": True,
                            "installPath": str(package),
                        }
                    ]
                )
            return json.dumps(
                {
                    "installed": [
                        {
                            "pluginId": "demo@market",
                            "installed": True,
                            "enabled": True,
                            "version": "4.0.0",
                            "source": {"path": str(package)},
                        }
                    ]
                }
            )
        elif args[:2] in {("plugin", "install"), ("plugin", "add")}:
            state["installed"] = True
            if host == "codex":
                return json.dumps({"installedPath": str(package)})
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    monkeypatch.setattr(
        plugin_bridge, "_repair_missing_codex_marketplaces", lambda sources: None
    )
    declaration = {
        "plugin_bridge": {
            "marketplaces": {
                "market": {"source_type": "generated", "hosts": ["claude", "codex"]}
            },
            "plugins": {
                "demo": {
                    "marketplace": "market",
                    "hosts": ["claude", "codex"],
                    "package_path": "./plugins/demo",
                }
            },
        }
    }
    plugin_bridge.reconcile(tmp_path, declaration)
    assert all(state["installed"] for state in hosts.values())
    for state in hosts.values():
        state["calls"].clear()

    plugin_bridge.reconcile(tmp_path, declaration)

    for host, state in hosts.items():
        assert state["calls"], host
        assert all(
            args[:2] == ("plugin", "list")
            or args[:3] == ("plugin", "marketplace", "list")
            for args in state["calls"]
        ), (host, state["calls"])


def test_main_refreshes_on_flag_chezmoi_refresh_or_expired_stamp(tmp_path, monkeypatch):
    calls = []

    def fake_reconcile(destination, declaration, *, refresh=False):
        calls.append(refresh)

    monkeypatch.setattr(plugin_bridge, "reconcile", fake_reconcile)
    stamp = tmp_path / ".local/state/dotfiles/agent-plugin-refresh"
    argv = ["reconcile", "--destination", str(tmp_path)]

    def run(env_args="chezmoi apply", extra=()):
        monkeypatch.setenv("CHEZMOI_ARGS", env_args)
        monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
        assert plugin_bridge.main([*argv, *extra]) == 0
        return calls[-1]

    assert run() is True  # no stamp yet
    assert stamp.exists()
    assert run() is False  # inside the 24-hour window: no network refresh
    assert run(extra=["--refresh"]) is True
    assert run("chezmoi apply -R") is True
    assert run("chezmoi --config c apply --refresh-externals --no-tty") is True
    assert run("chezmoi apply --refresh-externals=never") is False
    old = stamp.stat().st_mtime - plugin_bridge._REFRESH_INTERVAL_SECONDS - 1
    plugin_bridge.os.utime(stamp, (old, old))
    assert run() is True


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


@pytest.mark.parametrize("probe_status", [None, 1, 0])
def test_agy_installs_generated_plugin_directories_only_when_the_cli_works(
    tmp_path, monkeypatch, caplog, probe_status
):
    commands = []

    def command(arguments):
        commands.append(arguments)
        if arguments[-1] == "--help":
            return probe_status
        return 3  # a failed install is logged, never raised

    marketplace = tmp_path / "m"
    for name in ("with-manifest", "other-with-manifest"):
        (marketplace / "plugins" / name).mkdir(parents=True)
        (marketplace / "plugins" / name / "plugin.json").write_text("{}")
    (marketplace / "plugins" / "no-manifest").mkdir()
    monkeypatch.setattr(plugin_bridge, "_cli_host_command", command)
    caplog.set_level("INFO", logger=plugin_bridge.logger.name)
    plugin_bridge.reconcile(
        tmp_path,
        {
            "plugin_bridge": {
                "cli_hosts": ["antigravity"],
                "marketplaces": {
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
            }
        },
    )

    installs = [
        arguments
        for arguments in commands
        if arguments[:3] == ("agy", "plugin", "install")
    ]
    if probe_status == 0:
        assert installs == [
            ("agy", "plugin", "install", str(marketplace / "plugins" / name))
            for name in ("other-with-manifest", "with-manifest")
        ]
        assert ("agy", "plugin", "list", "--json") in commands
        assert (
            "host=antigravity marketplace=dotfiles plugin=with-manifest operation=plugin-install status=3"
            in caplog.text
        )
    else:
        assert installs == []
        assert "host=antigravity event=unavailable reason=no-plugin-cli" in caplog.text


def test_cli_hosts_reject_unknown_hosts(tmp_path):
    with pytest.raises(plugin_bridge.BridgeError, match="cli_hosts"):
        plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {"cli_hosts": ["cursor"]}})


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_legacy_declared_host_provided_record_migrates_owned_then_uninstalls(
    tmp_path, monkeypatch, host
):
    ownership = _ownership_file(tmp_path)
    ownership.parent.mkdir(parents=True)
    ownership.write_text(
        f"plugin\t{host}\tmarket\tdemo\nplugin\t{host}\tmarket\tundeclared\n"
    )
    installed = {"demo@market", "undeclared@market"}
    mutations = []

    def run(command, *args):
        if args[:3] == ("plugin", "marketplace", "list"):
            return '[{"name":"market"}]' if host == "claude" else "market  /x\n"
        if args[:2] == ("plugin", "list"):
            records = [
                {"id": n, "pluginId": n, "installed": True, "enabled": True}
                for n in sorted(installed)
            ]
            return json.dumps(records if host == "claude" else {"installed": records})
        mutations.append(args)
        if args[:2] in {("plugin", "uninstall"), ("plugin", "remove")}:
            installed.discard(args[2])
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    declaration = _public_declaration(host, "host-provided")
    plugin_bridge.reconcile(tmp_path, declaration)
    assert ownership.read_text() == f"plugin\t{host}\tmarket\tdemo\towned\n"
    assert mutations == []

    declaration["plugin_bridge"]["plugins"].clear()
    plugin_bridge.reconcile(tmp_path, declaration)
    removal = "uninstall" if host == "claude" else "remove"
    assert mutations == [("plugin", removal, "demo@market")]
    assert installed == {"undeclared@market"}
    assert ownership.read_text() == ""
