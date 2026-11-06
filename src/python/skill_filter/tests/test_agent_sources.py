import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from skill_filter import agent_sources
from skill_filter.agent_sources import (
    AgentSourceError,
    discover,
    inventory_document,
    load_identity,
)


def _write(path: Path, text="x\n", mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    if mode is not None:
        path.chmod(mode)
    return path


def _plugin(authored: Path, directory: str, identity=None, skills=("one",)):
    root = authored / "overlay-plugins" / directory
    body = {"description": f"{directory} plugin"}
    body.update(identity or {})
    _write(root / "plugin.json", json.dumps(body))
    for skill in skills:
        _write(root / "skills" / skill / "SKILL.md", f"{skill}\n")
    return root


@pytest.fixture
def layout(tmp_path):
    """Return (root, source_root, authored) shaped like the overlay layout."""
    authored = tmp_path / "root" / "src"
    source_root = authored / "chezmoi"
    source_root.mkdir(parents=True)
    return tmp_path / "root", source_root, authored


def test_identity_defaults_name_to_directory(layout):
    _, _, authored = layout
    root = _plugin(authored, "domain-brain")
    identity = load_identity(root, authored)
    assert identity.name == "domain-brain"
    assert identity.skills_source_dir == root / "skills"
    assert identity.native_source is False
    assert identity.native_wrappers == ()
    assert identity.author is None


def test_identity_name_overrides_directory_for_installed_names(layout):
    _, source_root, authored = layout
    _plugin(authored, "writing", {"name": "mikekobit-writing"})
    _plugin(authored, "skill-feedback", {"name": "mkobit-skill-feedback"})
    inventory = discover(source_root)
    assert set(inventory.plugins) == {"mikekobit-writing", "mkobit-skill-feedback"}
    document = inventory_document(inventory)["agent_source_inventory"]
    assert (
        document["plugins"]["mikekobit-writing"]["source_dir"]
        == "src/overlay-plugins/writing"
    )


@pytest.mark.parametrize(
    ("identity", "message"),
    [
        ({"description": ""}, "description"),
        ({"surprise": 1}, "unknown identity key"),
        ({"name": "mkobit-dotfiles"}, "reserved"),
        ({"name": "Bad_Name"}, "invalid plugin name"),
        ({"native_wrappers": ["gemini"]}, "native_wrappers"),
        ({"native_source": "yes"}, "native_source"),
        ({"author": "me"}, "author"),
        ({"name": "same"}, "duplicate plugin name"),
    ],
)
def test_identity_rejects_missing_description_unknown_key_reserved_and_duplicate_name(
    layout, identity, message
):
    _, source_root, authored = layout
    _plugin(
        authored,
        "first",
        {"name": "same"} if message == "duplicate plugin name" else None,
    )
    _plugin(authored, "second", identity)
    with pytest.raises(AgentSourceError, match=message):
        discover(source_root)


def test_identity_missing_description_key(layout):
    _, _, authored = layout
    root = authored / "overlay-plugins" / "p"
    _write(root / "plugin.json", "{}")
    with pytest.raises(AgentSourceError, match="description"):
        load_identity(root, authored)


def test_plugin_directory_without_identity_fails(layout):
    _, source_root, authored = layout
    _write(authored / "overlay-plugins" / "AGENTS.md")
    (authored / "overlay-plugins" / "orphan").mkdir()
    with pytest.raises(AgentSourceError, match="missing plugin identity"):
        discover(source_root)


def test_skills_source_dir_reads_shared_overlay_skills(layout):
    _, source_root, authored = layout
    _write(authored / "overlay-skills" / "mermaid-sharing" / "SKILL.md")
    root = _plugin(
        authored,
        "stripe-dotfiles",
        {"skills_source_dir": "src/overlay-skills"},
        skills=(),
    )
    assert (
        load_identity(root, authored).skills_source_dir == authored / "overlay-skills"
    )
    document = inventory_document(discover(source_root))["agent_source_inventory"]
    plugin = document["plugins"]["stripe-dotfiles"]
    assert plugin["skills_source_dir"] == "src/overlay-skills"
    assert set(plugin["skills"]) == {"mermaid-sharing"}


def test_skills_source_dir_rejects_escape_and_symlink(layout):
    root, _, authored = layout
    (root / "outside").mkdir()
    (authored / "real").mkdir()
    (authored / "link").symlink_to(authored / "real")
    for value in ("../outside", "src/../outside", "/abs", "src/Bad", "src/missing"):
        plugin = _plugin(authored, "p", {"skills_source_dir": value})
        with pytest.raises(AgentSourceError):
            load_identity(plugin, authored)
        shutil.rmtree(plugin)
    plugin = _plugin(authored, "p", {"skills_source_dir": "src/link"})
    with pytest.raises(AgentSourceError, match="symlink"):
        load_identity(plugin, authored)


def test_bare_and_plugin_skills_discovered_from_skill_markdown_or_template(layout):
    _, source_root, authored = layout
    _write(authored / "ai" / "skills" / "AGENTS.md")
    _write(authored / "ai" / "skills" / "beads" / "SKILL.md")
    _write(authored / "ai" / "skills" / "tw" / "SKILL.md.tmpl", mode=0o755)
    plugin = _plugin(authored, "writing", skills=())
    _write(plugin / "skills" / "email" / "SKILL.md.tmpl")
    document = inventory_document(discover(source_root))["agent_source_inventory"]
    assert set(document["bare_skills"]) == {"beads", "tw"}
    record = document["bare_skills"]["tw"]["files"]["SKILL.md"]
    assert record["template"] is True
    assert record["executable"] is True
    assert record["source"] == "src/ai/skills/tw/SKILL.md.tmpl"
    assert set(document["plugins"]["writing"]["skills"]) == {"email"}


def test_skill_directory_without_skill_markdown_fails(layout):
    _, source_root, authored = layout
    _write(authored / "ai" / "skills" / "broken" / "README.md")
    with pytest.raises(AgentSourceError, match="SKILL.md"):
        discover(source_root)
    shutil.rmtree(authored / "ai" / "skills" / "broken")
    plugin = _plugin(authored, "p", skills=())
    _write(plugin / "skills" / "broken" / "README.md")
    with pytest.raises(AgentSourceError, match="SKILL.md"):
        discover(source_root)


def test_wrapper_components_detect_mcp_and_rules(layout):
    _, source_root, authored = layout
    plugin = _plugin(authored, "toolshed-mcp")
    _write(plugin / "wrappers" / "claude" / ".mcp.json.tmpl", "{}")
    _write(plugin / "wrappers" / "cursor" / "rules" / "g.mdc.tmpl")
    (plugin / "wrappers" / "codex").mkdir()
    wrappers = inventory_document(discover(source_root))["agent_source_inventory"][
        "plugins"
    ]["toolshed-mcp"]["wrappers"]
    assert wrappers["claude"]["components"] == {"mcpServers": "./.mcp.json"}
    assert wrappers["cursor"]["components"] == {"rules": "./rules"}
    assert wrappers["codex"] == {"dirs": [], "files": {}, "components": {}}
    assert "rules/g.mdc" in wrappers["cursor"]["files"]
    (plugin / "wrappers" / "gemini").mkdir()
    with pytest.raises(AgentSourceError, match="unknown wrapper"):
        discover(source_root)


def test_native_trees_parse_chezmoi_names(layout):
    _, source_root, authored = layout
    plugin = _plugin(authored, "nat", {"native_source": True}, skills=())
    _write(plugin / "skills" / "exact_foo" / "executable_SKILL.md.tmpl")
    _write(plugin / "skills" / "exact_foo" / "empty_dot_keep-me")
    _write(plugin / "wrappers" / "claude" / "exact_rules" / ".keep", "")
    document = inventory_document(discover(source_root))["agent_source_inventory"]
    files = document["plugins"]["nat"]["skills"]["foo"]["files"]
    assert files["SKILL.md"]["executable"] and files["SKILL.md"]["template"]
    assert files[".keep-me"]["empty"]
    assert document["plugins"]["nat"]["wrappers"]["claude"]["components"] == {
        "rules": "./rules"
    }
    _write(plugin / "skills" / "exact_foo" / "run_bad.sh")
    with pytest.raises(AgentSourceError, match="forbidden prefix"):
        discover(source_root)


def test_inventory_digest_ignores_absolute_location_and_tracks_bytes_and_modes(
    tmp_path,
):
    def build(name):
        authored = tmp_path / name / "src"
        (authored / "chezmoi").mkdir(parents=True)
        _write(authored / "ai" / "skills" / "beads" / "SKILL.md", "a\n")
        _plugin(authored, "writing")
        return authored

    first, second = build("one"), build("two")

    def digest(authored):
        return inventory_document(discover(authored / "chezmoi"))[
            "agent_source_inventory"
        ]["source_digest"]

    assert digest(first) == digest(second)
    skill = second / "ai" / "skills" / "beads" / "SKILL.md"
    skill.write_text("b\n", encoding="utf-8")
    changed_bytes = digest(second)
    assert changed_bytes != digest(first)
    skill.chmod(0o755)
    assert digest(second) != changed_bytes
    skill.write_text("a\n", encoding="utf-8")
    skill.chmod(0o644)
    assert digest(second) == digest(first)


def test_build_artifacts_are_skipped(layout):
    _, source_root, authored = layout
    skill = authored / "ai" / "skills" / "beads"
    _write(skill / "SKILL.md")
    _write(skill / "__pycache__" / "x.pyc")
    _write(skill / "mod.pyc")
    _write(skill / ".DS_Store")
    _write(authored / "ai" / "skills" / "__pycache__" / "y.pyc")
    document = inventory_document(discover(source_root))["agent_source_inventory"]
    assert list(document["bare_skills"]["beads"]["files"]) == ["SKILL.md"]
    assert document["bare_skills"]["beads"]["dirs"] == []


def test_source_symlink_is_rejected(layout):
    _, source_root, authored = layout
    skill = authored / "ai" / "skills" / "beads"
    _write(skill / "SKILL.md")
    (skill / "link").symlink_to(skill / "SKILL.md")
    with pytest.raises(AgentSourceError, match="symlink"):
        discover(source_root)


def test_empty_directories_and_files_are_recorded(layout):
    _, source_root, authored = layout
    skill = authored / "ai" / "skills" / "beads"
    _write(skill / "SKILL.md")
    _write(skill / "empty.txt", "")
    (skill / "references").mkdir()
    entry = inventory_document(discover(source_root))["agent_source_inventory"][
        "bare_skills"
    ]["beads"]
    assert entry["dirs"] == ["references"]
    assert entry["files"]["empty.txt"]["empty"] is True


def test_runs_on_python_38_without_site_packages(layout):
    _, source_root, authored = layout
    _write(authored / "ai" / "skills" / "beads" / "SKILL.md")
    command = [sys.executable, "-S", agent_sources.__file__]
    result = subprocess.run(
        [*command, "--help"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    result = subprocess.run(
        [*command, str(source_root)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["agent_source_inventory"]["schema"] == 1


def test_symlinked_skill_and_plugin_directories_fail(layout, tmp_path):
    _, source_root, authored = layout
    elsewhere = tmp_path / "elsewhere"
    _write(elsewhere / "SKILL.md")
    (authored / "ai" / "skills").mkdir(parents=True)
    (authored / "ai" / "skills" / "foo").symlink_to(elsewhere)
    with pytest.raises(AgentSourceError, match="symlink"):
        discover(source_root)
    (authored / "ai" / "skills" / "foo").unlink()
    plugin = _plugin(authored, "real")
    (authored / "overlay-plugins" / "linked").symlink_to(plugin)
    with pytest.raises(AgentSourceError, match="symlink"):
        discover(source_root)
    (authored / "overlay-plugins" / "linked").unlink()
    shutil.rmtree(plugin / "skills")
    (plugin / "skills").symlink_to(elsewhere)
    with pytest.raises(AgentSourceError, match="symlink"):
        discover(source_root)


@pytest.mark.parametrize(
    "native_name", ["dot_chezmoiignore", "literal_.chezmoiignore", "dot_chezmoi.toml"]
)
def test_chezmoi_control_targets_are_rejected(layout, native_name):
    _, source_root, authored = layout
    plugin = _plugin(authored, "nat", {"native_source": True}, skills=())
    _write(plugin / "skills" / "foo" / "SKILL.md")
    _write(plugin / "skills" / "foo" / native_name)
    with pytest.raises(AgentSourceError, match="reserved chezmoi"):
        discover(source_root)


def test_literal_chezmoi_control_target_and_bare_tmpl_name_are_rejected(layout):
    _, source_root, authored = layout
    skill = authored / "ai" / "skills" / "beads"
    _write(skill / "SKILL.md")
    _write(skill / ".chezmoiignore.tmpl")
    with pytest.raises(AgentSourceError, match="reserved chezmoi"):
        discover(source_root)
    (skill / ".chezmoiignore.tmpl").unlink()
    _write(skill / ".tmpl")
    with pytest.raises(AgentSourceError, match="empty target"):
        discover(source_root)


def test_native_executable_comes_from_prefix_only_and_literal_from_mode(layout):
    _, source_root, authored = layout
    plugin = _plugin(authored, "nat", {"native_source": True}, skills=())
    _write(plugin / "skills" / "foo" / "SKILL.md", mode=0o755)
    _write(plugin / "skills" / "foo" / "executable_run.sh")
    bare = authored / "ai" / "skills" / "beads"
    _write(bare / "SKILL.md", mode=0o755)
    document = inventory_document(discover(source_root))["agent_source_inventory"]
    native = document["plugins"]["nat"]["skills"]["foo"]["files"]
    assert native["SKILL.md"]["executable"] is False
    assert native["run.sh"]["executable"] is True
    assert document["bare_skills"]["beads"]["files"]["SKILL.md"]["executable"] is True


def test_directory_and_file_target_collisions_fail(layout):
    _, source_root, authored = layout
    plugin = _plugin(authored, "nat", {"native_source": True}, skills=())
    _write(plugin / "skills" / "foo" / "SKILL.md")
    _write(plugin / "skills" / "foo" / "exact_x" / "a")
    _write(plugin / "skills" / "foo" / "x" / "b")
    with pytest.raises(AgentSourceError, match="two sources map"):
        discover(source_root)


@pytest.mark.parametrize("root", ["ai/skills", "overlay-plugins"])
def test_symlinked_discovery_roots_fail(layout, tmp_path, root):
    _, source_root, authored = layout
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (authored / root).parent.mkdir(parents=True, exist_ok=True)
    (authored / root).symlink_to(elsewhere)
    with pytest.raises(AgentSourceError, match="symlink"):
        discover(source_root)


def test_symlinked_wrapper_host_directory_fails(layout, tmp_path):
    _, source_root, authored = layout
    plugin = _plugin(authored, "p")
    (tmp_path / "elsewhere").mkdir()
    (plugin / "wrappers").mkdir()
    (plugin / "wrappers" / "claude").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(AgentSourceError, match="unknown wrapper"):
        discover(source_root)


def test_hidden_bare_skill_and_plugin_directories_fail(layout):
    _, source_root, authored = layout
    _write(authored / "ai" / "skills" / ".chezmoiignore" / "SKILL.md")
    with pytest.raises(AgentSourceError, match="invalid skill name"):
        discover(source_root)
    shutil.rmtree(authored / "ai" / "skills" / ".chezmoiignore")
    _plugin(authored, ".hidden")
    with pytest.raises(AgentSourceError, match="hidden"):
        discover(source_root)


def test_directory_and_file_collision_fails(layout):
    _, source_root, authored = layout
    plugin = _plugin(authored, "nat", {"native_source": True}, skills=())
    _write(plugin / "skills" / "foo" / "SKILL.md")
    _write(plugin / "skills" / "foo" / "exact_x" / "a")
    _write(plugin / "skills" / "foo" / "x")
    with pytest.raises(AgentSourceError, match="two sources map"):
        discover(source_root)


# Projection and publication.

MARKET = "dot_local/share/agent-plugins/marketplace/plugins"
LOCAL = "dot_cursor/plugins/local"
HOSTS_ = ("claude", "codex", "cursor")
LAUNCHER = Path(agent_sources.__file__).resolve().parent.parent / (
    "prepare-agent-sources.sh"
)


def _fixture(authored: Path):
    _write(authored / "ai" / "skills" / "beads" / "SKILL.md", "beads\n")
    _plugin(authored, "domain-brain", skills=("records",))


def _snapshot(root: Path):
    state = {}
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        data = path.read_bytes() if path.is_file() else None
        state[path.relative_to(root).as_posix()] = (
            info.st_mode,
            info.st_ino,
            info.st_mtime_ns,
            data,
        )
    return state


def _manifest(source_root: Path):
    path = source_root / agent_sources.MANIFEST_NAME
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("name", "flags", "expected"),
    [
        (".hidden", {"kind": "file"}, "dot_hidden"),
        ("exact_notes.md", {"kind": "file"}, "literal_exact_notes.md"),
        ("private_x", {"kind": "dir", "exact": True}, "exact_literal_private_x"),
        ("run.sh", {"kind": "file", "executable": True}, "executable_run.sh"),
        ("x", {"kind": "file", "empty": True}, "empty_x"),
        ("SKILL.md", {"kind": "file", "template": True}, "SKILL.md.tmpl"),
        (
            "SKILL.md",
            {"kind": "file", "template": True, "executable": True},
            "executable_SKILL.md.tmpl",
        ),
    ],
)
def test_encode_literal_names(name, flags, expected):
    encoded = agent_sources.encode_name(name, **flags)
    assert encoded == expected
    assert agent_sources.source_target_name(encoded) == name


@pytest.mark.parametrize("name", ["..", "a/b", "x.literal"])
def test_encode_rejects_unsafe_names(name):
    with pytest.raises(AgentSourceError, match="unsafe target name"):
        agent_sources.encode_name(name, kind="file")


def test_native_tree_copied_verbatim_with_forced_exact_root(layout):
    _, source_root, authored = layout
    plugin = _plugin(authored, "nat", {"native_source": True}, skills=())
    _write(plugin / "skills" / "private_foo" / "executable_SKILL.md.tmpl")
    _write(plugin / "skills" / "private_foo" / "exact_refs" / ".keep", "")
    _write(plugin / "skills" / "exact_bar" / "SKILL.md")
    _write(plugin / "wrappers" / "claude" / "dot_mcp.json.tmpl", "{}", mode=0o600)
    plan = agent_sources.plan_projection(source_root, discover(source_root))
    host = f"{MARKET}/exact_nat/exact_claude"
    skill = f"{host}/exact_skills/exact_private_foo"
    assert plan[f"{skill}/executable_SKILL.md.tmpl"].data == b"x\n"
    assert plan[f"{skill}/exact_refs/.keep"].data == b""
    assert f"{host}/exact_skills/exact_bar/SKILL.md" in plan
    assert plan[f"{host}/dot_mcp.json.tmpl"].mode == 0o600
    assert f"{LOCAL}/exact_nat/exact_skills/exact_private_foo" in plan


@pytest.mark.parametrize(
    "case", ["run_x.sh", "symlink", "dot_chezmoiignore", "modify_x"]
)
def test_native_tree_rejects_scripts_symlink_and_control_names(layout, case):
    _, source_root, authored = layout
    plugin = _plugin(authored, "nat", {"native_source": True}, skills=())
    skill = plugin / "skills" / "foo"
    _write(skill / "SKILL.md")
    if case == "symlink":
        (skill / "link").symlink_to(skill / "SKILL.md")
    else:
        _write(skill / case)
    with pytest.raises(AgentSourceError):
        agent_sources.prepare(source_root)
    assert not (source_root / agent_sources.MANIFEST_NAME).exists()
    assert not (source_root / agent_sources.INVENTORY_PATH).exists()


def test_projection_layout_matches_resolved_table(layout):
    _, source_root, authored = layout
    _fixture(authored)
    plan = agent_sources.plan_projection(source_root, discover(source_root))
    bare_roots = [
        f"{MARKET}/mkobit-dotfiles/skills",
        f"{MARKET}/mkobit-dotfiles/claude/skills",
        f"{MARKET}/mkobit-dotfiles/codex/skills",
        f"{MARKET}/mkobit-dotfiles/cursor/skills",
        f"{LOCAL}/mkobit-dotfiles/skills",
        "dot_gemini/antigravity-cli/skills",
    ]
    expected = {
        ".chezmoidata/agent-source-inventory.json",
        f"{MARKET}/.chezmoiignore.tmpl",
        f"{LOCAL}/.chezmoiignore.tmpl",
        "dot_gemini/antigravity-cli/skills/.chezmoiignore.tmpl",
        f"{MARKET}/exact_domain-brain",
    }
    for root in bare_roots:
        expected |= {root, f"{root}/exact_beads", f"{root}/exact_beads/SKILL.md"}
    views = [(f"{MARKET}/exact_domain-brain/exact_{host}", host) for host in HOSTS_] + [
        (f"{LOCAL}/exact_domain-brain", "cursor")
    ]
    for root, host in views:
        expected |= {
            root,
            f"{root}/exact_dot_{host}-plugin",
            f"{root}/exact_dot_{host}-plugin/plugin.json.tmpl",
            f"{root}/exact_skills",
            f"{root}/exact_skills/exact_records",
            f"{root}/exact_skills/exact_records/SKILL.md",
        }
    assert set(plan) == expected
    assert agent_sources.top_level_paths(plan) == sorted(
        [
            ".chezmoidata/agent-source-inventory.json",
            f"{MARKET}/.chezmoiignore.tmpl",
            f"{LOCAL}/.chezmoiignore.tmpl",
            f"{MARKET}/exact_domain-brain",
            f"{LOCAL}/exact_domain-brain",
            *bare_roots,
        ]
    )
    assert plan[
        f"{LOCAL}/exact_domain-brain/exact_dot_cursor-plugin/plugin.json.tmpl"
    ].data == (
        b'{{- includeTemplate "ai/authored-plugin-manifest" '
        b'(dict "root" . "name" "domain-brain" "host" "cursor") -}}\n'
    )
    assert plan[f"{MARKET}/.chezmoiignore.tmpl"].data == (
        b'{{- includeTemplate "ai/agent-source-ignore" '
        b'(dict "root" . "view" "marketplace-plugins") -}}\n'
    )
    inventory = plan[".chezmoidata/agent-source-inventory.json"].data.decode()
    assert inventory == (
        json.dumps(inventory_document(discover(source_root)), indent=2, sort_keys=True)
        + "\n"
    )


def test_rejects_target_collision_with_canonical_sibling(layout):
    _, source_root, authored = layout
    _fixture(authored)
    _write(source_root / MARKET / "domain-brain" / "plugin.json")
    with pytest.raises(AgentSourceError, match="same target"):
        agent_sources.prepare(source_root)
    assert not (source_root / agent_sources.MANIFEST_NAME).exists()


def test_rejects_canonical_ignore_at_generated_control_path(layout):
    _, source_root, authored = layout
    _fixture(authored)
    _write(source_root / LOCAL / ".chezmoiignore", "x\n")
    with pytest.raises(AgentSourceError, match="control file"):
        agent_sources.prepare(source_root)
    assert not (source_root / agent_sources.MANIFEST_NAME).exists()


@pytest.mark.parametrize(
    "wrapper_file",
    [
        ".claude-plugin/plugin.json",
        ".claude-plugin/plugin.json.tmpl",
        "skills/x/SKILL.md",
    ],
)
def test_rejects_wrapper_manifest_and_wrapper_under_skills(layout, wrapper_file):
    _, source_root, authored = layout
    plugin = _plugin(authored, "p")
    _write(plugin / "wrappers" / "claude" / wrapper_file)
    with pytest.raises(AgentSourceError, match="wrapper"):
        agent_sources.prepare(source_root)


@pytest.mark.parametrize(
    ("identity", "names"),
    [
        ({}, ["a", "a.tmpl"]),
        ({"native_wrappers": ["claude"]}, ["dot_claude-plugin/extra.json"]),
    ],
)
def test_rejects_template_plain_collision(layout, identity, names):
    _, source_root, authored = layout
    plugin = _plugin(authored, "p", identity)
    for name in names:
        _write(plugin / "wrappers" / "claude" / name)
    with pytest.raises(AgentSourceError, match="two sources map"):
        agent_sources.prepare(source_root)


def test_failed_preparation_leaves_previous_tree_and_manifest_unchanged(layout):
    _, source_root, authored = layout
    _fixture(authored)
    assert agent_sources.prepare(source_root) is True
    before = _snapshot(source_root)
    skill = authored / "ai" / "skills" / "beads"
    _write(skill / "changed.md")
    (skill / "link").symlink_to(skill / "SKILL.md")
    with pytest.raises(AgentSourceError, match="symlink"):
        agent_sources.prepare(source_root)
    assert _snapshot(source_root) == before


def test_publishing_manifest_recovers_after_interrupted_publish(layout, monkeypatch):
    _, source_root, authored = layout
    _fixture(authored)
    assert agent_sources.prepare(source_root) is True
    _write(authored / "ai" / "skills" / "beads" / "SKILL.md", "changed\n")
    real_replace = os.replace
    calls = []

    def crash_after_manifest(source, destination):
        calls.append(destination)
        if len(calls) == 3:
            raise OSError("simulated crash")
        real_replace(source, destination)

    with monkeypatch.context() as patch:
        patch.setattr(agent_sources.os, "replace", crash_after_manifest)
        with pytest.raises(OSError, match="simulated crash"):
            agent_sources.prepare(source_root)
    interrupted = _manifest(source_root)
    assert interrupted["state"] == "publishing"
    assert interrupted["digest"] is None
    assert agent_sources.prepare(source_root) is True
    manifest = _manifest(source_root)
    assert manifest["state"] == "complete"
    assert not (source_root / agent_sources.STAGING_NAME).exists()
    plan = agent_sources.plan_projection(source_root, discover(source_root))
    assert manifest["paths"] == agent_sources.top_level_paths(plan)
    assert manifest["digest"] == agent_sources.digest(plan)
    for path, entry in plan.items():
        if entry.kind == "file":
            assert (source_root / path).read_bytes() == entry.data
    portable = source_root / MARKET / "mkobit-dotfiles/skills/exact_beads/SKILL.md"
    assert portable.read_text(encoding="utf-8") == "changed\n"


def test_unchanged_sources_do_not_rewrite(layout):
    _, source_root, authored = layout
    _fixture(authored)
    assert agent_sources.prepare(source_root) is True
    inventory = source_root / agent_sources.INVENTORY_PATH
    manifest = source_root / agent_sources.MANIFEST_NAME
    before = [(p.stat().st_ino, p.stat().st_mtime_ns) for p in (inventory, manifest)]
    assert agent_sources.prepare(source_root) is False
    after = [(p.stat().st_ino, p.stat().st_mtime_ns) for p in (inventory, manifest)]
    assert after == before


def test_stale_generated_paths_listed_in_manifest_are_replaced_not_merged(layout):
    _, source_root, authored = layout
    _fixture(authored)
    old = _plugin(authored, "old-plugin")
    extra = _write(authored / "ai" / "skills" / "beads" / "extra.md")
    assert agent_sources.prepare(source_root) is True
    portable = source_root / MARKET / "mkobit-dotfiles/skills/exact_beads"
    assert (portable / "extra.md").exists()
    _write(portable / "stray.md")
    shutil.rmtree(old)
    extra.unlink()
    assert agent_sources.prepare(source_root) is True
    assert not (source_root / MARKET / "exact_old-plugin").exists()
    assert not (source_root / LOCAL / "exact_old-plugin").exists()
    assert sorted(p.name for p in portable.iterdir()) == ["SKILL.md"]
    assert f"{MARKET}/exact_old-plugin" not in _manifest(source_root)["paths"]


def test_unlisted_preexisting_generated_path_fails(layout):
    _, source_root, authored = layout
    _fixture(authored)
    _write(source_root / LOCAL / "exact_domain-brain" / "keep.md")
    before = _snapshot(source_root)
    with pytest.raises(AgentSourceError, match="not in the manifest"):
        agent_sources.prepare(source_root)
    after = _snapshot(source_root)
    after.pop(agent_sources.LOCK_NAME)
    assert after == before


def test_symlinked_generated_path_component_fails(layout, tmp_path):
    _, source_root, authored = layout
    _fixture(authored)
    (tmp_path / "elsewhere").mkdir()
    (source_root / "dot_cursor").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(AgentSourceError, match="symlink"):
        agent_sources.prepare(source_root)
    assert list((tmp_path / "elsewhere").iterdir()) == []


def test_concurrent_prepare_serializes_on_lock(layout):
    import fcntl
    import time

    _, source_root, authored = layout
    _fixture(authored)
    module_dir = str(Path(agent_sources.__file__).resolve().parent)
    code = (
        "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); "
        "import agent_sources; print(agent_sources.prepare(Path(sys.argv[2])))"
    )
    lock = os.open(str(source_root / agent_sources.LOCK_NAME), os.O_RDWR | os.O_CREAT)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        runs = [
            subprocess.Popen(
                [sys.executable, "-S", "-c", code, module_dir, str(source_root)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for _ in range(2)
        ]
        time.sleep(0.5)
        assert [run.poll() for run in runs] == [None, None]
    finally:
        os.close(lock)
    results = [run.communicate(timeout=60) for run in runs]
    assert [run.returncode for run in runs] == [0, 0], results
    assert sorted(out.strip() for out, _ in results) == ["False", "True"]
    assert _manifest(source_root)["state"] == "complete"


def test_cli_prepare_and_list_generated(layout):
    _, source_root, authored = layout
    command = [sys.executable, "-S", agent_sources.__file__]
    listed = subprocess.run(
        [*command, "list-generated", "--source-root", str(source_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (listed.returncode, listed.stdout) == (0, "")
    _fixture(authored)
    prepared = subprocess.run(
        [*command, "prepare", "--source-root", str(source_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert prepared.returncode == 0, prepared.stderr
    listed = subprocess.run(
        [*command, "list-generated", "--source-root", str(source_root)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert listed.stdout.splitlines() == _manifest(source_root)["paths"]
    _write(source_root / LOCAL / ".chezmoiignore")
    failed = subprocess.run(
        [*command, "prepare", "--source-root", str(source_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert failed.returncode == 1
    assert failed.stderr.startswith("agent-sources: canonical control file")


def test_launcher_runs_with_system_python(layout):
    _, source_root, authored = layout
    _fixture(authored)
    result = subprocess.run(
        ["sh", str(LAUNCHER), str(source_root), "/nonexistent"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert (source_root / agent_sources.INVENTORY_PATH).is_file()
    assert _manifest(source_root)["state"] == "complete"


@pytest.mark.skipif(shutil.which("chezmoi") is None, reason="chezmoi is not installed")
def test_projection_applies_with_plain_chezmoi(layout, tmp_path):
    _, source_root, authored = layout
    skill = authored / "ai" / "skills" / "beads"
    _write(skill / "SKILL.md", "beads\n")
    _write(skill / "scripts" / "run.sh", "#!/bin/sh\n", mode=0o755)
    _write(skill / "empty.txt", "")
    _write(skill / ".hidden", "h\n")
    _write(skill / "exact_notes.md", "n\n")
    (skill / "assets").mkdir()
    plugin = _plugin(authored, "domain-brain", skills=())
    _write(plugin / "skills" / "records" / "SKILL.md.tmpl", '{{ "rendered" }}\n')
    _write(plugin / "wrappers" / "claude" / ".mcp.json.tmpl", "{}\n", mode=0o755)
    templates = source_root / ".chezmoitemplates" / "ai"
    _write(templates / "authored-plugin-manifest", '{"name": "{{ .name }}"}\n')
    _write(templates / "agent-source-ignore", "")
    assert agent_sources.prepare(source_root) is True
    dest = tmp_path / "dest"
    dest.mkdir()
    config = _write(tmp_path / "c.toml", "")
    result = subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source_root),
            "--destination",
            str(dest),
            "--config",
            str(config),
            "--cache",
            str(tmp_path / "cache"),
            "--persistent-state",
            str(tmp_path / "state.boltdb"),
            "apply",
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "HOME": str(tmp_path)},
    )
    assert result.returncode == 0, result.stderr
    market = dest / ".local/share/agent-plugins/marketplace/plugins"
    for view in (
        market / "mkobit-dotfiles/skills/beads",
        market / "mkobit-dotfiles/claude/skills/beads",
        dest / ".cursor/plugins/local/mkobit-dotfiles/skills/beads",
        dest / ".gemini/antigravity-cli/skills/beads",
    ):
        assert (view / "SKILL.md").read_text(encoding="utf-8") == "beads\n"
        assert (view / "scripts/run.sh").stat().st_mode & 0o111
        assert (view / "empty.txt").read_bytes() == b""
        assert (view / ".hidden").read_text(encoding="utf-8") == "h\n"
        assert (view / "exact_notes.md").read_text(encoding="utf-8") == "n\n"
        assert (view / "assets").is_dir()
        assert list((view / "assets").iterdir()) == []
    for root, host in [
        (market / "domain-brain/claude", "claude"),
        (market / "domain-brain/codex", "codex"),
        (dest / ".cursor/plugins/local/domain-brain", "cursor"),
    ]:
        manifest = root / f".{host}-plugin/plugin.json"
        assert json.loads(manifest.read_text(encoding="utf-8")) == {
            "name": "domain-brain"
        }
        records = root / "skills/records/SKILL.md"
        assert records.read_text(encoding="utf-8") == "rendered\n"
    assert (market / "domain-brain/claude/.mcp.json").read_text() == "{}\n"
    assert not (market / "domain-brain/codex/.mcp.json").exists()
