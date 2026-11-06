"""Integration coverage for authored plugins delivered as generated native entries."""

import json
import shutil
import stat

import pytest
from test_ai_skills import _install_cleanup

MARKET = ".local/share/agent-plugins/marketplace/plugins"
CURSOR_LOCAL = ".cursor/plugins/local"
HOSTS = ("claude", "codex", "cursor")
MARKETPLACE_FILES = {
    "claude": ".local/share/agent-plugins/marketplace/.claude-plugin/marketplace.json",
    "codex": ".local/share/agent-plugins/marketplace/.agents/plugins/marketplace.json",
}


def _manifest_path(name: str, host: str) -> str:
    return f"{MARKET}/{name}/{host}/.{host}-plugin/plugin.json"


def _cursor_manifest_path(name: str) -> str:
    return f"{CURSOR_LOCAL}/{name}/.cursor-plugin/plugin.json"


def _manifest_paths(name: str) -> list[str]:
    return [*(_manifest_path(name, host) for host in HOSTS), _cursor_manifest_path(name)]


def _apply(fixture) -> None:
    result = fixture.run("apply")
    assert result.returncode == 0, result.stderr


def _assert_stable(fixture) -> None:
    result = fixture.run("--no-pager", "diff")
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def _read_json(fixture, relative: str) -> dict:
    return json.loads((fixture.destination / relative).read_text(encoding="utf-8"))


def _plugin_names(managed: set[str], root: str) -> set[str]:
    return {path.removeprefix(f"{root}/").split("/")[0] for path in managed if path.startswith(f"{root}/")}


def _marketplace_names(fixture, host: str) -> set[str]:
    return {entry["name"] for entry in _read_json(fixture, MARKETPLACE_FILES[host])["plugins"]}


def _host_views(managed: set[str], name: str, relative: str) -> set[str]:
    views = {host for host in HOSTS if f"{MARKET}/{name}/{host}/{relative}" in managed}
    if f"{CURSOR_LOCAL}/{name}/{relative}" in managed:
        views.add("cursor-local")
    return views


def _capability(name: str, **values) -> str:
    lines = [f'[data.ai.plugin_bridge.capabilities."{name}"]']
    lines.extend(f"{key} = {json.dumps(value)}" for key, value in values.items() if key != "skills")
    if "skills" in values:
        lines.append(f'[data.ai.plugin_bridge.capabilities."{name}".skills]')
        lines.extend(f"{key} = {json.dumps(value)}" for key, value in values["skills"].items())
    return "\n".join(lines) + "\n"


def _set_environment(fixture, environment: str) -> None:
    """Add ai.plugin_bridge.environment to the table that write_config opens."""
    text = fixture.config.read_text(encoding="utf-8")
    hosts = 'default_hosts = ["claude", "codex", "cursor"]\n'
    fixture.config.write_text(text.replace(hosts, hosts + f"environment = {json.dumps(environment)}\n", 1))


def test_discovered_identities_match_installed_names(agent_source_fixture):
    """Directory names map to the identity names that hosts already have installed."""
    fixture = agent_source_fixture
    skill = {"guide": {"SKILL.md": "# Guide\n"}}
    fixture.write_plugin("domain-brain", skills=skill)
    fixture.write_plugin("writing", {"name": "mikekobit-writing"}, skills=skill)
    fixture.write_plugin("skill-feedback", {"name": "mkobit-skill-feedback"}, skills=skill)
    fixture.write_plugin("stripe-dotfiles", skills=skill)
    mcp = {".mcp.json.tmpl": '{"mcpServers": {}}\n'}
    fixture.write_plugin("toolshed-mcp", wrappers={"claude": mcp, "codex": mcp})
    fixture.write_config(_capability("toolshed-mcp", hosts=["claude", "codex"]))
    authored = {"domain-brain", "mikekobit-writing", "mkobit-skill-feedback", "stripe-dotfiles", "toolshed-mcp"}

    managed = fixture.managed_files()
    assert _plugin_names(managed, MARKET) == authored | {"mkobit-dotfiles"}
    assert _plugin_names(managed, CURSOR_LOCAL) == authored - {"toolshed-mcp"} | {"mkobit-dotfiles"}
    _apply(fixture)
    for name in authored:
        for path in _manifest_paths(name):
            if path in managed:
                assert _read_json(fixture, path)["name"] == name
    for host in MARKETPLACE_FILES:
        assert _marketplace_names(fixture, host) == authored | {"mkobit-dotfiles"}
    _assert_stable(fixture)


