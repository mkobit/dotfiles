from __future__ import annotations

import json
import subprocess
import sys

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
        plugin_bridge,
        "_ensure_marketplace",
        lambda host, name, *args: calls.append(("marketplace", name, host)),
    )
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_plugin",
        lambda host, marketplace, name, *args: calls.append(("plugin", name, host)),
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
        lambda host, marketplace, name, *args: calls.append(
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
        plugin_bridge,
        "_ensure_marketplace",
        lambda host, *args: calls.append(("marketplace", host)),
    )
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_plugin",
        lambda host, *args: calls.append(("plugin", host)),
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

    def ensure(host, marketplace, name, ownership_file, desired, owned):
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


def test_existing_codex_plugin_is_not_added_again(tmp_path, monkeypatch):
    calls = []

    def run(host, *args):
        calls.append((host, *args))
        if args == ("plugin", "list", "-m", "market"):
            return "demo@market  installed, enabled  1.0.0  /fixture/demo\n"
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)
    desired, owned = set(), set()
    plugin_bridge._ensure_plugin(
        "codex", "market", "demo", tmp_path / "ownership", desired, owned
    )

    assert ("codex", "plugin", "add", "demo@market") not in calls
    assert owned == {"plugin\tcodex\tmarket\tdemo"}


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
