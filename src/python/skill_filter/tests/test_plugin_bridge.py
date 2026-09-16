from __future__ import annotations

import importlib
import io
import json
import os
import subprocess
from pathlib import Path

import pytest

MAIN_MODULE = importlib.import_module("skill_filter.main")
BASE_ROOT = Path(__file__).resolve().parents[4]
BASE_TEMPLATE = BASE_ROOT / "src/chezmoi/.chezmoitemplates/ai/plugin-bridge-plan"


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


def rendered_v2_plan(resources, *, owned_removals=None):
    plan = {
        "version": 2,
        "resources": list(resources),
        "skill_mappings": [],
        "legacy_cleanup": None,
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
        "update": [host, "marketplace", "update", resource_id],
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
        "update": [host, "plugin", "update", resource_id],
        "uninstall": [host, "plugin", "uninstall", resource_id],
        "status": [host, "plugin", "status", resource_id, "--json"],
        "verify": [host, "plugin", "skills", resource_id, "--json"],
        "expected_skills": skills,
    }


def plugin_v2(host: str, resource_id: str, skills: list[str], fingerprint="plugin-v1"):
    return {
        **plugin(host, resource_id, skills, fingerprint),
        "marketplace": resource_id.rsplit("@", 1)[-1],
        "order": 200,
        "enable": ["bridge", "plugin-enable", host, resource_id],
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


def render_declaration_plan(data, destination):
    return subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(BASE_ROOT),
            "--destination",
            str(destination),
            "--override-data",
            json.dumps(data),
            "execute-template",
            "--file",
            str(BASE_TEMPLATE),
        ],
        capture_output=True,
        check=False,
        text=True,
    )


def render_adapter(template: Path, data, destination):
    return subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(BASE_ROOT),
            "--destination",
            str(destination),
            "--override-data",
            json.dumps(data),
            "execute-template",
            "--file",
            str(template),
        ],
        capture_output=True,
        check=False,
        text=True,
    )