def test_added_plugin_deploys_without_catalog_entry(agent_source_fixture):
    """A new plugin directory deploys every default view and joins the marketplaces."""
    fixture = agent_source_fixture
    fixture.write_plugin("first", skills={"one": {"SKILL.md": "# One\n"}})
    _apply(fixture)
    assert "second" not in _marketplace_names(fixture, "claude")

    fixture.write_plugin("second", skills={"two": {"SKILL.md": "# Two\n"}})
    _apply(fixture)
    for host in HOSTS:
        assert (fixture.destination / MARKET / "second" / host / "skills/two/SKILL.md").read_text() == "# Two\n"
    assert (fixture.destination / CURSOR_LOCAL / "second/skills/two/SKILL.md").read_text() == "# Two\n"
    assert all(_read_json(fixture, path)["skills"] == "./skills" for path in _manifest_paths("second"))
    for host in MARKETPLACE_FILES:
        assert _marketplace_names(fixture, host) == {"mkobit-dotfiles", "first", "second"}
    _assert_stable(fixture)


def test_default_hosts_and_host_exception_select_views(agent_source_fixture):
    """Default hosts give every view; a hosts exception drops the Cursor view and local copy."""
    fixture = agent_source_fixture
    mcp = {".mcp.json.tmpl": '{"mcpServers": {"toolshed": {}}}\n'}
    fixture.write_plugin("toolshed-mcp", wrappers={"claude": mcp, "codex": mcp})
    fixture.write_plugin("everywhere", skills={"one": {"SKILL.md": "# One\n"}})
    fixture.write_config(_capability("toolshed-mcp", hosts=["claude", "codex"]))

    managed = fixture.managed_files()
    assert _host_views(managed, "toolshed-mcp", ".mcp.json") == {"claude", "codex"}
    assert not any(path.startswith(f"{MARKET}/toolshed-mcp/cursor") for path in managed)
    assert not any(path.startswith(f"{CURSOR_LOCAL}/toolshed-mcp") for path in managed)
    assert _host_views(managed, "everywhere", "skills/one/SKILL.md") == {*HOSTS, "cursor-local"}
    _apply(fixture)
    assert not (fixture.destination / CURSOR_LOCAL / "toolshed-mcp").exists()
    assert not (fixture.destination / MARKET / "toolshed-mcp/cursor").exists()
    for host in ("claude", "codex"):
        manifest = _read_json(fixture, _manifest_path("toolshed-mcp", host))
        assert manifest["mcpServers"] == "./.mcp.json"
        assert "skills" not in manifest
    _assert_stable(fixture)


def test_skill_exception_absent_and_single_host(agent_source_fixture):
    """Skill exceptions drop a skill everywhere or keep it on one host, and manifests follow."""
    fixture = agent_source_fixture
    fixture.write_plugin(
        "mixed",
        skills={name: {"SKILL.md": f"# {name}\n"} for name in ("kept", "dropped", "codex-only")},
    )
    fixture.write_plugin("single", skills={"only": {"SKILL.md": "# Only\n"}})
    fixture.write_config(
        _capability("mixed", skills={"dropped": "absent", "codex-only": "codex", "stale": "absent"})
        + _capability("single", skills={"only": "codex"})
    )

    managed = fixture.managed_files()
    assert _host_views(managed, "mixed", "skills/kept/SKILL.md") == {*HOSTS, "cursor-local"}
    assert _host_views(managed, "mixed", "skills/dropped/SKILL.md") == set()
    assert _host_views(managed, "mixed", "skills/codex-only/SKILL.md") == {"codex"}
    assert _host_views(managed, "single", "skills/only/SKILL.md") == {"codex"}
    _apply(fixture)
    assert all(_read_json(fixture, path)["skills"] == "./skills" for path in _manifest_paths("mixed"))
    for path in _manifest_paths("single"):
        assert ("skills" in _read_json(fixture, path)) is (path == _manifest_path("single", "codex"))
    assert not (fixture.destination / MARKET / "single/claude/skills").exists()
    assert not (fixture.destination / CURSOR_LOCAL / "single/skills").exists()
    _assert_stable(fixture)


