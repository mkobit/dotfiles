import json
import subprocess
import sys
from pathlib import Path

import pytest
import tomllib

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


def test_cursor_marketplace_move_preserves_newly_materialized_plugin(tmp_path):
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    ownership.write_text("plugin\tcursor\told-market\tdemo\n", encoding="utf-8")
    package = tmp_path / ".local/share/agent-plugins/marketplace/plugins/demo/cursor"
    package.mkdir(parents=True)
    (package / "plugin.json").write_text("new", encoding="utf-8")

    plugin_bridge.reconcile(
        tmp_path,
        {
            "plugin_bridge": {
                "marketplaces": {"new-market": {"hosts": ["cursor"]}},
                "plugins": {"demo": {"marketplace": "new-market", "hosts": ["cursor"]}},
            }
        },
    )

    installed = tmp_path / ".cursor/plugins/local/demo/plugin.json"
    assert installed.read_text(encoding="utf-8") == "new"
    assert ownership.read_text(encoding="utf-8") == (
        "plugin\tcursor\tnew-market\tdemo\n"
    )


def test_reconcile_rejects_symlinked_state_root_before_writing(tmp_path):
    redirected_state = tmp_path / "redirected-state"
    redirected_state.mkdir()
    state = tmp_path / ".local/state/dotfiles"
    state.parent.mkdir(parents=True)
    state.symlink_to(redirected_state, target_is_directory=True)

    with pytest.raises(plugin_bridge.BridgeError, match="state root"):
        plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert not (redirected_state / "agent-plugin-ownership").exists()


def test_reconcile_rejects_symlinked_cursor_root_before_materializing(
    tmp_path,
):
    redirected_plugins = tmp_path / "redirected-plugins"
    redirected_plugins.mkdir()
    marker = redirected_plugins / "demo/marker"
    marker.parent.mkdir()
    marker.write_text("keep", encoding="utf-8")
    cursor_root = tmp_path / ".cursor/plugins/local"
    cursor_root.parent.mkdir(parents=True)
    cursor_root.symlink_to(redirected_plugins, target_is_directory=True)
    package = tmp_path / ".local/share/agent-plugins/marketplace/plugins/demo/cursor"
    package.mkdir(parents=True)

    with pytest.raises(plugin_bridge.BridgeError, match="cursor plugin root"):
        plugin_bridge.reconcile(
            tmp_path,
            {
                "plugin_bridge": {
                    "plugins": {"demo": {"marketplace": "market", "hosts": ["cursor"]}}
                }
            },
        )

    assert marker.read_text(encoding="utf-8") == "keep"


def test_reconcile_rejects_symlinked_cursor_root_before_stale_cleanup(tmp_path):
    ownership = tmp_path / ".local/state/dotfiles/agent-plugin-ownership"
    ownership.parent.mkdir(parents=True)
    ownership.write_text("plugin\tcursor\told-market\tdemo\n", encoding="utf-8")
    redirected_plugins = tmp_path / "redirected-plugins"
    redirected_plugins.mkdir()
    marker = redirected_plugins / "demo/marker"
    marker.parent.mkdir()
    marker.write_text("keep", encoding="utf-8")
    cursor_root = tmp_path / ".cursor/plugins/local"
    cursor_root.parent.mkdir(parents=True)
    cursor_root.symlink_to(redirected_plugins, target_is_directory=True)

    with pytest.raises(plugin_bridge.BridgeError, match="cursor plugin root"):
        plugin_bridge.reconcile(tmp_path, {"plugin_bridge": {}})

    assert marker.read_text(encoding="utf-8") == "keep"