def executable(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


def declaration_data(*, marketplaces=None, plugins=None, capabilities=None):
    return {
        "ai": {
            "plugin_bridge": {
                "environment": "local",
                "marketplaces": marketplaces or {},
                "plugins": plugins or {},
                "capabilities": capabilities or {},
            }
        }
    }


def example_marketplace(**overrides):
    declaration = {
        "source_type": "generated",
        "trust_class": "owned",
        "hosts": ["claude", "codex", "cursor"],
        "order": 100,
    }
    declaration.update(overrides)
    return declaration


def example_plugin(**overrides):
    declaration = {
        "marketplace": "dotfiles",
        "hosts": ["claude", "codex"],
        "environments": ["local", "mydev", "mydata"],
        "order": 200,
    }
    declaration.update(overrides)
    return declaration


class TestPluginBridgeDeclarations:
    def test_renders_version_two_resources_from_keyed_declarations(self, tmp_path):
        result = render_declaration_plan(
            declaration_data(
                marketplaces={"dotfiles": example_marketplace()},
                plugins={"example": example_plugin()},
            ),
            tmp_path,
        )

        assert result.returncode == 0, result.stderr
        plan = json.loads(result.stdout)
        resources = [
            resource
            for resource in plan["resources"]
            if resource["stable_key"] in {"dotfiles", "example"}
        ]
        assert plan["version"] == 2
        assert [
            (resource["kind"], resource["stable_key"], resource["host"])
            for resource in resources
        ] == [
            ("marketplace", "dotfiles", "claude"),
            ("marketplace", "dotfiles", "codex"),
            ("marketplace", "dotfiles", "cursor"),
            ("plugin", "example", "claude"),
            ("plugin", "example", "codex"),
        ]
        assert plan["skill_mappings"] == []
        assert plan["legacy_cleanup"]["direct_roots"] == []
        assert plan["owned_removals"] == []

    def test_orders_same_phase_and_order_by_stable_key_then_host(self, tmp_path):
        result = render_declaration_plan(
            declaration_data(
                marketplaces={
                    "zeta": example_marketplace(order=100),
                    "alpha": example_marketplace(order=100),
                },
                plugins={
                    "zeta-plugin": example_plugin(order=200),
                    "alpha-plugin": example_plugin(order=200),
                },
            ),
            tmp_path,
        )

        assert result.returncode == 0, result.stderr
        resources = json.loads(result.stdout)["resources"]
        assert [
            (resource["stable_key"], resource["host"])
            for resource in resources
            if resource["kind"] == "marketplace"
            and resource["stable_key"] in {"alpha", "zeta"}
        ] == [
            ("alpha", "claude"),
            ("alpha", "codex"),
            ("alpha", "cursor"),
            ("zeta", "claude"),
            ("zeta", "codex"),
            ("zeta", "cursor"),
        ]
        assert [
            (resource["stable_key"], resource["host"])
            for resource in resources
            if resource["kind"] == "plugin"
            and resource["stable_key"] in {"alpha-plugin", "zeta-plugin"}
        ] == [
            ("alpha-plugin", "claude"),
            ("alpha-plugin", "codex"),
            ("zeta-plugin", "claude"),
            ("zeta-plugin", "codex"),
        ]
        assert all(
            resource["phase"] == 10
            for resource in resources
            if resource["kind"] == "marketplace"
        )
        assert all(
            resource["phase"] == 30
            for resource in resources
            if resource["kind"] == "plugin"
            and resource["stable_key"] in {"alpha-plugin", "zeta-plugin"}
        )

    @pytest.mark.parametrize(
        ("marketplace", "plugin", "message"),
        [
            (
                example_marketplace(),
                example_plugin(marketplace="missing"),
                "marketplace",
            ),
            (example_marketplace(hosts=[]), example_plugin(), "hosts"),
            (example_marketplace(), example_plugin(hosts=[]), "hosts"),
            (example_marketplace(), example_plugin(environments=[]), "environments"),
            (
                example_marketplace(source_type=""),
                example_plugin(),
                "source_type",
            ),
            (
                example_marketplace(source_type="internal"),
                example_plugin(),
                "source_locator",
            ),
            (example_marketplace(order=-1), example_plugin(), "order"),
            (example_marketplace(order=1_000_000_000), example_plugin(), "order"),
            (example_marketplace(order="100"), example_plugin(), "order"),
        ],
        ids=[
            "unknown-marketplace",
            "empty-marketplace-hosts",
            "empty-plugin-hosts",
            "empty-plugin-environments",
            "empty-source-type",
            "missing-explicit-source-locator",
            "negative-order",
            "order-out-of-range",
            "non-integer-order",
        ],
    )
    def test_rejects_invalid_keyed_declarations_during_rendering(
        self, tmp_path, marketplace, plugin, message
    ):
        result = render_declaration_plan(
            declaration_data(
                marketplaces={"dotfiles": marketplace},
                plugins={"example": plugin},
            ),
            tmp_path,
        )

        assert result.returncode != 0
        assert message in result.stderr


class TestPluginBridgeDeclarationPolicies:
    def test_generated_marketplace_uses_configurable_filesystem_locator(self, tmp_path):
        data = declaration_data(
            marketplaces={"generated": example_marketplace(hosts=["codex"])},
        )
        result = render_declaration_plan(data, tmp_path)

        assert result.returncode == 0, result.stderr
        resource = json.loads(result.stdout)["resources"][0]
        default_locator = str(tmp_path / ".local/share/agent-plugins/marketplace")
        assert resource["source_locator"] == default_locator
        assert resource["install"][-1] == default_locator
        assert resource["update"][-1] == default_locator

        configured_locator = str(tmp_path / "rendered-marketplace")
        data["ai"]["plugin_bridge"]["generated_marketplace_root"] = configured_locator
        result = render_declaration_plan(data, tmp_path)

        assert result.returncode == 0, result.stderr
        resource = json.loads(result.stdout)["resources"][0]
        assert resource["source_locator"] == configured_locator
        assert resource["install"][-1] == configured_locator
        assert resource["update"][-1] == configured_locator

    def test_renders_generic_explicit_marketplace_sources(self, tmp_path):
        result = render_declaration_plan(
            declaration_data(
                marketplaces={
                    "internal": example_marketplace(
                        source_type="internal",
                        source_locator="corp://internal-marketplace",
                        trust_class="managed",
                        update_policy="pinned",
                    ),
                    "public": example_marketplace(
                        source_type="reviewed-public",
                        source_locator="https://example.invalid/marketplace",
                        trust_class="reviewed",
                    ),
                }
            ),
            tmp_path,
        )

        assert result.returncode == 0, result.stderr
        resources = json.loads(result.stdout)["resources"]
        internal = next(
            resource for resource in resources if resource["stable_key"] == "internal"
        )
        public = next(
            resource for resource in resources if resource["stable_key"] == "public"
        )
        assert internal["source_locator"] == "corp://internal-marketplace"
        assert internal["update_policy"] == "pinned"
        assert internal["install"][-1] == "corp://internal-marketplace"
        assert public["source_type"] == "reviewed-public"
        assert public["install"][-1] == "https://example.invalid/marketplace"

    def test_host_provided_marketplace_is_discovered_and_verified(self, tmp_path):
        result = render_declaration_plan(
            declaration_data(
                marketplaces={
                    "managed": example_marketplace(source_type="host-provided")
                }
            ),
            tmp_path,
        )

        assert result.returncode == 0, result.stderr
        resource = next(
            resource
            for resource in json.loads(result.stdout)["resources"]
            if resource["stable_key"] == "managed"
        )
        assert resource["install"][1] == "marketplace-discover"
        assert resource["update"][1] == "marketplace-verify"
        assert resource["uninstall"][1] == "marketplace-verify"
        assert "marketplace-add" not in resource["install"]
        assert "marketplace-update" not in resource["update"]

    @pytest.mark.parametrize(
        "plugin",
        [
            example_plugin(environments=["local", ""]),
            example_plugin(environments=["local", 1]),
        ],
        ids=["empty-environment", "non-string-environment"],
    )
    def test_rejects_invalid_environment_entries(self, tmp_path, plugin):
        result = render_declaration_plan(
            declaration_data(
                marketplaces={"dotfiles": example_marketplace()},
                plugins={"example": plugin},
            ),
            tmp_path,
        )

        assert result.returncode != 0
        assert "environments entries" in result.stderr

    def test_rejects_empty_runtime_environment(self, tmp_path):
        data = declaration_data(marketplaces={"dotfiles": example_marketplace()})
        data["ai"]["plugin_bridge"]["environment"] = ""
        result = render_declaration_plan(data, tmp_path)

        assert result.returncode != 0
        assert "environment must be a non-empty string" in result.stderr

    def test_requires_capability_skills_table_and_explicit_marketplace(self, tmp_path):
        invalid_skills = declaration_data(
            marketplaces={"dotfiles": example_marketplace()},
            capabilities={
                "capability": {
                    "marketplace": "dotfiles",
                    "skills": [],
                }
            },
        )
        result = render_declaration_plan(invalid_skills, tmp_path)
        assert result.returncode != 0
        assert "skills must be a table" in result.stderr

        missing_marketplace = declaration_data(
            marketplaces={"dotfiles": example_marketplace()},
            capabilities={"capability": {"skills": {"skill": {}}}},
        )
        result = render_declaration_plan(missing_marketplace, tmp_path)
        assert result.returncode != 0
        assert "marketplace must be an explicit" in result.stderr

    def test_capability_skills_are_sorted_and_hosts_are_validated(self, tmp_path):
        result = render_declaration_plan(
            declaration_data(
                marketplaces={"dotfiles": example_marketplace()},
                capabilities={
                    "capability": {
                        "marketplace": "dotfiles",
                        "hosts": ["codex"],
                        "skills": {"zeta": {}, "alpha": {}},
                    }
                },
            ),
            tmp_path,
        )

        assert result.returncode == 0, result.stderr
        resource = next(
            resource
            for resource in json.loads(result.stdout)["resources"]
            if resource["stable_key"] == "capability"
        )
        assert resource["expected_skills"] == ["alpha", "zeta"]
        assert resource["host"] == "codex"

    def test_routes_cursor_and_verifies_generated_package_skills(self, tmp_path):
        result = render_declaration_plan(
            declaration_data(
                marketplaces={"dotfiles": example_marketplace()},
                capabilities={
                    "capability": {
                        "marketplace": "dotfiles",
                        "hosts": ["cursor", "claude"],
                        "skills": {"zeta": {}, "alpha": {}},
                    }
                },
            ),
            tmp_path,
        )

        assert result.returncode == 0, result.stderr
        resources = json.loads(result.stdout)["resources"]
        for host in ("cursor", "claude"):
            resource = next(
                resource
                for resource in resources
                if resource["kind"] == "plugin" and resource["host"] == host
            )
            assert resource["enable"][1] == "plugin-enable"
            assert resource["expected_skills"] == ["alpha", "zeta"]
            assert resource["verify"][-4:] == [
                str(tmp_path),
                "capability",
                "alpha",
                "zeta",
            ]
            if host == "cursor":
                assert resource["install"][0].endswith("agent-plugin-cursor-bridge.sh")
            else:
                assert resource["install"][0].endswith("agent-plugin-host-bridge.sh")

    def test_orders_numeric_values_before_stable_key(self, tmp_path):
        result = render_declaration_plan(
            declaration_data(
                marketplaces={
                    "ten": example_marketplace(order=10),
                    "two": example_marketplace(order=2),
                }
            ),
            tmp_path,
        )

        assert result.returncode == 0, result.stderr
        resources = [
            resource
            for resource in json.loads(result.stdout)["resources"]
            if resource["kind"] == "marketplace"
            and resource["host"] == "claude"
            and resource["stable_key"] in {"two", "ten"}
        ]
        assert [resource["stable_key"] for resource in resources] == ["two", "ten"]


class TestPluginPlanning:
    def test_empty_preflight_output_means_no_occupying_plugin(self, monkeypatch):
        operation = MAIN_MODULE.PluginOperation(
            "preflight",
            "plugin",
            "claude",
            "bridge@dotfiles",
            ("claude", "plugin", "status", "bridge@dotfiles"),
        )

        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(
                args[0], 0, stdout="", stderr=""
            ),
        )

        assert MAIN_MODULE._execute_plugin_command(operation) == ()

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
            ("preflight", "plugin", "cursor", "bridge"),
            ("install", "plugin", "cursor", "bridge"),
            ("preflight", "plugin", "claude", "bridge@dotfiles"),
            ("install", "plugin", "claude", "bridge@dotfiles"),
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
            ("preflight", "plugin", "cursor", "bridge"),
            ("install", "plugin", "cursor", "bridge"),
            ("preflight", "plugin", "claude", "bridge@dotfiles"),
            ("update", "plugin", "claude", "bridge@dotfiles"),
            ("uninstall", "plugin", "claude", "obsolete@dotfiles"),
            ("uninstall", "marketplace", "claude", "obsolete-market"),
        ]

    def test_plans_documented_marketplace_update_for_changed_fingerprint(self):
        parse_plan = bridge_helper("parse_plugin_plan")
        parse_ownership = bridge_helper("parse_plugin_ownership")
        plan_operations = bridge_helper("plan_plugin_operations")
        desired = parse_plan(
            rendered_plan([marketplace("codex", "dotfiles", "market-v2")])
        )
        owned = parse_ownership(
            json.dumps(
                {
                    "version": 1,
                    "resources": [marketplace("codex", "dotfiles", "market-v1")],
                }
            )
        )

        (operation,) = plan_operations(desired, owned)

        assert (operation.action, operation.argv) == (
            "update",
            ("codex", "marketplace", "update", "dotfiles"),
        )

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


