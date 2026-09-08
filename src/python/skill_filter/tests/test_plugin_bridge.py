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


def rendered_plan(
    resources,
    *,
    skill_mappings=(),
    legacy_cleanup=None,
    owned_removals=None,
):
    plan = {
        "version": 1,
        "resources": list(resources),
        "skill_mappings": list(skill_mappings),
        "legacy_cleanup": legacy_cleanup,
    }
    if owned_removals is not None:
        plan["owned_removals"] = list(owned_removals)
    return json.dumps(plan)


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


def removal_preview(resource):
    return {
        "action": "uninstall",
        "kind": resource["kind"],
        "host": resource["host"],
        "id": resource["id"],
        "argv": resource["uninstall"],
    }


def legacy_cleanup(tmp_path, *, prior=(), desired=()):
    state_manifest = tmp_path / ".local/state/dotfiles/skill-roots.manifest"
    if prior:
        state_manifest.parent.mkdir(parents=True, exist_ok=True)
        state_manifest.write_text(
            "".join(f"{root}\n" for root in prior), encoding="utf-8"
        )
    return {
        "dest_dir": str(tmp_path),
        "state_manifest": str(state_manifest),
        "desired_manifest": "".join(f"{root}\n" for root in desired),
    }


class TestPluginPlanning:
    def test_rejects_duplicate_desired_resource_identities(self):
        parse_plan = bridge_helper("parse_plugin_plan")
        resources = [
            plugin("claude", "bridge@dotfiles", ["brainstorming"]),
            plugin(
                "claude",
                "bridge@dotfiles",
                ["writing"],
                fingerprint="plugin-v2",
            ),
        ]

        with pytest.raises(
            MAIN_MODULE.FilterError, match="duplicate desired resource identity"
        ):
            parse_plan(rendered_plan(resources))

    @pytest.mark.parametrize(
        ("resource", "message"),
        [
            (
                {
                    **plugin("claude", "bridge@dotfiles", ["brainstorming"]),
                    "adopt": "yes",
                },
                "adopt marker must be a boolean",
            ),
            (
                {**marketplace("claude", "dotfiles"), "adopt": True},
                "only plugin resources can be adopted",
            ),
        ],
        ids=["non-boolean", "unverifiable-marketplace"],
    )
    def test_rejects_invalid_adoption_markers(self, resource, message):
        parse_plan = bridge_helper("parse_plugin_plan")

        with pytest.raises(MAIN_MODULE.FilterError, match=message):
            parse_plan(rendered_plan([resource]))

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
    def test_rejects_mismatched_owned_removal_preview_before_host_execution(self, tmp_path):
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        ownership_file.parent.mkdir(parents=True)
        owned_resource = plugin("claude", "obsolete@dotfiles", ["old"])
        ownership_file.write_text(
            json.dumps({"version": 1, "resources": [owned_resource]}),
            encoding="utf-8",
        )
        plan = parse_plan(
            rendered_plan(
                [],
                owned_removals=[
                    {
                        **removal_preview(owned_resource),
                        "argv": ["claude", "plugin", "uninstall", "wrong@dotfiles"],
                    }
                ],
            )
        )
        executed = []

        with pytest.raises(MAIN_MODULE.FilterError, match="owned removal preview"):
            reconcile(tmp_path, ownership_file, plan, executed.append, lambda _: None)

        assert executed == []

    def test_adopts_verified_existing_plugin_without_installing(self, tmp_path):
        parse_plan = bridge_helper("parse_plugin_plan")
        parse_ownership = bridge_helper("parse_plugin_ownership")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        resource = plugin("claude", "bridge@dotfiles", ["brainstorming"])
        resource["adopt"] = True
        plan = parse_plan(rendered_plan([resource]))
        actions = []

        def execute(operation):
            actions.append(operation.action)
            return ("brainstorming",) if operation.action == "adopt" else ()

        reconcile(tmp_path, ownership_file, plan, execute, lambda _: None)

        assert actions == ["adopt"]
        (owned,) = parse_ownership(ownership_file.read_text(encoding="utf-8"))
        assert (owned.kind, owned.host, owned.resource_id) == (
            "plugin",
            "claude",
            "bridge@dotfiles",
        )

    def test_failed_adoption_verification_does_not_record_ownership(self, tmp_path):
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        resource = plugin("claude", "bridge@dotfiles", ["brainstorming"])
        resource["adopt"] = True
        plan = parse_plan(rendered_plan([resource]))

        with pytest.raises(MAIN_MODULE.FilterError, match="expected"):
            reconcile(
                tmp_path,
                ownership_file,
                plan,
                lambda operation: ("unexpected",),
                lambda _: None,
            )

        assert json.loads(ownership_file.read_text(encoding="utf-8")) == {
            "resources": [],
            "version": 1,
        }

    @pytest.mark.parametrize(
        "mapping",
        [
            None,
            {
                "legacy_root": ".claude/skills/brainstorming",
                "host": "claude",
                "plugin": "other@dotfiles",
                "skill": "brainstorming",
            },
            {
                "legacy_root": ".claude/skills/brainstorming",
                "host": "claude",
                "plugin": "bridge@dotfiles",
                "skill": "missing",
            },
        ],
        ids=["missing", "wrong-plugin", "missing-expected-skill"],
    )
    def test_rejects_unmapped_legacy_cleanup_before_host_execution(
        self, tmp_path, mapping
    ):
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        cleanup_state = tmp_path / ".local/state/dotfiles/skill-roots.manifest"
        cleanup_state.parent.mkdir(parents=True)
        cleanup_state.write_text(".claude/skills/brainstorming\n", encoding="utf-8")
        cleanup_plan = {
            "dest_dir": str(tmp_path),
            "state_manifest": str(cleanup_state),
            "desired_manifest": "",
        }
        mappings = [] if mapping is None else [mapping]
        executed = []

        with pytest.raises(MAIN_MODULE.FilterError, match="legacy cleanup mapping"):
            plan = parse_plan(
                rendered_plan(
                    [plugin("claude", "bridge@dotfiles", ["brainstorming"])],
                    skill_mappings=mappings,
                    legacy_cleanup=cleanup_plan,
                )
            )
            reconcile(
                tmp_path,
                ownership_file,
                plan,
                lambda operation: executed.append(operation),
                lambda _: None,
            )

        assert executed == []

    def test_allows_direct_antigravity_cleanup_without_a_plugin_mapping(self, tmp_path):
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        legacy_root = ".gemini/antigravity-cli/skills/retired"
        stale_skill = tmp_path / legacy_root
        stale_skill.mkdir(parents=True)
        (stale_skill / "SKILL.md").write_text("# retired\n", encoding="utf-8")
        cleanup_plan = legacy_cleanup(tmp_path, prior=(legacy_root,))
        cleanup_plan["direct_roots"] = [legacy_root]
        plan = parse_plan(rendered_plan([], legacy_cleanup=cleanup_plan))

        reconcile(
            tmp_path,
            ownership_file,
            plan,
            lambda _: (),
            MAIN_MODULE._cleanup_legacy_skill_roots,
        )

        assert not stale_skill.exists()
        assert (
            tmp_path / ".local/state/dotfiles/skill-roots.manifest"
        ).read_text(encoding="utf-8") == ""

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
                skill_mappings=[
                    {
                        "legacy_root": ".claude/skills/brainstorming",
                        "host": "claude",
                        "plugin": "bridge@dotfiles",
                        "skill": "brainstorming",
                    }
                ],
                legacy_cleanup=legacy_cleanup(
                    tmp_path, prior=(".claude/skills/brainstorming",)
                ),
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
            events.append(("cleanup", cleanup_plan["state_manifest"]))

        reconcile(tmp_path, ownership_file, plan, execute, cleanup)

        assert events == [
            ("install", "marketplace", "claude", "dotfiles"),
            ("install", "plugin", "claude", "bridge@dotfiles"),
            ("verify", "plugin", "claude", "bridge@dotfiles"),
            (
                "cleanup",
                str(tmp_path / ".local/state/dotfiles/skill-roots.manifest"),
            ),
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
                skill_mappings=[
                    {
                        "legacy_root": ".claude/skills/brainstorming",
                        "host": "claude",
                        "plugin": "bridge@dotfiles",
                        "skill": "brainstorming",
                    }
                ],
                legacy_cleanup=legacy_cleanup(
                    tmp_path, prior=(".claude/skills/brainstorming",)
                ),
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
                legacy_cleanup=legacy_cleanup(tmp_path),
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

    def test_cleanup_failure_records_successfully_verified_installs(self, tmp_path):
        parse_plan = bridge_helper("parse_plugin_plan")
        parse_ownership = bridge_helper("parse_plugin_ownership")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        cleanup_state = tmp_path / ".local/state/dotfiles/skill-roots.manifest"
        cleanup_plan = {
            "dest_dir": str(tmp_path),
            "state_manifest": str(cleanup_state),
            "desired_manifest": "",
        }
        plan = parse_plan(
            rendered_plan(
                [plugin("claude", "bridge@dotfiles", ["brainstorming"])],
                legacy_cleanup=cleanup_plan,
            )
        )

        def execute(operation):
            return ("brainstorming",) if operation.action == "verify" else ()

        def fail_cleanup(_cleanup_plan):
            raise OSError("cleanup failed")

        with pytest.raises(OSError, match="cleanup failed"):
            reconcile(tmp_path, ownership_file, plan, execute, fail_cleanup)

        (owned,) = parse_ownership(ownership_file.read_text(encoding="utf-8"))
        assert (owned.kind, owned.host, owned.resource_id) == (
            "plugin",
            "claude",
            "bridge@dotfiles",
        )

    def test_uninstall_failure_records_prior_successful_removals(self, tmp_path):
        parse_plan = bridge_helper("parse_plugin_plan")
        parse_ownership = bridge_helper("parse_plugin_ownership")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        ownership_file.parent.mkdir(parents=True)
        ownership_file.write_text(
            json.dumps(
                {
                    "version": 1,
                    "resources": [
                        plugin("claude", "first@dotfiles", ["first"]),
                        plugin("claude", "second@dotfiles", ["second"]),
                    ],
                }
            ),
            encoding="utf-8",
        )
        plan = parse_plan(rendered_plan([]))

        def execute(operation):
            if operation.resource_id == "second@dotfiles":
                raise OSError("uninstall failed")
            return ()

        with pytest.raises(OSError, match="uninstall failed"):
            reconcile(tmp_path, ownership_file, plan, execute, lambda _: None)

        (owned,) = parse_ownership(ownership_file.read_text(encoding="utf-8"))
        assert owned.resource_id == "second@dotfiles"

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