@pytest.mark.parametrize(("state", "message"), [("present", "has no skill"), ("opencode", "state must be one of")])
def test_skill_exception_for_unknown_skill_or_state_fails(agent_source_fixture, state, message):
    """Only an absent exception may name a skill the plugin does not have."""
    fixture = agent_source_fixture
    fixture.write_plugin("mixed", skills={"kept": {"SKILL.md": "# Kept\n"}})
    fixture.write_config(_capability("mixed", skills={"missing": state}))
    result = fixture.run("managed", "--include=files")
    assert result.returncode != 0
    assert message in result.stderr


def test_shared_skills_source_dir_projects_overlay_skills(agent_source_fixture):
    """skills_source_dir projects a shared skill tree into every view of one plugin."""
    fixture = agent_source_fixture
    shared = fixture.authored / "overlay-skills/mermaid-sharing"
    (shared / "references").mkdir(parents=True)
    (shared / "SKILL.md").write_text("# Mermaid sharing\n", encoding="utf-8")
    (shared / "references/stripe-delivery.md").write_text("delivery\n", encoding="utf-8")
    fixture.write_plugin("stripe-dotfiles", {"skills_source_dir": "src/overlay-skills"})

    _apply(fixture)
    roots = [f"{MARKET}/stripe-dotfiles/{host}/skills" for host in HOSTS] + [f"{CURSOR_LOCAL}/stripe-dotfiles/skills"]
    for root in roots:
        skill = fixture.destination / root / "mermaid-sharing"
        assert (skill / "SKILL.md").read_text() == "# Mermaid sharing\n"
        assert (skill / "references/stripe-delivery.md").read_text() == "delivery\n"
    assert all(_read_json(fixture, path)["skills"] == "./skills" for path in _manifest_paths("stripe-dotfiles"))
    _assert_stable(fixture)


def test_generated_manifest_adds_mcp_and_rules_components(agent_source_fixture):
    """Wrapper .mcp.json and rules/ become manifest components on the hosts that carry them."""
    fixture = agent_source_fixture
    fixture.write_config('[data.fixture]\nserver = "toolshed"\n')
    fixture.write_plugin(
        "components",
        skills={"one": {"SKILL.md": "# One\n"}},
        wrappers={
            "claude": {".mcp.json.tmpl": '{"mcpServers": {"{{ .fixture.server }}": {}}}\n'},
            "cursor": {"rules/guidelines.mdc.tmpl": "rule {{ .fixture.server }}\n"},
        },
    )

    _apply(fixture)
    claude = _read_json(fixture, _manifest_path("components", "claude"))
    assert claude["mcpServers"] == "./.mcp.json"
    assert "rules" not in claude
    codex = _read_json(fixture, _manifest_path("components", "codex"))
    assert "mcpServers" not in codex
    assert "rules" not in codex
    for path in (_manifest_path("components", "cursor"), _cursor_manifest_path("components")):
        cursor = _read_json(fixture, path)
        assert cursor["rules"] == "./rules"
        assert "mcpServers" not in cursor
    assert _read_json(fixture, f"{MARKET}/components/claude/.mcp.json") == {"mcpServers": {"toolshed": {}}}
    for root in (f"{MARKET}/components/cursor", f"{CURSOR_LOCAL}/components"):
        assert (fixture.destination / root / "rules/guidelines.mdc").read_text() == "rule toolshed\n"
    _assert_stable(fixture)


