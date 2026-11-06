import json
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
