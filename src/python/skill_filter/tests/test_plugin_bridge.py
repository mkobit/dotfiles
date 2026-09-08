from __future__ import annotations

import importlib
import io
import json
import os

import pytest

MAIN_MODULE = importlib.import_module("skill_filter.main")


def bridge_helper(name: str):
    helper = getattr(MAIN_MODULE, name, None)
    assert helper is not None, f"{name} is not implemented"
    return helper


def rendered_plan(resources, *, skill_mappings=(), legacy_cleanup=None):
    return json.dumps(
        {
            "version": 1,
            "resources": list(resources),
            "skill_mappings": list(skill_mappings),
            "legacy_cleanup": legacy_cleanup,
        }
    )


def marketplace(host: str, resource_id: str, fingerprint: str = "market-v1"):
    return {
        "kind": "marketplace",
        "host": host,
        "id": resource_id,
        "fingerprint": fingerprint,
        "install": [host, "marketplace", "add", resource_id],
        "uninstall": [host, "marketplace", "remove", resource_id],
    }


def plugin(
    host: str,
    resource_id: str,
    skills: list[str],
    fingerprint: str = "plugin-v1",
):
    return {
        "kind": "plugin",
        "host": host,
        "id": resource_id,
        "fingerprint": fingerprint,
        "install": [host, "plugin", "install", resource_id],
        "uninstall": [host, "plugin", "uninstall", resource_id],
        "verify": [host, "plugin", "skills", resource_id, "--json"],
        "expected_skills": skills,
    }


def operation_keys(operations):
    return [
        (operation.action, operation.kind, operation.host, operation.resource_id)
        for operation in operations
    ]


class TestPluginPlanning:
    def test_desired_resources_have_deterministic_install_order(self):
        parse_plan = bridge_helper("parse_plugin_plan")
        plan_operations = bridge_helper("plan_plugin_operations")
        resources = [
            plugin("cursor", "bridge", ["writing"]),
            marketplace("claude", "dotfiles"),
            plugin("claude", "bridge@dotfiles", ["brainstorming"]),
            marketplace("cursor", "dotfiles"),
        ]

        forward = plan_operations(parse_plan(rendered_plan(resources)), ())
        reverse = plan_operations(parse_plan(rendered_plan(reversed(resources))), ())

        expected = [
            ("install", "marketplace", "claude", "dotfiles"),
            ("install", "marketplace", "cursor", "dotfiles"),
            ("install", "plugin", "claude", "bridge@dotfiles"),
            ("install", "plugin", "cursor", "bridge"),
        ]
        assert operation_keys(forward) == expected
        assert operation_keys(reverse) == expected

    def test_plans_install_update_and_owned_uninstall_deltas(self):
        parse_plan = bridge_helper("parse_plugin_plan")
        parse_ownership = bridge_helper("parse_plugin_ownership")
        plan_operations = bridge_helper("plan_plugin_operations")
        desired = parse_plan(
            rendered_plan(
                [
                    marketplace("claude", "dotfiles"),
                    plugin(
                        "claude",
                        "bridge@dotfiles",
                        ["brainstorming"],
                        fingerprint="plugin-v2",
                    ),
                    plugin("cursor", "bridge", ["writing"]),
                ]
            )
        )
        owned = parse_ownership(
            json.dumps(
                {
                    "version": 1,
                    "resources": [
                        marketplace("claude", "dotfiles"),
                        plugin(
                            "claude",
                            "bridge@dotfiles",
                            ["brainstorming"],
                            fingerprint="plugin-v1",
                        ),
                        plugin("claude", "obsolete@dotfiles", ["old"]),
                        marketplace("claude", "obsolete-market"),
                    ],
                }
            )
        )

        operations = plan_operations(desired, owned)

        assert operation_keys(operations) == [
            ("install", "plugin", "claude", "bridge@dotfiles"),
            ("install", "plugin", "cursor", "bridge"),
            ("uninstall", "plugin", "claude", "obsolete@dotfiles"),
            ("uninstall", "marketplace", "claude", "obsolete-market"),
        ]

    @pytest.mark.parametrize(
        "mappings",
        [
            [
                {
                    "legacy_root": ".claude/skills/brainstorming",
                    "host": "claude",
                    "plugin": "bridge@dotfiles",
                    "skill": "brainstorming",
                },
                {
                    "legacy_root": ".claude/skills/brainstorming",
                    "host": "claude",
                    "plugin": "other@dotfiles",
                    "skill": "brainstorming",
                },
            ],
            [
                {
                    "legacy_root": ".claude/skills/brainstorming",
                    "host": "claude",
                    "plugin": "bridge@dotfiles",
                    "skill": "brainstorming",
                },
                {
                    "legacy_root": ".claude/skills/brainstorming-copy",
                    "host": "claude",
                    "plugin": "bridge@dotfiles",
                    "skill": "brainstorming",
                },
            ],
        ],
        ids=["multiple-replacements", "duplicate-replacement-identity"],
    )
    def test_rejects_ambiguous_skill_mappings(self, mappings):
        parse_plan = bridge_helper("parse_plugin_plan")

        with pytest.raises(MAIN_MODULE.FilterError, match="ambiguous skill mapping"):
            parse_plan(rendered_plan([], skill_mappings=mappings))