def test_codex_manifest_carries_identity_author_and_interface(agent_source_fixture):
    """Identity author and interface appear in the Codex manifest only."""
    fixture = agent_source_fixture
    author = {"name": "Local developer"}
    interface = {"displayName": "Domain brain", "capabilities": ["records"], "defaultPrompt": ["Help me."]}
    skills = {"records": {"SKILL.md": "# Records\n"}}
    fixture.write_plugin("domain-brain", {"author": author, "interface": interface}, skills=skills)
    fixture.write_plugin("plain", skills=skills)

    _apply(fixture)
    codex = _read_json(fixture, _manifest_path("domain-brain", "codex"))
    assert codex["author"] == author
    assert codex["interface"] == interface
    assert codex["description"] == "domain-brain fixture plugin."
    for path in (_manifest_path("domain-brain", "claude"), _manifest_path("domain-brain", "cursor")):
        assert set(_read_json(fixture, path)) == {"name", "version", "description", "skills"}
    assert set(_read_json(fixture, _manifest_path("plain", "codex"))) == {"name", "version", "description", "skills"}


def test_canonical_wrapper_manifest_is_rejected(agent_source_fixture):
    """Host manifests are generated, so a wrapper manifest stops preparation."""
    fixture = agent_source_fixture
    fixture.write_plugin(
        "domain-brain",
        skills={"records": {"SKILL.md": "# Records\n"}},
        wrappers={"claude": {".claude-plugin/plugin.json.tmpl": "{}\n"}},
    )
    result = fixture.run("managed", "--include=files")
    assert result.returncode != 0
    assert "wrapper defines the generated manifest" in result.stderr


def test_native_plugin_source_supports_nested_exact_dot_private_readonly_empty_and_executable(agent_source_fixture):
    """A native plugin tree uses chezmoi source attributes as written."""
    fixture = agent_source_fixture
    fixture.write_config('[data.fixture]\nvalue = "native"\n')
    root = fixture.write_plugin(
        "native",
        {"native_source": True},
        skills={
            "private_tool": {
                "SKILL.md": "# Tool\n",
                "exact_dot_config/private_readonly_settings": "settings\n",
                "notes/readme.md": "notes\n",
                "empty_marker": "",
                "executable_run.sh": "#!/bin/sh\necho run\n",
                "dot_hidden.tmpl": "{{ .fixture.value }}\n",
                "cache/.keep": "",
            }
        },
        wrappers={"claude": {"executable_dot_check.sh": "#!/bin/sh\nexit 0\n"}},
    )
    assert root.is_dir()

    _apply(fixture)
    for base in [f"{MARKET}/native/{host}/skills/tool" for host in HOSTS] + [f"{CURSOR_LOCAL}/native/skills/tool"]:
        skill = fixture.destination / base
        assert stat.S_IMODE(skill.stat().st_mode) == 0o700
        settings = skill / ".config/settings"
        assert settings.read_text() == "settings\n"
        assert stat.S_IMODE(settings.stat().st_mode) == 0o400
        assert (skill / "marker").read_bytes() == b""
        assert (skill / "run.sh").stat().st_mode & 0o111
        assert (skill / ".hidden").read_text() == "native\n"
        assert (skill / "cache").is_dir()
        assert not (skill / "cache/.keep").exists()
        (skill / ".config/unmanaged").write_text("pruned\n")
        (skill / "notes/unmanaged").write_text("kept\n")
    check = fixture.destination / MARKET / "native/claude/.check.sh"
    assert check.stat().st_mode & 0o111
    assert not (fixture.destination / MARKET / "native/codex/.check.sh").exists()

    _apply(fixture)
    for base in [f"{MARKET}/native/{host}/skills/tool" for host in HOSTS] + [f"{CURSOR_LOCAL}/native/skills/tool"]:
        skill = fixture.destination / base
        assert not (skill / ".config/unmanaged").exists()
        assert (skill / "notes/unmanaged").read_text() == "kept\n"
    _assert_stable(fixture)