class TestPluginAdapters:
    def test_codex_adapter_uses_supported_cli_commands(self, tmp_path):
        template = (
            BASE_ROOT
            / "src/chezmoi/dot_local/libexec/dotfiles/executable_agent-plugin-host-bridge.sh.tmpl"
        )
        data = declaration_data(
            marketplaces={"dotfiles": example_marketplace(hosts=["codex"])},
            plugins={"bridge": example_plugin(hosts=["codex"])},
        )
        rendered = render_adapter(template, data, tmp_path)
        assert rendered.returncode == 0, rendered.stderr
        adapter = executable(tmp_path / "host-bridge.sh", rendered.stdout)
        log = tmp_path / "codex-argv.log"
        executable(
            tmp_path / "codex",
            "#!/bin/sh\n"
            'printf \'%s\\n\' "$*" >> "$CODEX_ARGV_LOG"\n'
            'case "$*" in\n'
            "  'plugin list -m dotfiles')\n"
            "    printf '%s\\n' 'Marketplace `dotfiles`' 'Installed plugins:' 'PLUGIN  STATUS  VERSION  SOURCE' 'bridge@dotfiles  installed, enabled  1.0  local'\n"
            "    ;;\n"
            "esac\n",
        )
        env = {"PATH": f"{tmp_path}:/usr/bin:/bin", "CODEX_ARGV_LOG": str(log)}

        operations = [
            ("marketplace-update", "dotfiles"),
            ("plugin-install", "bridge@dotfiles"),
            ("plugin-update", "bridge@dotfiles"),
            ("plugin-enable", "bridge@dotfiles"),
            ("plugin-status", "bridge@dotfiles"),
            ("plugin-remove", "bridge@dotfiles"),
        ]
        for operation, resource in operations:
            result = subprocess.run(
                [str(adapter), operation, "codex", resource],
                capture_output=True,
                check=False,
                text=True,
                env=env,
            )
            assert result.returncode == 0, result.stderr

        assert log.read_text(encoding="utf-8").splitlines() == [
            "plugin marketplace upgrade dotfiles",
            "plugin add bridge@dotfiles",
            "plugin add bridge@dotfiles",
            "plugin list -m dotfiles",
            "plugin list -m dotfiles",
            "plugin remove bridge@dotfiles",
        ]

    @pytest.mark.parametrize("host", ["claude", "codex"])
    def test_host_adapter_requires_declared_plugin_and_returns_packaged_skills(
        self, tmp_path, host
    ):
        template = (
            BASE_ROOT
            / "src/chezmoi/dot_local/libexec/dotfiles/executable_agent-plugin-host-bridge.sh.tmpl"
        )
        data = declaration_data(
            marketplaces={"dotfiles": example_marketplace(hosts=[host])},
            capabilities={
                "capability": {
                    "marketplace": "dotfiles",
                    "hosts": [host],
                    "skills": {"alpha": {}, "zeta": {}},
                }
            },
        )
        rendered = render_adapter(template, data, tmp_path)
        assert rendered.returncode == 0, rendered.stderr
        adapter = executable(tmp_path / "host-bridge.sh", rendered.stdout)
        package = (
            tmp_path
            / ".local/share/agent-plugins/marketplace/plugins/capability"
            / host
        )
        (package / (f".{host}-plugin")).mkdir(parents=True)
        (package / f".{host}-plugin/plugin.json").write_text(
            json.dumps({"name": "capability"}), encoding="utf-8"
        )
        for skill in ("alpha", "zeta"):
            (package / "skills" / skill).mkdir(parents=True)
            (package / "skills" / skill / "SKILL.md").write_text("# skill\n")

        if host == "claude":
            plugin_list = (
                'printf \'%s\' \'[{"id":"capability@dotfiles","enabled":true}]\''
            )
        else:
            plugin_list = "printf '%s\\n' 'Marketplace `dotfiles`' 'Installed plugins:' 'PLUGIN  STATUS  VERSION  SOURCE' 'capability@dotfiles  installed, enabled  1.0  local'"
        executable(
            tmp_path / host,
            f"#!/bin/sh\ncase \"$*\" in\n  *'plugin marketplace list'*) printf '%s' '[{{\"name\":\"dotfiles\"}}]' ;;\n  *'plugin list'*) {plugin_list} ;;\n  *) exit 0 ;;\nesac\n",
        )
        env = {"PATH": f"{tmp_path}:/usr/bin:/bin"}
        marketplace_result = subprocess.run(
            [str(adapter), "marketplace-add", host, "dotfiles", "locator://one"],
            capture_output=True,
            check=False,
            text=True,
            env=env,
        )
        assert marketplace_result.returncode == 0, marketplace_result.stderr
        discovered_marketplace = subprocess.run(
            [str(adapter), "marketplace-discover", host, "dotfiles"],
            capture_output=True,
            check=False,
            text=True,
            env=env,
        )
        assert discovered_marketplace.returncode == 0, discovered_marketplace.stderr
        verify_result = subprocess.run(
            [
                str(adapter),
                "plugin-verify",
                host,
                "capability@dotfiles",
                str(tmp_path),
                "capability",
                "alpha",
                "zeta",
            ],
            capture_output=True,
            check=False,
            text=True,
            env=env,
        )
        assert verify_result.returncode == 0, verify_result.stderr
        assert json.loads(verify_result.stdout) == {"skills": ["alpha", "zeta"]}

        missing_marketplace = subprocess.run(
            [str(adapter), "marketplace-discover", host, "missing"],
            capture_output=True,
            check=False,
            text=True,
            env=env,
        )
        assert missing_marketplace.returncode != 0

    def test_cursor_adapter_routes_local_plugin_and_reports_actual_skills(
        self, tmp_path
    ):
        template = (
            BASE_ROOT
            / "src/chezmoi/dot_local/libexec/dotfiles/executable_agent-plugin-cursor-bridge.sh.tmpl"
        )
        data = declaration_data(
            marketplaces={"dotfiles": example_marketplace(hosts=["cursor"])},
            capabilities={
                "capability": {
                    "marketplace": "dotfiles",
                    "hosts": ["cursor"],
                    "skills": {"alpha": {}},
                }
            },
        )
        rendered = render_adapter(template, data, tmp_path)
        assert rendered.returncode == 0, rendered.stderr
        adapter = executable(tmp_path / "cursor-bridge.sh", rendered.stdout)
        package = (
            tmp_path
            / ".local/share/agent-plugins/marketplace/plugins/capability/cursor"
        )
        (package / ".cursor-plugin").mkdir(parents=True)
        (package / ".cursor-plugin/plugin.json").write_text(
            json.dumps({"name": "capability"}), encoding="utf-8"
        )
        (package / "skills/alpha").mkdir(parents=True)
        (package / "skills/alpha/SKILL.md").write_text("# alpha\n")
        env = {"PATH": "/usr/bin:/bin"}
        install = subprocess.run(
            [
                str(adapter),
                "plugin-install",
                "cursor",
                "capability@dotfiles",
                str(tmp_path),
            ],
            capture_output=True,
            check=False,
            text=True,
            env=env,
        )
        assert install.returncode == 0, install.stderr
        verify = subprocess.run(
            [
                str(adapter),
                "plugin-verify",
                "cursor",
                "capability@dotfiles",
                str(tmp_path),
                "capability",
                "alpha",
            ],
            capture_output=True,
            check=False,
            text=True,
            env=env,
        )
        assert verify.returncode == 0, verify.stderr
        assert json.loads(verify.stdout) == {"skills": ["alpha"]}

    def test_cursor_adapter_executes_generic_plugin_declaration(self, tmp_path):
        template = (
            BASE_ROOT
            / "src/chezmoi/dot_local/libexec/dotfiles/executable_agent-plugin-cursor-bridge.sh.tmpl"
        )
        data = declaration_data(
            marketplaces={"dotfiles": example_marketplace(hosts=["cursor"])},
            plugins={"generic": example_plugin(hosts=["cursor"])},
        )
        rendered = render_adapter(template, data, tmp_path)
        assert rendered.returncode == 0, rendered.stderr
        adapter = executable(tmp_path / "cursor-bridge.sh", rendered.stdout)
        package = (
            tmp_path / ".local/share/agent-plugins/marketplace/plugins/generic/cursor"
        )
        package.mkdir(parents=True)

        install = subprocess.run(
            [
                str(adapter),
                "plugin-install",
                "cursor",
                "generic@dotfiles",
                str(tmp_path),
            ],
            capture_output=True,
            check=False,
            text=True,
            env={"PATH": "/usr/bin:/bin"},
        )

        assert install.returncode == 0, install.stderr


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
    def test_v1_marketplace_ownership_matches_v2_desired_identity(self, tmp_path):
        parse_ownership = bridge_helper("parse_plugin_ownership")
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        ownership_file.parent.mkdir(parents=True)
        desired = marketplace("claude", "dotfiles")
        desired["marketplace"] = "dotfiles"
        ownership_file.write_text(
            json.dumps(
                {
                    "version": 1,
                    "resources": [
                        {
                            "kind": "marketplace",
                            "host": "claude",
                            "id": "dotfiles",
                            "fingerprint": "market-v1",
                            "uninstall": desired["uninstall"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        plan = parse_plan(rendered_v2_plan([desired]))
        actions = []

        reconcile(tmp_path, ownership_file, plan, actions.append, lambda _: None)

        assert actions == []
        (owned,) = parse_ownership(ownership_file.read_text(encoding="utf-8"))
        assert owned.marketplace == "dotfiles"

    def test_owned_removal_preview_is_order_insensitive_but_exact(self, tmp_path):
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        ownership_file.parent.mkdir(parents=True)
        first = plugin("claude", "first@dotfiles", ["one"])
        second = plugin("claude", "second@dotfiles", ["two"])
        ownership_file.write_text(
            json.dumps({"version": 1, "resources": [first, second]}),
            encoding="utf-8",
        )
        plan = parse_plan(
            rendered_plan(
                [],
                owned_removals=[removal_preview(second), removal_preview(first)],
            )
        )
        removed = []
        reconcile(
            tmp_path,
            ownership_file,
            plan,
            lambda operation: removed.append(operation.resource_id),
            lambda _: None,
        )
        assert removed == ["first@dotfiles", "second@dotfiles"]

    def test_rejects_mismatched_owned_removal_preview_before_host_execution(
        self, tmp_path
    ):
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

        assert actions == ["preflight", "adopt"]
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

        assert not ownership_file.exists()

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
        assert (tmp_path / ".local/state/dotfiles/skill-roots.manifest").read_text(
            encoding="utf-8"
        ) == ""

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
            ("preflight", "plugin", "claude", "bridge@dotfiles"),
            ("install", "plugin", "claude", "bridge@dotfiles"),
            ("verify", "plugin", "claude", "bridge@dotfiles"),
            (
                "cleanup",
                str(tmp_path / ".local/state/dotfiles/skill-roots.manifest"),
            ),
            ("uninstall", "plugin", "claude", "obsolete@dotfiles"),
        ]
        assert installed_plugins == {"unmanaged@personal", "bridge@dotfiles"}

    def test_skill_verification_failure_preserves_legacy_and_records_install(
        self, tmp_path
    ):
        parse_ownership = bridge_helper("parse_plugin_ownership")
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
        assert parse_ownership(ownership_file.read_text(encoding="utf-8")) == ()

    def test_plugin_install_failure_records_prior_marketplace_install(self, tmp_path):
        parse_ownership = bridge_helper("parse_plugin_ownership")
        parse_plan = bridge_helper("parse_plugin_plan")
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
        (owned,) = parse_ownership(ownership_file.read_text(encoding="utf-8"))
        assert (owned.kind, owned.resource_id) == ("marketplace", "dotfiles")

    def test_retry_recovers_ownership_after_a_later_install_failure(self, tmp_path):
        parse_ownership = bridge_helper("parse_plugin_ownership")
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/agent-plugin-ownership.json"
        first = plugin("claude", "first@dotfiles", ["first"])
        second = plugin("codex", "second@dotfiles", ["second"])
        plan = parse_plan(rendered_plan([first, second]))
        first_attempts = []

        def fail_second_install(operation):
            first_attempts.append((operation.action, operation.resource_id))
            if (
                operation.action == "install"
                and operation.resource_id == "second@dotfiles"
            ):
                raise OSError("second install failed")
            if operation.action == "verify":
                return (operation.resource_id[: -len("@dotfiles")],)
            return ()

        with pytest.raises(OSError, match="second install failed"):
            reconcile(
                tmp_path, ownership_file, plan, fail_second_install, lambda _: None
            )

        assert first_attempts == [
            ("preflight", "first@dotfiles"),
            ("install", "first@dotfiles"),
            ("verify", "first@dotfiles"),
            ("preflight", "second@dotfiles"),
            ("install", "second@dotfiles"),
        ]
        (owned,) = parse_ownership(ownership_file.read_text(encoding="utf-8"))
        assert owned.resource_id == "first@dotfiles"

        retry_attempts = []

        def complete_retry(operation):
            retry_attempts.append((operation.action, operation.resource_id))
            if operation.action == "preflight":
                return (
                    ("installed", "enabled")
                    if operation.resource_id == "first@dotfiles"
                    else ()
                )
            if operation.action == "verify":
                return (operation.resource_id[: -len("@dotfiles")],)
            return ()

        reconcile(tmp_path, ownership_file, plan, complete_retry, lambda _: None)

        assert retry_attempts == [
            ("preflight", "first@dotfiles"),
            ("verify", "first@dotfiles"),
            ("preflight", "second@dotfiles"),
            ("install", "second@dotfiles"),
            ("verify", "second@dotfiles"),
        ]
        assert {
            resource.resource_id
            for resource in parse_ownership(ownership_file.read_text(encoding="utf-8"))
        } == {"first@dotfiles", "second@dotfiles"}

    def test_retry_recovers_marketplace_after_plugin_install_failure(self, tmp_path):
        parse_ownership = bridge_helper("parse_plugin_ownership")
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        plan = parse_plan(
            rendered_plan(
                [
                    marketplace("claude", "dotfiles"),
                    plugin("claude", "bridge@dotfiles", ["brainstorming"]),
                ]
            )
        )

        def fail_plugin_install(operation):
            if operation.action == "install" and operation.kind == "plugin":
                raise OSError("plugin install failed")
            return ()

        with pytest.raises(OSError, match="plugin install failed"):
            reconcile(
                tmp_path, ownership_file, plan, fail_plugin_install, lambda _: None
            )

        (owned,) = parse_ownership(ownership_file.read_text(encoding="utf-8"))
        assert (owned.kind, owned.resource_id) == ("marketplace", "dotfiles")

        actions = []

        def complete_retry(operation):
            actions.append((operation.action, operation.kind))
            return ("brainstorming",) if operation.action == "verify" else ()

        reconcile(tmp_path, ownership_file, plan, complete_retry, lambda _: None)

        assert ("install", "marketplace") not in actions

    def test_retry_owns_plugin_when_initial_verification_fails(self, tmp_path):
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        plan = parse_plan(
            rendered_plan([plugin("claude", "bridge@dotfiles", ["brainstorming"])])
        )

        def fail_verification(operation):
            return ("unexpected",) if operation.action == "verify" else ()

        with pytest.raises(MAIN_MODULE.FilterError, match="expected"):
            reconcile(tmp_path, ownership_file, plan, fail_verification, lambda _: None)

        assert not ownership_file.exists()

        actions = []

        def complete_retry(operation):
            actions.append(operation.action)
            return ("brainstorming",) if operation.action == "verify" else ()

        reconcile(tmp_path, ownership_file, plan, complete_retry, lambda _: None)

        assert actions == ["preflight", "install", "verify"]

    def test_partial_checkpoint_preserves_prior_update_fingerprint(self, tmp_path):
        parse_ownership = bridge_helper("parse_plugin_ownership")
        parse_plan = bridge_helper("parse_plugin_plan")
        reconcile = bridge_helper("reconcile_plugins")
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        ownership_file.parent.mkdir(parents=True)
        prior_first = plugin("claude", "first@dotfiles", ["first"], "plugin-v1")
        prior_third = plugin("claude", "third@dotfiles", ["third"], "plugin-v1")
        ownership_file.write_text(
            json.dumps({"version": 1, "resources": [prior_first, prior_third]}),
            encoding="utf-8",
        )
        plan = parse_plan(
            rendered_plan(
                [
                    plugin("claude", "first@dotfiles", ["first"], "plugin-v2"),
                    plugin("claude", "second@dotfiles", ["second"]),
                    plugin("claude", "third@dotfiles", ["third"], "plugin-v2"),
                ]
            )
        )

        def fail_last_update(operation):
            if operation.action == "preflight":
                return (
                    ()
                    if operation.resource_id == "second@dotfiles"
                    else ("installed", "enabled")
                )
            if (
                operation.action == "update"
                and operation.resource_id == "third@dotfiles"
            ):
                raise OSError("last update failed")
            if operation.action == "verify":
                return (operation.resource_id[: -len("@dotfiles")],)
            return ()

        with pytest.raises(OSError, match="last update failed"):
            reconcile(tmp_path, ownership_file, plan, fail_last_update, lambda _: None)

        owned = {
            resource.resource_id: resource
            for resource in parse_ownership(ownership_file.read_text(encoding="utf-8"))
        }
        assert owned["first@dotfiles"].fingerprint == "plugin-v2"
        assert owned["second@dotfiles"].fingerprint == "plugin-v1"
        assert owned["third@dotfiles"].fingerprint == "plugin-v1"

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
        assert actions == ["preflight", "install", "verify"]


class TestVersionTwoPluginLifecycle:
    def test_missing_plugin_is_installed_enabled_verified_and_checkpointed(
        self, tmp_path
    ):
        resource = plugin_v2("claude", "bridge@dotfiles", ["brainstorming"])
        plan = MAIN_MODULE.parse_plugin_plan(rendered_v2_plan([resource]))
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        actions = []

        def execute(operation):
            actions.append(operation.action)
            return ("brainstorming",) if operation.action == "verify" else ()

        MAIN_MODULE.reconcile_plugins(
            tmp_path, ownership_file, plan, execute, lambda _: None
        )

        assert actions == ["preflight", "install", "enable", "verify"]
        ownership = json.loads(ownership_file.read_text(encoding="utf-8"))
        assert ownership["version"] == 2
        assert ownership["resources"][0]["marketplace"] == "dotfiles"

    def test_enabled_unowned_plugin_is_verified_and_adopted_without_install(
        self, tmp_path
    ):
        resource = plugin_v2("claude", "bridge@dotfiles", ["brainstorming"])
        plan = MAIN_MODULE.parse_plugin_plan(rendered_v2_plan([resource]))
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        actions = []

        def execute(operation):
            actions.append(operation.action)
            if operation.action == "preflight":
                return ("installed", "enabled")
            return ("brainstorming",) if operation.action == "verify" else ()

        MAIN_MODULE.reconcile_plugins(
            tmp_path, ownership_file, plan, execute, lambda _: None
        )

        assert actions == ["preflight", "verify"]

    def test_disabled_owned_plugin_is_enabled_and_verified(self, tmp_path):
        resource = plugin_v2("claude", "bridge@dotfiles", ["brainstorming"])
        plan = MAIN_MODULE.parse_plugin_plan(rendered_v2_plan([resource]))
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        ownership_file.parent.mkdir(parents=True)
        ownership_file.write_text(
            json.dumps(
                {
                    "version": 2,
                    "resources": [
                        {
                            "kind": "plugin",
                            "host": "claude",
                            "marketplace": "dotfiles",
                            "id": "bridge@dotfiles",
                            "order": 200,
                            "fingerprint": "plugin-v1",
                            "enable": resource["enable"],
                            "uninstall": resource["uninstall"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        actions = []

        def execute(operation):
            actions.append(operation.action)
            if operation.action == "preflight":
                return ("installed",)
            return ("brainstorming",) if operation.action == "verify" else ()

        MAIN_MODULE.reconcile_plugins(
            tmp_path, ownership_file, plan, execute, lambda _: None
        )

        assert actions == ["preflight", "enable", "verify"]

    def test_failed_verification_does_not_claim_new_plugin(self, tmp_path):
        resource = plugin_v2("claude", "bridge@dotfiles", ["brainstorming"])
        plan = MAIN_MODULE.parse_plugin_plan(rendered_v2_plan([resource]))
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"

        def execute(operation):
            if operation.action == "verify":
                return ("wrong",)
            return ()

        with pytest.raises(MAIN_MODULE.FilterError, match="expected"):
            MAIN_MODULE.reconcile_plugins(
                tmp_path, ownership_file, plan, execute, lambda _: None
            )
        assert not ownership_file.exists()

    def test_removed_owned_plugin_is_uninstalled_after_desired_verification(
        self, tmp_path
    ):
        resource = plugin_v2("claude", "bridge@dotfiles", ["brainstorming"])
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        ownership_file.parent.mkdir(parents=True)
        ownership_file.write_text(
            json.dumps(
                {
                    "version": 2,
                    "resources": [
                        {
                            "kind": "plugin",
                            "host": "claude",
                            "marketplace": "dotfiles",
                            "id": "bridge@dotfiles",
                            "order": 200,
                            "fingerprint": "plugin-v1",
                            "enable": resource["enable"],
                            "uninstall": resource["uninstall"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        actions = []
        plan = MAIN_MODULE.parse_plugin_plan(rendered_v2_plan([]))

        def execute(operation):
            actions.append(operation.action)
            return ()

        MAIN_MODULE.reconcile_plugins(
            tmp_path, ownership_file, plan, execute, lambda _: None
        )

        assert actions == ["uninstall"]
        assert json.loads(ownership_file.read_text(encoding="utf-8"))["resources"] == []

    def test_never_owned_undeclared_plugin_is_untouched(self, tmp_path):
        actions = []
        plan = MAIN_MODULE.parse_plugin_plan(rendered_v2_plan([]))
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"

        MAIN_MODULE.reconcile_plugins(
            tmp_path, ownership_file, plan, actions.append, lambda _: None
        )

        assert actions == []
        assert not ownership_file.exists()

    def test_fingerprint_update_failure_preserves_prior_ownership(self, tmp_path):
        resource = plugin_v2(
            "claude", "bridge@dotfiles", ["brainstorming"], fingerprint="plugin-v2"
        )
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        ownership_file.parent.mkdir(parents=True)
        ownership_file.write_text(
            json.dumps(
                {
                    "version": 2,
                    "resources": [
                        {
                            "kind": "plugin",
                            "host": "claude",
                            "marketplace": "dotfiles",
                            "id": "bridge@dotfiles",
                            "order": 200,
                            "fingerprint": "plugin-v1",
                            "enable": resource["enable"],
                            "uninstall": resource["uninstall"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        plan = MAIN_MODULE.parse_plugin_plan(rendered_v2_plan([resource]))

        def execute(operation):
            if operation.action == "preflight":
                return ("installed", "enabled")
            if operation.action == "update":
                raise OSError("update failed")
            return ()

        with pytest.raises(OSError, match="update failed"):
            MAIN_MODULE.reconcile_plugins(
                tmp_path, ownership_file, plan, execute, lambda _: None
            )

        ownership = json.loads(ownership_file.read_text(encoding="utf-8"))
        assert ownership["version"] == 2
        assert ownership["resources"][0]["fingerprint"] == "plugin-v1"

    def test_enable_failure_preserves_prior_ownership(self, tmp_path):
        resource = plugin_v2("claude", "bridge@dotfiles", ["brainstorming"])
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        ownership_file.parent.mkdir(parents=True)
        ownership_file.write_text(
            json.dumps(
                {
                    "version": 2,
                    "resources": [
                        {
                            "kind": "plugin",
                            "host": "claude",
                            "marketplace": "dotfiles",
                            "id": "bridge@dotfiles",
                            "order": 200,
                            "fingerprint": "plugin-v1",
                            "enable": resource["enable"],
                            "uninstall": resource["uninstall"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        plan = MAIN_MODULE.parse_plugin_plan(rendered_v2_plan([resource]))

        def execute(operation):
            if operation.action == "preflight":
                return ("installed",)
            if operation.action == "enable":
                raise OSError("enable failed")
            return ()

        with pytest.raises(OSError, match="enable failed"):
            MAIN_MODULE.reconcile_plugins(
                tmp_path, ownership_file, plan, execute, lambda _: None
            )

        ownership = json.loads(ownership_file.read_text(encoding="utf-8"))
        assert ownership["resources"][0]["fingerprint"] == "plugin-v1"

    def test_uninstall_failure_preserves_prior_ownership(self, tmp_path):
        resource = plugin_v2("claude", "bridge@dotfiles", ["brainstorming"])
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        ownership_file.parent.mkdir(parents=True)
        ownership_file.write_text(
            json.dumps(
                {
                    "version": 2,
                    "resources": [
                        {
                            "kind": "plugin",
                            "host": "claude",
                            "marketplace": "dotfiles",
                            "id": "bridge@dotfiles",
                            "order": 200,
                            "fingerprint": "plugin-v1",
                            "enable": resource["enable"],
                            "uninstall": resource["uninstall"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        plan = MAIN_MODULE.parse_plugin_plan(rendered_v2_plan([]))

        def execute(operation):
            raise OSError("uninstall failed")

        with pytest.raises(OSError, match="uninstall failed"):
            MAIN_MODULE.reconcile_plugins(
                tmp_path, ownership_file, plan, execute, lambda _: None
            )

        ownership = json.loads(ownership_file.read_text(encoding="utf-8"))
        assert ownership["resources"][0]["id"] == "bridge@dotfiles"

    def test_v1_ownership_is_migrated_when_desired_resource_is_verified(self, tmp_path):
        resource = plugin_v2("claude", "bridge@dotfiles", ["brainstorming"])
        ownership_file = tmp_path / ".local/state/dotfiles/ownership.json"
        ownership_file.parent.mkdir(parents=True)
        ownership_file.write_text(
            json.dumps(
                {
                    "version": 1,
                    "resources": [
                        {
                            "kind": "plugin",
                            "host": "claude",
                            "id": "bridge@dotfiles",
                            "fingerprint": "plugin-v1",
                            "uninstall": resource["uninstall"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        plan = MAIN_MODULE.parse_plugin_plan(rendered_v2_plan([resource]))

        def execute(operation):
            if operation.action == "preflight":
                return ("installed", "enabled")
            return ("brainstorming",) if operation.action == "verify" else ()

        MAIN_MODULE.reconcile_plugins(
            tmp_path, ownership_file, plan, execute, lambda _: None
        )

        ownership = json.loads(ownership_file.read_text(encoding="utf-8"))
        assert ownership["version"] == 2
        assert ownership["resources"][0]["marketplace"] == "dotfiles"