class TestPluginOwnership:
    def test_parses_owned_resources_needed_for_future_removal(self):
        parse_ownership = bridge_helper("parse_plugin_ownership")
        content = json.dumps(
            {
                "version": 1,
                "resources": [
                    {
                        "kind": "plugin",
                        "host": "claude",
                        "id": "bridge@dotfiles",
                        "fingerprint": "plugin-v1",
                        "uninstall": [
                            "claude",
                            "plugin",
                            "uninstall",
                            "bridge@dotfiles",
                        ],
                    }
                ],
            }
        )

        (owned,) = parse_ownership(content)

        assert owned.kind == "plugin"
        assert owned.host == "claude"
        assert owned.resource_id == "bridge@dotfiles"
        assert owned.fingerprint == "plugin-v1"
        assert owned.uninstall == (
            "claude",
            "plugin",
            "uninstall",
            "bridge@dotfiles",
        )

    def test_failed_atomic_update_preserves_prior_ownership(
        self, tmp_path, monkeypatch
    ):
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/agent-plugin-ownership.json"
        ownership_file.parent.mkdir(parents=True)
        prior = json.dumps(
            {"version": 1, "resources": [marketplace("claude", "dotfiles")]}
        )
        ownership_file.write_text(prior, encoding="utf-8")
        plan = parse_plan(rendered_plan([marketplace("claude", "dotfiles")]))

        def fail_replace(src, dst):
            raise OSError("replace failed")

        monkeypatch.setattr(os, "replace", fail_replace)

        with pytest.raises(OSError, match="replace failed"):
            reconcile(
                tmp_path, ownership_file, plan, lambda operation: (), lambda _: None
            )

        assert ownership_file.read_text(encoding="utf-8") == prior
        assert [path.name for path in ownership_file.parent.iterdir()] == [
            ownership_file.name
        ]