def test_native_wrapper_dir_is_copied_verbatim(agent_source_fixture):
    """A native wrapper host uses source attributes; other hosts keep literal names."""
    fixture = agent_source_fixture
    fixture.write_config('[data.fixture]\nvalue = "rule"\n')
    fixture.write_plugin(
        "stripe-dotfiles",
        {"native_wrappers": ["cursor"]},
        skills={"writing": {"SKILL.md": "# Writing\n"}},
        wrappers={
            "cursor": {"exact_rules/private_guidelines.mdc.tmpl": "{{ .fixture.value }}\n"},
            "claude": {"dot_literal": "literal\n"},
        },
    )

    _apply(fixture)
    for root in (f"{MARKET}/stripe-dotfiles/cursor", f"{CURSOR_LOCAL}/stripe-dotfiles"):
        rule = fixture.destination / root / "rules/guidelines.mdc"
        assert rule.read_text() == "rule\n"
        assert stat.S_IMODE(rule.stat().st_mode) == 0o600
    assert (fixture.destination / MARKET / "stripe-dotfiles/claude/dot_literal").read_text() == "literal\n"
    assert _read_json(fixture, _cursor_manifest_path("stripe-dotfiles"))["rules"] == "./rules"
    _assert_stable(fixture)


def test_inactive_host_and_environment_templates_are_not_rendered(agent_source_fixture):
    """Unselected hosts, absent skills, and disabled environments never render their templates."""
    fixture = agent_source_fixture
    failing = '{{ fail "inactive template rendered" }}'
    fixture.write_plugin(
        "partial",
        skills={"active": {"SKILL.md": "# Active\n"}, "inactive": {"SKILL.md.tmpl": failing}},
        wrappers={"cursor": {"broken.json.tmpl": failing}},
    )
    fixture.write_plugin("remote", skills={"remote": {"SKILL.md.tmpl": failing}})
    fixture.write_config(
        _capability("partial", hosts=["claude", "codex"], skills={"inactive": "absent"})
        + _capability("remote", environments=["mydata"])
    )
    _set_environment(fixture, "mydev")

    managed = fixture.managed_files()
    assert "remote" not in _plugin_names(managed, MARKET)
    assert "remote" not in _plugin_names(managed, CURSOR_LOCAL)
    assert _host_views(managed, "partial", "skills/active/SKILL.md") == {"claude", "codex"}
    _apply(fixture)
    assert all((fixture.destination / path).is_file() for path in _manifest_paths("partial")[:2])
    assert "remote" not in _marketplace_names(fixture, "claude")
    assert not list(fixture.destination.rglob("broken.json"))
    _assert_stable(fixture)


def test_manifest_version_follows_rendered_data_and_is_stable_on_repeat(agent_source_fixture):
    """Versions are shared by every view, stable on repeat, and change with rendered content."""
    fixture = agent_source_fixture
    fixture.write_config('[data.fixture]\nvalue = "first"\n')
    root = fixture.write_plugin(
        "versioned",
        skills={"one": {"SKILL.md.tmpl": "one {{ .fixture.value }}\n", "payload.bin": b"\x00\xff"}},
    )
    targets = [f"{MARKET}/versioned/{host}/skills/one/SKILL.md" for host in HOSTS]
    targets.append(f"{CURSOR_LOCAL}/versioned/skills/one/SKILL.md")

    def versions() -> set[str]:
        _apply(fixture)
        return {_read_json(fixture, path)["version"] for path in _manifest_paths("versioned")}

    first = versions()
    assert len(first) == 1
    assert versions() == first
    _assert_stable(fixture)

    fixture.write_config('[data.fixture]\nvalue = "second"\n')
    data_changed = versions()
    assert len(data_changed) == 1 and data_changed != first
    assert all((fixture.destination / path).read_text() == "one second\n" for path in targets)

    (root / "skills/one/SKILL.md.tmpl").write_text("edited {{ .fixture.value }}\n", encoding="utf-8")
    source_changed = versions()
    assert len(source_changed) == 1 and source_changed not in (first, data_changed)
    assert all((fixture.destination / path).read_text() == "edited second\n" for path in targets)

    (root / "skills/one/payload.bin").chmod(0o755)
    assert versions() not in (first, data_changed, source_changed)
    assert versions() == versions()
    _assert_stable(fixture)