def test_reconcile_cleans_generated_package_after_plugin_materialization(
    tmp_path, monkeypatch
):
    source_dir = tmp_path / "source"
    package_source = (
        source_dir / "dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles"
    )
    package_source.joinpath("claude/dot_claude-plugin").mkdir(parents=True)
    package_source.joinpath("plugin.json.tmpl").write_text("plugin", encoding="utf-8")
    package_source.joinpath("claude/dot_claude-plugin/plugin.json.tmpl").write_text(
        "claude", encoding="utf-8"
    )
    working_tree = tmp_path / "working"
    authored_skill = working_tree / "src/ai/skills/kept"
    authored_skill.mkdir(parents=True)
    (authored_skill / "SKILL.md").write_text("authored", encoding="utf-8")
    selected_skill = working_tree / "src/ai/skills/selected"
    selected_skill.mkdir(parents=True)
    (selected_skill / "SKILL.md").write_text("selected", encoding="utf-8")
    plugin_skill = working_tree / "src/overlay-plugins/example/skills/plugin-skill"
    plugin_skill.mkdir(parents=True)
    (plugin_skill / "SKILL.md").write_text("plugin", encoding="utf-8")
    generated_root = tmp_path / ".local/share/agent-plugins/marketplace"
    package_root = generated_root / "plugins/mkobit-dotfiles"
    package_root.mkdir(parents=True)
    expected = {
        "plugin.json": "plugin",
        "claude/.claude-plugin/plugin.json": "claude",
        "skills/kept/SKILL.md": "portable",
        "claude/skills/kept/SKILL.md": "claude skill",
        "codex/skills/kept/SKILL.md": "codex skill",
        "cursor/skills/selected/SKILL.md": "cursor skill",
        "skills/plugin-skill/SKILL.md": "plugin skill",
    }
    for relative, content in expected.items():
        path = package_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    for relative in ("skills/removed/SKILL.md", "codex/skills/removed/SKILL.md"):
        stale = package_root / relative
        stale.parent.mkdir(parents=True, exist_ok=True)
        stale.write_text("stale", encoding="utf-8")
    stale = package_root / "skills/removed/SKILL.md"
    external = package_root / "skills/external"
    external.mkdir(parents=True)
    (external / "README.md").write_text("external", encoding="utf-8")

    events = []
    cleanup = plugin_bridge._cleanup_generated_package

    def cleanup_before_host_sync(*args):
        cleanup(*args)
        events.append("cleanup")

    monkeypatch.setattr(
        plugin_bridge, "_cleanup_generated_package", cleanup_before_host_sync
    )
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_marketplace",
        lambda *args: (assert_not_exists(stale), events.append("marketplace"))[1],
    )
    monkeypatch.setattr(
        plugin_bridge,
        "_ensure_plugin",
        lambda *args: (assert_not_exists(stale), events.append("plugin"))[1],
    )

    plugin_bridge.reconcile(
        tmp_path,
        {
            "plugin_bridge": {
                "generated_marketplace_root": str(generated_root),
                "marketplaces": {"dotfiles": {"hosts": ["claude"]}},
                "capabilities": {
                    "mkobit-dotfiles": {
                        "marketplace": "dotfiles",
                        "hosts": ["claude", "codex", "cursor"],
                        "authored_skill_source": "src/ai/skills",
                        "source_dir": "src/overlay-plugins/example",
                        "skills": {"plugin-skill": "present"},
                    }
                },
            },
            "skills": {
                "authored": {
                    "kept": "present",
                    "selected": "cursor",
                    "removed": "absent",
                },
                "external": {"catalog": {"skills": {"external": "present"}}},
            },
            "source_dir": str(source_dir),
            "working_tree": str(working_tree),
            "generated_marketplace_root": str(generated_root),
        },
    )

    assert events == ["cleanup", "marketplace", "plugin", "plugin", "plugin"]
    for relative in expected:
        assert (package_root / relative).exists()
    assert not (package_root / "skills/removed").exists()
    assert not (package_root / "codex/skills/removed").exists()
    assert (external / "README.md").read_text(encoding="utf-8") == "external"


def assert_not_exists(path):
    assert not path.exists()