class TestPluginReconciliation:
    def test_verifies_before_cleanup_and_preserves_unmanaged_plugins(self, tmp_path):
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/agent-plugin-ownership.json"
        ownership_file.parent.mkdir(parents=True)
        ownership_file.write_text(
            json.dumps(
                {
                    "version": 1,
                    "resources": [plugin("claude", "obsolete@dotfiles", ["old"])],
                }
            ),
            encoding="utf-8",
        )
        plan = parse_plan(
            rendered_plan(
                [
                    marketplace("claude", "dotfiles"),
                    plugin("claude", "bridge@dotfiles", ["brainstorming"]),
                ],
                legacy_cleanup={"manifest": "legacy-roots"},
            )
        )
        events = []
        installed_plugins = {"unmanaged@personal", "obsolete@dotfiles"}

        def execute(operation):
            events.append(
                (
                    operation.action,
                    operation.kind,
                    operation.host,
                    operation.resource_id,
                )
            )
            if operation.action == "install" and operation.kind == "plugin":
                installed_plugins.add(operation.resource_id)
            if operation.action == "verify":
                return ("brainstorming",)
            if operation.action == "uninstall" and operation.kind == "plugin":
                installed_plugins.remove(operation.resource_id)
            return ()

        def cleanup(cleanup_plan):
            events.append(("cleanup", cleanup_plan["manifest"]))

        reconcile(tmp_path, ownership_file, plan, execute, cleanup)

        assert events == [
            ("install", "marketplace", "claude", "dotfiles"),
            ("install", "plugin", "claude", "bridge@dotfiles"),
            ("verify", "plugin", "claude", "bridge@dotfiles"),
            ("cleanup", "legacy-roots"),
            ("uninstall", "plugin", "claude", "obsolete@dotfiles"),
        ]
        assert installed_plugins == {"unmanaged@personal", "bridge@dotfiles"}

    def test_skill_verification_failure_preserves_legacy_and_ownership(self, tmp_path):
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/agent-plugin-ownership.json"
        ownership_file.parent.mkdir(parents=True)
        prior = json.dumps({"version": 1, "resources": []})
        ownership_file.write_text(prior, encoding="utf-8")
        plan = parse_plan(
            rendered_plan(
                [plugin("claude", "bridge@dotfiles", ["brainstorming"])],
                legacy_cleanup={"manifest": "legacy-roots"},
            )
        )
        cleaned = []

        def execute(operation):
            if operation.action == "verify":
                return ("unexpected-skill",)
            return ()

        with pytest.raises(MAIN_MODULE.FilterError, match="expected"):
            reconcile(
                tmp_path,
                ownership_file,
                plan,
                execute,
                cleaned.append,
            )

        assert cleaned == []
        assert ownership_file.read_text(encoding="utf-8") == prior

    def test_install_failure_records_only_prior_successes(self, tmp_path):
        parse_plan = bridge_helper("parse_plugin_plan")
        parse_ownership = bridge_helper("parse_plugin_ownership")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/agent-plugin-ownership.json"
        plan = parse_plan(
            rendered_plan(
                [
                    marketplace("claude", "dotfiles"),
                    plugin("claude", "bridge@dotfiles", ["brainstorming"]),
                ],
                legacy_cleanup={"manifest": "legacy-roots"},
            )
        )
        cleaned = []

        def execute(operation):
            if operation.resource_id == "bridge@dotfiles":
                raise OSError("install failed")
            return ()

        with pytest.raises(OSError, match="install failed"):
            reconcile(
                tmp_path,
                ownership_file,
                plan,
                execute,
                cleaned.append,
            )

        assert cleaned == []
        assert [
            (resource.kind, resource.host, resource.resource_id)
            for resource in parse_ownership(ownership_file.read_text(encoding="utf-8"))
        ] == [("marketplace", "claude", "dotfiles")]

    def test_reconcile_plugins_command_accepts_injected_host_executor(
        self, tmp_path, monkeypatch
    ):
        ownership_file = tmp_path / ".local/state/dotfiles/agent-plugin-ownership.json"
        plan = rendered_plan([plugin("claude", "bridge@dotfiles", ["brainstorming"])])
        monkeypatch.setattr("sys.stdin", io.StringIO(plan))
        actions = []

        def execute(operation):
            actions.append(operation.action)
            return ("brainstorming",) if operation.action == "verify" else ()

        result = MAIN_MODULE.main(
            [
                "reconcile-plugins",
                "--dest-dir",
                str(tmp_path),
                "--ownership-file",
                str(ownership_file),
            ],
            plugin_executor=execute,
            legacy_cleaner=lambda _: None,
        )

        assert result == 0
        assert actions == ["install", "verify"]
