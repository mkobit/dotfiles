import json
import subprocess
import sys

from skill_filter import plugin_bridge


def test_reconcile_orders_marketplaces_capabilities_then_environment_plugins(
    tmp_path, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_marketplace",
        lambda host, name, source_type, locator, *args: calls.append(
            ("marketplace", name, host)
        ),
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
                "environment": "mydata",
                "marketplaces": {
                    "z-market": {"hosts": ["codex"], "order": 10},
                    "a-market": {"hosts": ["claude"], "order": 10},
                },
                "capabilities": {
                    "z-capability": {
                        "marketplace": "a-market",
                        "hosts": ["claude"],
                        "order": 20,
                    },
                    "a-capability": {
                        "marketplace": "a-market",
                        "hosts": ["codex"],
                        "order": 20,
                    },
                },
                "plugins": {
                    "z-plugin": {
                        "marketplace": "a-market",
                        "hosts": ["claude"],
                        "environments": ["mydata"],
                        "order": 1,
                    },
                    "a-plugin": {
                        "marketplace": "a-market",
                        "hosts": ["codex"],
                        "environments": ["mydata"],
                        "order": 1,
                    },
                },
            }
        },
    )

    assert calls == [
        ("marketplace", "a-market", "claude"),
        ("marketplace", "z-market", "codex"),
        ("plugin", "a-capability", "codex"),
        ("plugin", "z-capability", "claude"),
        ("plugin", "a-plugin", "codex"),
        ("plugin", "z-plugin", "claude"),
    ]


def test_reconcile_removes_plugins_before_marketplaces(tmp_path, monkeypatch):
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    ownership.write_text(
        """marketplace\tcodex\tz-market\t
plugin\tcodex\tb-market\tz-plugin
marketplace\tclaude\ta-market\t
plugin\tclaude\ta-market\ta-plugin
"""
    )
    calls = []
    monkeypatch.setattr(
        plugin_bridge,
        "_run",
        lambda host, *args: calls.append((host, *args)) or "",
    )

    plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert calls == [
        ("claude", "plugin", "uninstall", "a-plugin@a-market"),
        ("codex", "plugin", "remove", "z-plugin@b-market"),
        ("claude", "plugin", "marketplace", "remove", "a-market"),
        ("codex", "plugin", "marketplace", "remove", "z-market"),
    ]


def test_migrate_ownership_writes_canonical_tsv(tmp_path):
    legacy = tmp_path / "ownership.json"
    legacy.write_text(
        json.dumps(
            {
                "resources": [
                    {"kind": "plugin", "host": "claude", "id": "demo@market"},
                    {"kind": "marketplace", "host": "codex", "id": "market"},
                ]
            }
        )
    )

    result = subprocess.run(
        [sys.executable, str(plugin_bridge.__file__), "migrate-ownership", str(legacy)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert (
        result.stdout == "plugin\tclaude\tmarket\tdemo\nmarketplace\tcodex\tmarket\t\n"
    )


def test_has_identity_accepts_exact_json_identity():
    result = subprocess.run(
        [
            sys.executable,
            str(plugin_bridge.__file__),
            "has-identity",
            "--field",
            "id",
            "--expected",
            "demo@market",
        ],
        input='[{"id":"demo@market"}]\n',
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    result = subprocess.run(
        [
            sys.executable,
            str(plugin_bridge.__file__),
            "has-identity",
            "--field",
            "id",
            "--expected",
            "demo@market",
        ],
        input='[{"id":"demographic@market"}]\n',
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