def test_source_files_transforms_only_dot_prefix_per_path_component(tmp_path):
    root = tmp_path / "source"
    (root / "not_dot_name.tmpl").parent.mkdir(parents=True)
    (root / "not_dot_name.tmpl").write_text("keep", encoding="utf-8")
    (root / "dot_name.tmpl").write_text("hidden", encoding="utf-8")
    (root / "nested/not_dot_dir/dot_file.tmpl").parent.mkdir(parents=True)
    (root / "nested/not_dot_dir/dot_file.tmpl").write_text("nested", encoding="utf-8")

    assert plugin_bridge._source_files(root, transform_target_names=True) == [
        ".name",
        "nested/not_dot_dir/.file",
        "not_dot_name",
    ]


def test_actual_base_capability_inventory_uses_all_package_skill_destinations(
    tmp_path,
):
    base_root = Path(__file__).parents[4]
    with (base_root / "src/chezmoi/.chezmoidata/ai/plugin-bridge.toml").open(
        "rb"
    ) as config_file:
        config = tomllib.load(config_file)
    bridge = config["ai"]["plugin_bridge"]
    capability = bridge["capabilities"]["mkobit-dotfiles"]
    assert capability["hosts"] == ["claude", "codex", "cursor"]

    source_dir = tmp_path / "source"
    package_source = (
        source_dir / "dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles"
    )
    package_source.mkdir(parents=True)
    working_tree = tmp_path / "working"
    authored = working_tree / capability["authored_skill_source"] / "authored"
    authored.mkdir(parents=True)
    (authored / "SKILL.md").write_text("authored", encoding="utf-8")

    inventory = plugin_bridge._package_cleanup_inventory(
        "mkobit-dotfiles",
        capability,
        bridge["marketplaces"],
        {
            "authored": {"authored": "present"},
            "external": {"external": {"skills": {"external": "present"}}},
        },
        source_dir,
        working_tree,
        tmp_path / ".local/share/agent-plugins/marketplace",
    )

    assert inventory is not None
    assert {
        "skills/authored/SKILL.md",
        "claude/skills/authored/SKILL.md",
        "codex/skills/authored/SKILL.md",
        "cursor/skills/authored/SKILL.md",
    } <= set(inventory["expected_files"])
    assert set(inventory["preserved_directories"]) == {
        "skills/external",
        "claude/skills/external",
        "codex/skills/external",
        "cursor/skills/external",
    }


def test_external_host_specific_inventory_uses_destination_hosts(
    tmp_path,
):
    source_dir = tmp_path / "source"
    package_source = (
        source_dir / "dot_local/share/agent-plugins/marketplace/plugins/example"
    )
    package_source.mkdir(parents=True)

    inventory = plugin_bridge._package_cleanup_inventory(
        "example",
        {
            "marketplace": "dotfiles",
            "hosts": ["codex"],
            "authored_skill_source": "src/ai/skills",
        },
        {},
        {"external": {"catalog": {"skills": {"private": "claude"}}}},
        source_dir,
        tmp_path / "working",
        tmp_path / ".local/share/agent-plugins/marketplace",
    )

    assert inventory is not None
    assert inventory["preserved_directories"] == ["claude/skills/private"]


def test_actual_overlay_capability_inventory_uses_overlay_skill_states(tmp_path):
    repo_root = Path(__file__).parents[6]
    config_path = repo_root / "src/chezmoi/.chezmoidata/ai/overlay-plugin-bridge.toml"
    skills_path = repo_root / "src/chezmoi/.chezmoidata/ai/overlay-skills.toml"
    with config_path.open("rb") as config_file, skills_path.open("rb") as skills_file:
        capability = tomllib.load(config_file)["ai"]["plugin_bridge"]["capabilities"][
            "stripe-dotfiles"
        ]
        overlay_skills = tomllib.load(skills_file)["ai"]["overlay_skills"]

    source_dir = tmp_path / "source"
    package_source = (
        source_dir / "dot_local/share/agent-plugins/marketplace/plugins/stripe-dotfiles"
    )
    package_source.mkdir(parents=True)

    inventory = plugin_bridge._package_cleanup_inventory(
        "stripe-dotfiles",
        capability,
        {"dotfiles": {"hosts": ["claude", "codex", "cursor"]}},
        {},
        source_dir,
        repo_root,
        tmp_path / ".local/share/agent-plugins/marketplace",
        overlay_skills=overlay_skills,
    )

    assert inventory is not None
    expected = {
        "skills/domain-projects/SKILL.md",
        "claude/skills/domain-projects/SKILL.md",
        "codex/skills/domain-projects/SKILL.md",
        "cursor/skills/domain-projects/SKILL.md",
        "skills/writing/SKILL.md",
        "claude/skills/writing/SKILL.md",
        "codex/skills/writing/SKILL.md",
        "cursor/skills/writing/SKILL.md",
    }
    assert expected <= set(inventory["expected_files"])
    local_files = {
        f"{root}/jira-format-content/SKILL.md"
        for root in (
            "skills",
            "claude/skills",
            "codex/skills",
            "cursor/skills",
        )
    }
    if Path("/Applications/Santa.app").exists():
        assert local_files <= set(inventory["expected_files"])
    else:
        assert local_files.isdisjoint(inventory["expected_files"])