def test_deleted_plugin_identity_removes_package_and_cursor_roots(agent_source_fixture):
    """Deleting a plugin directory removes its package and Cursor-local roots; unowned plugins stay."""
    fixture = agent_source_fixture
    _install_cleanup(fixture)
    fixture.write_plugin("doomed", skills={"one": {"SKILL.md": "# One\n"}})
    fixture.write_plugin("survivor", skills={"one": {"SKILL.md": "# One\n"}})
    unowned = [fixture.destination / MARKET / "manual" / "SKILL.md", fixture.destination / CURSOR_LOCAL / "manual/x"]
    for path in unowned:
        path.parent.mkdir(parents=True)
        path.write_text("keep\n", encoding="utf-8")
    _apply(fixture)
    assert (fixture.destination / MARKET / "doomed/claude/skills/one/SKILL.md").is_file()
    assert (fixture.destination / CURSOR_LOCAL / "doomed/skills/one/SKILL.md").is_file()

    shutil.rmtree(fixture.authored / "overlay-plugins/doomed")
    _apply(fixture)

    assert not (fixture.destination / MARKET / "doomed").exists()
    assert not (fixture.destination / CURSOR_LOCAL / "doomed").exists()
    assert (fixture.destination / MARKET / "survivor/codex/skills/one/SKILL.md").is_file()
    assert all(path.read_text(encoding="utf-8") == "keep\n" for path in unowned)
    _assert_stable(fixture)


def test_deselected_plugin_host_and_environment_remove_roots(agent_source_fixture):
    """A deselected host, an absent skill, and a disabled environment leave the destination on apply."""
    fixture = agent_source_fixture
    _install_cleanup(fixture)
    skills = {name: {"SKILL.md": f"# {name}\n"} for name in ("one", "two", "three")}
    fixture.write_plugin("hosted", skills=skills)
    fixture.write_plugin("seasonal", skills={"one": {"SKILL.md": "# One\n"}})
    fixture.write_config(_capability("seasonal", environments=["default"]))
    _apply(fixture)
    destination = fixture.destination
    for host in HOSTS:
        assert (destination / MARKET / f"hosted/{host}/skills/two/SKILL.md").is_file()
    assert (destination / CURSOR_LOCAL / "hosted/skills/three/SKILL.md").is_file()
    assert (destination / MARKET / "seasonal/claude/skills/one/SKILL.md").is_file()

    fixture.write_config(
        _capability("hosted", hosts=["claude", "codex"], skills={"two": "codex", "three": "absent"})
        + _capability("seasonal", environments=["prod"])
    )
    _apply(fixture)

    assert not (destination / MARKET / "hosted/cursor").exists()
    assert not (destination / CURSOR_LOCAL / "hosted").exists()
    assert not (destination / MARKET / "hosted/claude/skills/two").exists()
    assert (destination / MARKET / "hosted/codex/skills/two/SKILL.md").is_file()
    for host in ("claude", "codex"):
        assert (destination / MARKET / f"hosted/{host}/skills/one/SKILL.md").is_file()
        assert not (destination / MARKET / f"hosted/{host}/skills/three").exists()
    assert not (destination / MARKET / "seasonal").exists()
    assert not (destination / CURSOR_LOCAL / "seasonal").exists()
    _assert_stable(fixture)