def test_actual_overlay_capability_declares_all_package_hosts():
    repo_root = Path(__file__).parents[6]
    config_path = repo_root / "src/chezmoi/.chezmoidata/ai/overlay-plugin-bridge.toml"
    with config_path.open("rb") as config_file:
        capability = tomllib.load(config_file)["ai"]["plugin_bridge"]["capabilities"][
            "stripe-dotfiles"
        ]

    assert capability["hosts"] == ["claude", "codex", "cursor"]


@pytest.mark.parametrize(
    "cleanup,match",
    [
        (
            {
                "stable_key": "mkobit-dotfiles",
                "root": "{generated}/plugins/other",
                "expected_files": [],
            },
            "outside generated marketplace root",
        ),
        (
            {
                "stable_key": "mkobit-dotfiles",
                "root": "{generated}/plugins/mkobit-dotfiles",
                "expected_files": ["../escape"],
            },
            "unsafe",
        ),
    ],
)
def test_reconcile_rejects_unsafe_package_cleanup_inventory(
    tmp_path, cleanup, match, monkeypatch
):
    generated_root = tmp_path / ".local/share/agent-plugins/marketplace"
    package_root = generated_root / "plugins/mkobit-dotfiles"
    package_root.mkdir(parents=True)
    cleanup = {
        key: value.replace("{generated}", str(generated_root))
        if isinstance(value, str)
        else value
        for key, value in cleanup.items()
    }
    monkeypatch.setattr(plugin_bridge, "_ensure_plugin", lambda *args: None)

    with pytest.raises(plugin_bridge.BridgeError, match=match):
        plugin_bridge.reconcile(
            tmp_path,
            {
                "plugin_bridge": {
                    "generated_marketplace_root": str(generated_root),
                    "capabilities": {
                        "mkobit-dotfiles": {
                            "marketplace": "dotfiles",
                            "package_cleanup": cleanup,
                        }
                    },
                }
            },
        )


def test_reconcile_rejects_symlinked_generated_package_ancestor(tmp_path, monkeypatch):
    generated_root = tmp_path / ".local/share/agent-plugins/marketplace"
    redirected = tmp_path / "redirected"
    redirected.mkdir()
    generated_root.parent.mkdir(parents=True)
    generated_root.symlink_to(redirected, target_is_directory=True)
    monkeypatch.setattr(plugin_bridge, "_ensure_plugin", lambda *args: None)

    with pytest.raises(plugin_bridge.BridgeError, match="symlink"):
        plugin_bridge.reconcile(
            tmp_path,
            {
                "plugin_bridge": {
                    "generated_marketplace_root": str(generated_root),
                    "capabilities": {
                        "mkobit-dotfiles": {
                            "marketplace": "dotfiles",
                            "package_cleanup": {
                                "stable_key": "mkobit-dotfiles",
                                "root": str(generated_root / "plugins/mkobit-dotfiles"),
                                "expected_files": [],
                            },
                        }
                    },
                }
            },
        )


def test_reconcile_rejects_expected_package_symlink(tmp_path, monkeypatch):
    generated_root = tmp_path / ".local/share/agent-plugins/marketplace"
    package_root = generated_root / "plugins/mkobit-dotfiles"
    package_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.write_text("outside", encoding="utf-8")
    (package_root / "plugin.json").symlink_to(outside)
    monkeypatch.setattr(plugin_bridge, "_ensure_plugin", lambda *args: None)

    with pytest.raises(plugin_bridge.BridgeError, match="expected file is a symlink"):
        plugin_bridge.reconcile(
            tmp_path,
            {
                "plugin_bridge": {
                    "generated_marketplace_root": str(generated_root),
                    "capabilities": {
                        "mkobit-dotfiles": {
                            "marketplace": "dotfiles",
                            "package_cleanup": {
                                "stable_key": "mkobit-dotfiles",
                                "root": str(package_root),
                                "expected_files": ["plugin.json"],
                            },
                        }
                    },
                }
            },
        )


def test_enabled_claude_plugin_is_not_enabled_again(tmp_path, monkeypatch):
    calls = []

    def run(host, *args):
        calls.append((host, *args))
        if args == ("plugin", "list", "--json"):
            return '[{"id":"demo@market","enabled":true}]'
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)

    plugin_bridge._ensure_plugin(
        "claude",
        "market",
        "demo",
        tmp_path,
        tmp_path / "ownership",
        set(),
        set(),
    )

    assert ("claude", "plugin", "enable", "demo@market") not in calls


def test_claude_plugin_update_rechecks_enabled_state(tmp_path, monkeypatch):
    calls = []
    enabled = True

    def run(host, *args):
        nonlocal enabled
        calls.append((host, *args))
        if args == ("plugin", "list", "--json"):
            return json.dumps([{"id": "demo@market", "enabled": enabled}])
        if args == ("plugin", "update", "demo@market"):
            enabled = False
        if args == ("plugin", "enable", "demo@market"):
            enabled = True
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)

    plugin_bridge._ensure_plugin(
        "claude",
        "market",
        "demo",
        tmp_path,
        tmp_path / "ownership",
        set(),
        set(),
    )

    assert ("claude", "plugin", "enable", "demo@market") in calls


def test_disabled_claude_plugin_must_be_enabled(tmp_path, monkeypatch):
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

    plugin_bridge._ensure_plugin(
        "claude",
        "market",
        "demo",
        tmp_path,
        tmp_path / "ownership",
        set(),
        set(),
    )

    assert ("claude", "plugin", "enable", "demo@market") in calls


def test_claude_plugin_reconciliation_rejects_disabled_final_state(
    tmp_path, monkeypatch
):
    calls = []

    def run(host, *args):
        calls.append((host, *args))
        if args == ("plugin", "list", "--json"):
            return '[{"id":"demo@market","enabled":false}]'
        return ""

    monkeypatch.setattr(plugin_bridge, "_run", run)

    with pytest.raises(
        plugin_bridge.BridgeError,
        match="plugin did not become available and enabled: demo@market",
    ):
        plugin_bridge._ensure_plugin(
            "claude",
            "market",
            "demo",
            tmp_path,
            tmp_path / "ownership",
            set(),
            set(),
        )

    assert ("claude", "plugin", "enable", "demo@market") in calls


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


def test_migrate_ownership_resolves_legacy_cursor_plugin_from_declaration(tmp_path):
    legacy = tmp_path / "ownership.json"
    legacy.write_text(
        json.dumps(
            {
                "resources": [
                    {"kind": "plugin", "host": "cursor", "id": "demo"},
                ]
            }
        )
    )

    result = plugin_bridge.migrate_ownership(legacy, {("cursor", "demo"): "market"})

    assert result == "plugin\tcursor\tmarket\tdemo\n"


def test_migrate_ownership_keeps_non_cursor_bare_plugin_ids_invalid(tmp_path):
    legacy = tmp_path / "ownership.json"
    legacy.write_text(
        json.dumps(
            {
                "resources": [
                    {"kind": "plugin", "host": "claude", "id": "demo"},
                ]
            }
        )
    )

    with pytest.raises(ValueError, match="invalid legacy plugin identity"):
        plugin_bridge.migrate_ownership(legacy)


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
