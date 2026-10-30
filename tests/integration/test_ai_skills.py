import hashlib
import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml
from chezmoi_test_data import installation_method

# Antigravity remains a direct skill consumer.
DIRECT_SKILL_DIRS = [
    pytest.param(Path(".gemini/antigravity-cli/skills"), frozenset(), id="antigravity"),
]

# Claude, Codex, and Cursor consume host-specific views of the capability bundle.
CAPABILITY_PLUGIN_DIRS = [
    pytest.param(
        Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/claude"),
        "claude",
        id="claude",
    ),
    pytest.param(
        Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/codex"),
        "codex",
        id="codex",
    ),
    pytest.param(
        Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/cursor"),
        "cursor",
        id="cursor",
    ),
]

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AUTHORED_CLEANUP_SCRIPT = (
    REPOSITORY_ROOT / "src/chezmoi/.chezmoiscripts/run_onchange_after_00-agent-plugin-authored-skills-cleanup.sh.tmpl"
)
AUTHORED_SKILLS_EXTERNAL = REPOSITORY_ROOT / "src/chezmoi/.chezmoiexternals/ai-authored-skills.toml.tmpl"
CURSOR_LOCAL_SKILLS_REMOVE = (
    REPOSITORY_ROOT / "src/chezmoi/dot_cursor/plugins/local/mkobit-dotfiles/.chezmoiremove.tmpl"
)
CURSOR_LOCAL_PLUGIN_MANIFEST = (
    REPOSITORY_ROOT / "src/chezmoi/dot_cursor/plugins/local/mkobit-dotfiles/exact_dot_cursor-plugin/plugin.json.tmpl"
)
CAPABILITY_PACKAGE_SKILLS_REMOVE = (
    REPOSITORY_ROOT
    / "src/chezmoi/dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/.chezmoiremove.tmpl"
)
FILTER_INTERPRETER_TEMPLATE = REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/python/filter-interpreter"
FILTER_INTERPRETER_RESOLVER = REPOSITORY_ROOT / "src/python/skill_filter/resolve-interpreter.sh"
AUTHORED_SKILL_ROOTS = {
    "portable": Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills"),
    "claude": Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/claude/skills"),
    "codex": Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/codex/skills"),
    "cursor": Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/cursor/skills"),
    "cursor-local": Path(".cursor/plugins/local/mkobit-dotfiles/skills"),
    "antigravity": Path(".gemini/antigravity-cli/skills"),
}
CAPABILITY_AUTHORED_SKILL_ROOTS = {
    root_name: root for root_name, root in AUTHORED_SKILL_ROOTS.items() if root_name != "antigravity"
}
CAPABILITY_MANIFEST_TEMPLATES = (
    Path("dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/plugin.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/claude/dot_claude-plugin/plugin.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/codex/dot_codex-plugin/plugin.json.tmpl"),
    Path("dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/cursor/dot_cursor-plugin/plugin.json.tmpl"),
)


def _entries(directory: Path) -> list[Path]:
    return [entry for entry in sorted(directory.iterdir()) if entry.name != ".DS_Store"]


def assert_is_skill(entry: Path) -> None:
    """Assert a directory is a skill: it holds a non-empty SKILL.md."""
    skill_md = entry / "SKILL.md"
    assert skill_md.is_file(), f"{entry} is missing SKILL.md"
    assert skill_md.stat().st_size > 0, f"{skill_md} is empty"


def assert_entries_are_valid_skills(skills_dir: Path, allowed_marker_files: frozenset[Path] = frozenset()) -> None:
    """Assert every entry is a skill, or a namespace whose children are skills.

    Claude Code discovers one level of nesting, so slack/format-message/SKILL.md is
    a real skill rather than a broken deployment — plugin-provided and
    overlay-authored skills both arrive this way. An entry with no SKILL.md of its
    own is therefore treated as a namespace and its children are checked instead,
    which is why a flat-only assertion reported healthy deployments as failures.
    """
    for entry in _entries(skills_dir):
        assert entry.is_dir(), f"{entry} is not a directory; deployed skills must be directories"
        if (entry / "SKILL.md").is_file():
            assert_is_skill(entry)
            continue

        nested = _entries(entry)
        assert nested, f"{entry} has neither a SKILL.md nor any nested skills"
        for child in nested:
            relative_child = child.relative_to(skills_dir)
            if relative_child in allowed_marker_files:
                assert child.is_file(), f"allowed marker {child} is not a file"
                continue
            assert child.is_dir(), (
                f"{child} is not a directory, but {entry} has no SKILL.md so it must be a namespace of skills"
            )
            assert_is_skill(child)


def _apply_authored_cleanup(source: Path, destination: Path, config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--config",
            str(config),
            "--refresh-externals=always",
            "apply",
        ],
        capture_output=True,
        check=False,
        cwd=destination.parent,
        text=True,
    )


def _initialize_authored_cleanup_source(source: Path, *, include_external: bool = False) -> None:
    source_root = source / "src/chezmoi"
    source_files = [
        (AUTHORED_CLEANUP_SCRIPT, Path(".chezmoiscripts") / AUTHORED_CLEANUP_SCRIPT.name),
        (
            CURSOR_LOCAL_SKILLS_REMOVE,
            Path("dot_cursor/plugins/local/mkobit-dotfiles/.chezmoiremove.tmpl"),
        ),
        (
            CURSOR_LOCAL_PLUGIN_MANIFEST,
            Path("dot_cursor/plugins/local/mkobit-dotfiles/exact_dot_cursor-plugin/plugin.json.tmpl"),
        ),
        (
            CAPABILITY_PACKAGE_SKILLS_REMOVE,
            Path("dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/.chezmoiremove.tmpl"),
        ),
        (FILTER_INTERPRETER_TEMPLATE, Path(".chezmoitemplates/python/filter-interpreter")),
        (FILTER_INTERPRETER_RESOLVER, Path("src/python/skill_filter/resolve-interpreter.sh")),
    ]
    source_files.extend(
        (REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/ai" / name, Path(".chezmoitemplates/ai") / name)
        for name in ("authored-render-context", "authored-file-digest", "authored-base-version")
    )
    if include_external:
        source_files.append(
            (
                REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/ai/authored-file-entry",
                Path(".chezmoitemplates/ai/authored-file-entry"),
            )
        )
        source_files.append((AUTHORED_SKILLS_EXTERNAL, Path(".chezmoiexternals") / AUTHORED_SKILLS_EXTERNAL.name))
    for source_file, relative_target in source_files:
        assert source_file.is_file(), f"missing cleanup fixture dependency: {source_file}"
        target = source_root / relative_target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)
    (source / ".chezmoiroot").write_text("src/chezmoi\n", encoding="utf-8")
    resolver = source / "src/python/skill_filter/resolve-interpreter.sh"
    resolver.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FILTER_INTERPRETER_RESOLVER, resolver)
    subprocess.run(["git", "init", "--quiet", str(source)], check=True)


def _render_capability_manifest_versions(source: Path, destination: Path, config: Path) -> dict[str, str]:
    """Render all base capability manifests and return their version strings."""
    result = subprocess.run(
        ["chezmoi", "--source", str(source), "--destination", str(destination), "--config", str(config), "apply"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    manifest_paths = {
        "root": destination / ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/plugin.json",
        "claude": destination
        / ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/claude/.claude-plugin/plugin.json",
        "codex": destination
        / ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/codex/.codex-plugin/plugin.json",
        "cursor": destination
        / ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/cursor/.cursor-plugin/plugin.json",
    }
    return {name: json.loads(path.read_text(encoding="utf-8"))["version"] for name, path in manifest_paths.items()}


def _assert_valid_capability_metadata(manifest: dict[str, object]) -> None:
    """Keep every rendered capability manifest compatible with Codex ingestion."""
    assert manifest["author"] == {"name": "mkobit"}
    assert manifest["interface"] == {
        "displayName": "mkobit dotfiles",
        "shortDescription": "Reusable dotfiles skills.",
        "longDescription": "Reusable skills for configuring and operating mkobit's development environment.",
        "developerName": "mkobit",
        "category": "Developer tools",
        "capabilities": ["Skills"],
        "defaultPrompt": "Help me use the dotfiles skills.",
    }


def test_capability_manifest_versions_ignore_legacy_overlay_source(tmp_path):
    """Base capability versions only depend on base-projected skill inputs."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    destination.mkdir()
    for relative_path in CAPABILITY_MANIFEST_TEMPLATES:
        template = source / relative_path
        template.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPOSITORY_ROOT / "src/chezmoi" / relative_path, template)

    for name in ("authored-render-context", "authored-file-digest", "authored-base-version"):
        target = source / ".chezmoitemplates/ai" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/ai" / name, target)

    base_skill = source.parent / "ai/skills/base/SKILL.md"
    base_skill.parent.mkdir(parents=True)
    base_skill.write_text("# Base\n", encoding="utf-8")
    first_overlay = tmp_path / "first-overlay"
    second_overlay = tmp_path / "second-overlay"
    first_overlay.mkdir()
    second_overlay.mkdir()
    (first_overlay / "SKILL.md").write_text("# First\n", encoding="utf-8")
    (second_overlay / "SKILL.md").write_text("# Second\n", encoding="utf-8")

    def config_for(overlay_source: Path) -> Path:
        config = tmp_path / f"{overlay_source.name}.toml"
        config.write_text(
            "\n".join(
                [
                    "[data.ai.skills]",
                    f"overlay_authored_source = {json.dumps(str(overlay_source))}",
                    "",
                    "[data.ai.skills.authored]",
                    "",
                    "[data.ai.skills.external]",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return config

    first_versions = _render_capability_manifest_versions(source, destination, config_for(first_overlay))
    second_versions = _render_capability_manifest_versions(source, destination, config_for(second_overlay))

    assert first_versions == second_versions


@pytest.mark.parametrize(
    ("state", "antigravity_enabled", "expected_roots"),
    [
        ("present", True, frozenset(CAPABILITY_AUTHORED_SKILL_ROOTS)),
        ("claude", True, frozenset({"claude"})),
        ("antigravity", True, frozenset()),
        ("present", False, frozenset({"portable", "claude", "codex", "cursor", "cursor-local"})),
        ("antigravity", False, frozenset()),
    ],
)
def test_authored_skill_cleanup_prunes_renamed_nested_file_from_every_catalog_owned_root(
    tmp_path, state, antigravity_enabled, expected_roots
):
    """A renamed authored skill file converges every catalog-owned package root."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    destination.mkdir()
    _initialize_authored_cleanup_source(source, include_external=True)

    skill_source = source / "src/ai/skills" / "fixture"
    (skill_source / "references").mkdir(parents=True)
    (skill_source / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")
    stale_source = skill_source / "references" / "old-name.md"
    stale_source.write_text("old\n", encoding="utf-8")

    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.skills.authored]",
                f'fixture = "{state}"',
                "",
                "[data.local.bin.agy]",
                f'installation_method = "{"system" if antigravity_enabled else "none"}"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    for root_name, root in CAPABILITY_AUTHORED_SKILL_ROOTS.items():
        if root_name not in expected_roots:
            skill_target = destination / root / "fixture"
            (skill_target / "references").mkdir(parents=True)
            (skill_target / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")
            (skill_target / "references" / "old-name.md").write_text("old\n", encoding="utf-8")
        unrelated = destination / root / "external-skill"
        unrelated.mkdir(parents=True)
        (unrelated / "SKILL.md").write_text("# External\n", encoding="utf-8")

    first_apply = _apply_authored_cleanup(source, destination, config)
    assert first_apply.returncode == 0, first_apply.stderr
    for root_name, root in CAPABILITY_AUTHORED_SKILL_ROOTS.items():
        assert (destination / root / "fixture").exists() is (root_name in expected_roots)
        assert (destination / root / "fixture/references/old-name.md").exists() is (root_name in expected_roots)

    stale_source.rename(skill_source / "references" / "new-name.md")

    second_apply = _apply_authored_cleanup(source, destination, config)
    assert second_apply.returncode == 0, second_apply.stderr
    for root_name, root in CAPABILITY_AUTHORED_SKILL_ROOTS.items():
        stale_target = destination / root / "fixture/references/old-name.md"
        assert not stale_target.exists()
        assert (destination / root / "fixture/references/new-name.md").exists() is (root_name in expected_roots)
        assert (destination / root / "fixture/SKILL.md").exists() is (root_name in expected_roots)
        assert (destination / root / "external-skill/SKILL.md").is_file()


def test_authored_skill_cleanup_removes_disabled_canonical_skill_from_every_capability_package_root(tmp_path):
    """Disabling an authored skill removes its package copies, including Cursor's local plugin."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    destination.mkdir()
    _initialize_authored_cleanup_source(source, include_external=True)

    skill_source = source / "src/ai/skills/fixture"
    skill_source.mkdir(parents=True)
    (skill_source / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")

    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.skills.authored]",
                'fixture = "present"',
                "",
                "[data.ai.skills.external]",
                "",
                "[data.ai.agents.external]",
                "",
                "[data.local.bin.agy]",
                'installation_method = "system"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    first_apply = _apply_authored_cleanup(source, destination, config)
    assert first_apply.returncode == 0, first_apply.stderr
    for root in CAPABILITY_AUTHORED_SKILL_ROOTS.values():
        assert (destination / root / "fixture/SKILL.md").is_file()
    cursor_manifest = destination / ".cursor/plugins/local/mkobit-dotfiles/.cursor-plugin/plugin.json"
    manifest = json.loads(cursor_manifest.read_text(encoding="utf-8"))
    assert manifest["name"] == "mkobit-dotfiles"
    assert manifest["version"].startswith("1.0.0+")
    assert manifest["description"] == "Base dotfiles capability bundle."
    assert manifest["skills"] == "./skills"

    config.write_text(
        "\n".join(
            [
                "[data.ai.skills.authored]",
                'fixture = "absent"',
                "",
                "[data.ai.skills.external]",
                "",
                "[data.ai.agents.external]",
                "",
                "[data.local.bin.agy]",
                'installation_method = "system"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    second_apply = _apply_authored_cleanup(source, destination, config)
    assert second_apply.returncode == 0, second_apply.stderr
    for root in CAPABILITY_AUTHORED_SKILL_ROOTS.values():
        assert not (destination / root / "fixture").exists()


def test_authored_skill_cleanup_rejects_shell_metacharacters_without_executing_them(tmp_path):
    """An invalid catalog key cannot become shell syntax in the rendered cleanup hook."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    destination.mkdir()
    _initialize_authored_cleanup_source(source)

    malicious_name = "$(touch${IFS}injected)"
    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.skills.authored]",
                f'{json.dumps(malicious_name)} = "claude"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = _apply_authored_cleanup(source, destination, config)

    assert result.returncode != 0
    assert "invalid authored skill name" in result.stderr
    assert not (tmp_path / "injected").exists()


@pytest.mark.parametrize("symlink_level", ["managed-root", "skill-root"])
def test_authored_skill_cleanup_rejects_symlink_escape_without_deleting_outside(tmp_path, symlink_level):
    """Cleanup refuses a symlinked managed root or skill root before traversal."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    _initialize_authored_cleanup_source(source)

    skill_source = source / "src/ai/skills" / "fixture"
    skill_source.mkdir(parents=True)
    (skill_source / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")
    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.skills.authored]",
                'fixture = "claude"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    managed_root = destination / AUTHORED_SKILL_ROOTS["claude"]
    outside_skill = tmp_path / "outside" / "fixture"
    (outside_skill / "references").mkdir(parents=True)
    sentinel = outside_skill / "references" / "old-name.md"
    sentinel.write_text("keep\n", encoding="utf-8")
    if symlink_level == "managed-root":
        managed_root.parent.mkdir(parents=True)
        managed_root.symlink_to(outside_skill.parent, target_is_directory=True)
    else:
        managed_root.mkdir(parents=True)
        (managed_root / "fixture").symlink_to(outside_skill, target_is_directory=True)

    result = _apply_authored_cleanup(source, destination, config)

    assert result.returncode != 0
    assert "symlink" in result.stderr
    assert sentinel.read_text(encoding="utf-8") == "keep\n"


def test_authored_skill_cleanup_handles_newline_descendant_without_escaping_root(tmp_path):
    """A newline-bearing descendant cannot become an outside deletion target."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    _initialize_authored_cleanup_source(source)

    skill_source = source / "src/ai/skills" / "fixture"
    skill_source.mkdir(parents=True)
    (skill_source / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")
    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.skills.authored]",
                'fixture = "claude"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    skill_target = destination / AUTHORED_SKILL_ROOTS["claude"] / "fixture"
    skill_target.mkdir(parents=True)
    (skill_target / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")
    sentinel = tmp_path / "outside" / "sentinel"
    sentinel.parent.mkdir()
    sentinel.write_text("keep\n", encoding="utf-8")
    mirrored_sentinel = skill_target / "payload\n" / Path(*sentinel.parts[1:])
    mirrored_sentinel.parent.mkdir(parents=True)
    mirrored_sentinel.write_text("stale\n", encoding="utf-8")

    result = _apply_authored_cleanup(source, destination, config)

    assert result.returncode == 0, result.stderr
    assert sentinel.read_text(encoding="utf-8") == "keep\n"
    assert not mirrored_sentinel.exists()


def test_authored_skill_cleanup_propagates_descendant_symlink_refusal(tmp_path):
    """A descendant symlink aborts traversal without touching its outside target."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    _initialize_authored_cleanup_source(source)

    skill_source = source / "src/ai/skills" / "fixture"
    skill_source.mkdir(parents=True)
    (skill_source / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")
    skill_target = destination / AUTHORED_SKILL_ROOTS["claude"] / "fixture"
    skill_target.mkdir(parents=True)
    (skill_target / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")
    sentinel = tmp_path / "outside" / "sentinel"
    sentinel.parent.mkdir()
    sentinel.write_text("keep\n", encoding="utf-8")
    escape = skill_target / "escape"
    escape.symlink_to(sentinel.parent, target_is_directory=True)
    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.skills.authored]",
                'fixture = "claude"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    result = _apply_authored_cleanup(source, destination, config)

    assert result.returncode != 0
    assert "symlink descendant" in result.stderr
    assert escape.is_symlink()
    assert sentinel.read_text(encoding="utf-8") == "keep\n"


@pytest.mark.integration
@pytest.mark.parametrize(("relative_dir", "allowed_marker_files"), DIRECT_SKILL_DIRS)
def test_direct_skill_dir_deployed_and_valid(chezmoi_data, chezmoi_dest, relative_dir, allowed_marker_files):
    """Verify each direct skill consumer receives a non-empty valid skill tree."""
    if installation_method(chezmoi_data, "local.bin.agy") in {"none", "uninstall"}:
        pytest.skip("Antigravity CLI is disabled")

    skills_dir = chezmoi_dest / relative_dir
    assert skills_dir.is_dir(), f"{skills_dir} does not exist after chezmoi apply"
    assert any(skills_dir.iterdir()), f"{skills_dir} contains no skills"
    assert_entries_are_valid_skills(skills_dir, allowed_marker_files)


@pytest.mark.integration
@pytest.mark.parametrize(("relative_dir", "plugin_host"), CAPABILITY_PLUGIN_DIRS)
def test_capability_plugin_deployed_and_valid(chezmoi_dest, relative_dir, plugin_host):
    """Verify every host plugin replaces its matching direct skill roots."""
    plugin_dir = chezmoi_dest / relative_dir
    manifest_path = plugin_dir / f".{plugin_host}-plugin" / "plugin.json"
    skills_dir = plugin_dir / "skills"

    assert manifest_path.is_file(), f"{manifest_path} does not exist after chezmoi apply"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["name"] == "mkobit-dotfiles"
    assert manifest["skills"] == "./skills"
    _assert_valid_capability_metadata(manifest)
    assert skills_dir.is_dir(), f"{skills_dir} does not exist after chezmoi apply"
    assert any(skills_dir.iterdir()), f"{skills_dir} contains no skills"
    assert_entries_are_valid_skills(skills_dir)
    direct_skills_dir = chezmoi_dest / f".{plugin_host}" / "skills"
    for plugin_skill in _entries(skills_dir):
        direct_skill = direct_skills_dir / plugin_skill.name
        assert not direct_skill.exists(), f"{direct_skill} remains after capability-plugin cutover"


@pytest.mark.integration
def test_portable_skills_root_deployed_and_valid(chezmoi_dest):
    """Verify portable skills root is deployed and contains valid skills."""
    portable_dir = chezmoi_dest / ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills"
    assert portable_dir.exists(), f"{portable_dir} does not exist after chezmoi apply"
    assert portable_dir.is_dir(), f"{portable_dir} is not a directory"
    assert any(portable_dir.iterdir()), f"{portable_dir} contains no skills"
    assert_entries_are_valid_skills(portable_dir)


@pytest.mark.integration
def test_root_capability_plugin_manifest_deployed_and_valid(chezmoi_dest):
    """Verify root capability plugin manifest is deployed and valid."""
    manifest_path = chezmoi_dest / ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/plugin.json"
    assert manifest_path.is_file(), f"{manifest_path} does not exist after chezmoi apply"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["name"] == "mkobit-dotfiles"
    assert manifest["skills"] == ["./skills"]
    assert manifest["version"].startswith("1.0.0+")
    _assert_valid_capability_metadata(manifest)


@pytest.mark.integration
def test_marketplace_manifests_deployed_and_valid(chezmoi_dest):
    """Verify marketplace manifests and bridge provenance are deployed and valid."""
    agents_marketplace = chezmoi_dest / ".local/share/agent-plugins/marketplace/.agents/plugins/marketplace.json"
    assert agents_marketplace.is_file(), f"{agents_marketplace} does not exist after chezmoi apply"
    agents_data = json.loads(agents_marketplace.read_text(encoding="utf-8"))
    assert agents_data["name"] == "dotfiles"
    agents_plugins = {plugin["name"]: plugin for plugin in agents_data["plugins"]}
    assert agents_plugins["mkobit-dotfiles"]["source"]["path"] == "./plugins/mkobit-dotfiles/codex"

    claude_marketplace = chezmoi_dest / ".local/share/agent-plugins/marketplace/.claude-plugin/marketplace.json"
    assert claude_marketplace.is_file(), f"{claude_marketplace} does not exist after chezmoi apply"
    claude_data = json.loads(claude_marketplace.read_text(encoding="utf-8"))
    assert claude_data["name"] == "dotfiles"
    claude_plugins = {plugin["name"]: plugin for plugin in claude_data["plugins"]}
    claude_source = claude_plugins["mkobit-dotfiles"]["source"]
    claude_path = claude_source["path"] if isinstance(claude_source, dict) else claude_source
    assert claude_path == "./plugins/mkobit-dotfiles/claude"

    superpowers_root = chezmoi_dest / ".local/share/agent-plugins/marketplaces/superpowers-marketplace"
    superpowers_agents = json.loads((superpowers_root / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    assert superpowers_agents["name"] == "superpowers-marketplace"
    superpowers_agents_plugins = {plugin["name"]: plugin for plugin in superpowers_agents["plugins"]}
    assert "superpowers" in superpowers_agents_plugins
    assert superpowers_agents_plugins["superpowers"]["source"]["path"] == "./plugins/superpowers"

    superpowers_claude = json.loads((superpowers_root / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    assert superpowers_claude["name"] == "superpowers-marketplace"
    superpowers_claude_plugins = {plugin["name"]: plugin for plugin in superpowers_claude["plugins"]}
    assert "superpowers" in superpowers_claude_plugins
    assert superpowers_claude_plugins["superpowers"]["source"] == "./plugins/superpowers"

    provenance_path = chezmoi_dest / ".local/share/agent-plugins/marketplace/bridge-provenance.json"
    assert provenance_path.is_file(), f"{provenance_path} does not exist after chezmoi apply"
    json.loads(provenance_path.read_text(encoding="utf-8"))


GLOBAL_MODERN_WEB_PATHS = (
    ".local/share/agent-plugins/marketplaces/googlechrome",
    ".cursor/plugins/local/modern-web-guidance",
    ".claude/plugins/cache/googlechrome",
    ".codex/plugins/cache/googlechrome",
    ".codex/skills/.source-modern-web-guidance",
    *(
        f"{agent}/plugins/cache/dotfiles/mkobit-dotfiles/{version}/skills/{skill}"
        for agent in (".claude", ".codex")
        for version in ("old", "older")
        for skill in ("modern-web-guidance", "chrome-extensions")
    ),
    *(
        f"{agent}/skills/{skill}"
        for agent in (".claude", ".codex", ".cursor", ".gemini/antigravity-cli")
        for skill in ("modern-web-guidance", "chrome-extensions")
    ),
)


@pytest.mark.integration
def test_googlechrome_marketplace_removed(chezmoi_dest):
    """Global guidance copies are absent after apply."""
    for relative in GLOBAL_MODERN_WEB_PATHS:
        assert not (chezmoi_dest / relative).exists(), relative
    for agent in (".claude", ".codex"):
        cache = chezmoi_dest / agent / "plugins/cache/dotfiles/mkobit-dotfiles"
        for skill in ("modern-web-guidance", "chrome-extensions"):
            assert not list(cache.glob(f"*/skills/{skill}")), (agent, skill)


@pytest.mark.parametrize("ownership_format", ["current", "legacy", "malformed"])
def test_global_modern_web_guidance_removal_migrates_existing_copies(tmp_path, ownership_format):
    """Retirement removes existing global copies and preserves local and unrelated content."""
    source = tmp_path / "source"
    source.mkdir()
    shutil.copy2(REPOSITORY_ROOT / "src/chezmoi/.chezmoiremove", source / ".chezmoiremove")
    cleanup = REPOSITORY_ROOT / "src/chezmoi/.chezmoiscripts/run_after_zz-retired-modern-web-guidance.sh.tmpl"
    for original, target in (
        (cleanup, source / ".chezmoiscripts" / cleanup.name),
        (FILTER_INTERPRETER_TEMPLATE, source / ".chezmoitemplates/python/filter-interpreter"),
        (FILTER_INTERPRETER_RESOLVER, source.parent / "python/skill_filter/resolve-interpreter.sh"),
    ):
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
    for name in ("plugin_bridge.py", "plugin_declarations.py"):
        target = source.parent / "python/skill_filter/skill_filter" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPOSITORY_ROOT / "src/python/skill_filter/skill_filter" / name, target)
    destination = tmp_path / "destination"
    destination.mkdir()
    config = tmp_path / "chezmoi.toml"
    config.write_text('[data.zsh]\nprompt = "none"\n')
    preserved = (
        "projects/web/.agents/skills/modern-web-guidance",
        "projects/web/.agents/skills/chrome-extensions",
        ".local/share/agent-plugins/marketplaces/superpowers-marketplace",
        ".cursor/plugins/local/unrelated",
        ".claude/plugins/cache/unrelated",
        ".codex/plugins/cache/unrelated",
        ".claude/plugins/cache/dotfiles/mkobit-dotfiles/old/skills/unrelated",
        ".codex/plugins/cache/dotfiles/mkobit-dotfiles/old/skills/unrelated",
        ".claude/skills/unrelated",
        ".codex/skills/unrelated",
        ".cursor/skills/unrelated",
        ".gemini/antigravity-cli/skills/unrelated",
    )
    for relative in (*GLOBAL_MODERN_WEB_PATHS, *preserved):
        directory = destination / relative
        directory.mkdir(parents=True)
        (directory / "sentinel").write_text(relative)
    state = destination / ".local/state/dotfiles"
    state.mkdir(parents=True)
    ownership = state / "agent-plugin-ownership"
    if ownership_format == "legacy":
        ownership = state / "agent-plugin-ownership.json"
        ownership.write_text(
            json.dumps(
                {
                    "resources": [
                        {"kind": "marketplace", "host": "codex", "id": "googlechrome"},
                        {"kind": "plugin", "host": "claude", "id": "modern-web-guidance@googlechrome"},
                    ]
                }
            )
        )
    else:
        ownership.write_text(
            "invalid state"
            if ownership_format == "malformed"
            else "marketplace\tcodex\tgooglechrome\t\nplugin\tclaude\tgooglechrome\tmodern-web-guidance\n"
        )
    late_paths = (
        ".local/share/agent-plugins/marketplaces/googlechrome",
        ".claude/plugins/cache/googlechrome",
        ".codex/plugins/cache/googlechrome",
    )
    result = _apply_authored_cleanup(source, destination, config)
    assert result.returncode == 0, result.stderr
    assert "Deferred googlechrome cleanup" in result.stderr
    for relative in GLOBAL_MODERN_WEB_PATHS:
        assert (destination / relative).exists() == (relative in late_paths), relative
    for relative in preserved:
        assert (destination / relative / "sentinel").read_text() == relative

    # Reproduce native reconciliation ordering: the source must survive until
    # the earlier bridge has inspected it and released native ownership.
    bridge = source / ".chezmoiscripts/run_after_agent-plugin-bridge.sh.tmpl"
    bridge.write_text(
        "#!/usr/bin/env sh\nset -eu\n"
        'test -f "{{ .chezmoi.destDir }}/.local/share/agent-plugins/marketplaces/googlechrome/sentinel"\n'
        'rm "{{ .chezmoi.destDir }}/.local/state/dotfiles/' + ownership.name + '"\n'
    )
    result = _apply_authored_cleanup(source, destination, config)
    assert result.returncode == 0, result.stderr
    bridge.unlink()
    for _ in range(2):
        result = _apply_authored_cleanup(source, destination, config)
        assert result.returncode == 0, result.stderr
        for relative in GLOBAL_MODERN_WEB_PATHS:
            assert not (destination / relative).exists(), relative
        for relative in preserved:
            assert (destination / relative / "sentinel").read_text() == relative


@pytest.mark.integration
def test_plugin_bridge_ownership_state(chezmoi_dest):
    """Verify agent-plugin ownership state file contains valid tab-separated records."""
    state_file = chezmoi_dest / ".local/state/dotfiles/agent-plugin-ownership"
    if not state_file.is_file():
        return
    for line in state_file.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        fields = line.split("\t")
        assert len(fields) == 4, f"expected 4 tab-separated fields in {line!r}, got {len(fields)}"


# Tool agent directories actively deployed to by .chezmoiexternals/ai-agents.toml.tmpl.
ACTIVE_AGENT_DIRS = [
    pytest.param(Path(".claude/agents"), id="claude"),
    pytest.param(Path(".config/opencode/agents"), id="opencode"),
]


@pytest.mark.integration
@pytest.mark.parametrize("relative_dir", ACTIVE_AGENT_DIRS)
def test_agents_dir_deployed_and_valid(chezmoi_dest, relative_dir):
    """Verify each deployed agent source directory contains only non-empty .md agent files."""
    agents_dir = chezmoi_dest / relative_dir
    assert agents_dir.is_dir(), f"{agents_dir} does not exist after chezmoi apply"
    source_dirs = [entry for entry in sorted(agents_dir.iterdir()) if entry.name != ".DS_Store"]
    assert source_dirs, f"{agents_dir} contains no agent sources"
    for source_dir in source_dirs:
        assert source_dir.is_dir(), f"{source_dir} is not a directory; agent sources must be directories"
        agent_files = [entry for entry in sorted(source_dir.iterdir()) if entry.name != ".DS_Store"]
        assert agent_files, f"{source_dir} contains no agents"
        for agent_file in agent_files:
            assert agent_file.suffix == ".md", f"{agent_file} is not an .md agent file"
            assert agent_file.stat().st_size > 0, f"{agent_file} is empty"


@pytest.mark.integration
def test_codex_agent_roles_deployed_and_loadable(chezmoi_dest):
    """Codex agents are TOML roles, not markdown, and every required key must be present.

    Codex silently skips a role file it cannot parse — it only says so as a startup
    warning — so a malformed one would otherwise look like a working deployment
    with a missing agent. See test_codex_reports_no_agent_role_warnings.
    """
    agents_dir = chezmoi_dest / ".codex/agents"
    assert agents_dir.is_dir(), f"{agents_dir} does not exist after chezmoi apply"

    role_files = sorted(agents_dir.rglob("*.toml"))
    assert role_files, f"{agents_dir} contains no .toml agent roles"

    for role_file in role_files:
        assert role_file.stat().st_size > 0, f"{role_file} is empty"
        parsed = tomllib.loads(role_file.read_text())
        for key in ("name", "description", "developer_instructions"):
            assert parsed.get(key), f"{role_file} is missing required key {key!r}"

    stray = [entry for entry in agents_dir.rglob("*") if entry.is_file() and entry.suffix != ".toml"]
    assert not stray, f"non-TOML files under {agents_dir}: {stray}"


@pytest.mark.integration
def test_codex_reports_no_agent_role_warnings(host):
    """Ask Codex itself whether it loaded the roles, rather than trusting the file layout.

    `codex doctor` emits "Ignoring malformed agent role definition" per bad file and
    counts it under startup warnings. Verified to fire for a role missing
    developer_instructions, including one nested in a subdirectory, so silence here
    is meaningful rather than vacuous.
    """
    if not shutil.which("codex"):
        pytest.skip("codex is not installed")

    result = host.run("codex doctor")
    offenders = [
        line.strip() for line in f"{result.stdout}\n{result.stderr}".splitlines() if "malformed agent role" in line
    ]
    assert not offenders, "codex rejected deployed agent roles:\n" + "\n".join(offenders)


@pytest.mark.parametrize("kind", ["base", "capability"])
@pytest.mark.parametrize("override", [False, True])
def test_authored_templates_render_effective_data_without_child_hooks(tmp_path, kind, override):
    """Template entries render parent data once and preserve plain binary resources."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    destination.mkdir()
    external = (
        AUTHORED_SKILLS_EXTERNAL
        if kind == "base"
        else REPOSITORY_ROOT / "src/chezmoi/.chezmoiexternals/ai-authored-capabilities.toml.tmpl"
    )
    externals = source / ".chezmoiexternals"
    externals.mkdir(parents=True)
    shutil.copy2(external, externals / external.name)
    template_root = source / ".chezmoitemplates/ai"
    template_root.mkdir(parents=True)
    for name in ("authored-render-context", "authored-file-entry", "authored-file-digest", "authored-base-version"):
        origin = REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/ai" / name
        shutil.copy2(origin, template_root / name)
    cleanup_name = "skills" if kind == "base" else "capabilities"
    dependencies = {
        REPOSITORY_ROOT
        / f"src/chezmoi/.chezmoiscripts/run_onchange_after_00-agent-plugin-authored-{cleanup_name}-cleanup.sh.tmpl": source
        / f".chezmoiscripts/run_onchange_after_00-agent-plugin-authored-{cleanup_name}-cleanup.sh.tmpl",
        FILTER_INTERPRETER_TEMPLATE: source / ".chezmoitemplates/python/filter-interpreter",
        FILTER_INTERPRETER_RESOLVER: source.parent / "python/skill_filter/resolve-interpreter.sh",
    }
    for origin, target in dependencies.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, target)
    data = source / ".chezmoidata/defaults.toml"
    data.parent.mkdir()
    data.write_text('[fixture]\nvalue = "catalog"\n')
    skill = source.parent / ("ai/skills/fixture" if kind == "base" else "overlay-plugins/example/skills/fixture")
    (skill / "nested").mkdir(parents=True)
    canonical = skill / "SKILL.md.tmpl"
    contents = "{{ .fixture.value }}|{{ .chezmoi.destDir }}|{{ .chezmoi.sourceFile }}|{{ .chezmoi.targetFile }}\n"
    canonical.write_text(contents)
    (skill / "nested/payload.bin").write_bytes(b"\x00\xff{{ untouched }}")
    executable = skill / "nested/run.tmpl"
    executable.write_text("#!/bin/sh\necho {{ .fixture.value }}\n")
    executable.chmod(0o755)
    (skill / "nested/name.tmpl.tmpl").write_text("{{ .chezmoi.targetFile }}")
    (skill / "nested/empty.tmpl").write_text('{{- "" -}}')
    counter = tmp_path / "hook-count"
    config = tmp_path / "chezmoi.toml"
    selection = (
        '[data.ai.skills.authored]\nfixture = "present"\n[data.local.bin.agy]\ninstallation_method = "preinstalled"\n'
        if kind == "base"
        else '[data.ai.plugin_bridge.capabilities.example]\nsource_dir = "src/overlay-plugins/example"\nhosts = ["claude", "codex", "cursor"]\n[data.ai.plugin_bridge.capabilities.example.skills]\nfixture = "present"\n'
    )
    config.write_text(
        '[hooks.read-source-state.pre]\ncommand = "sh"\nargs = ["-c", "echo once >> '
        + str(counter)
        + '"]\n'
        + selection
        + ('[data.fixture]\nvalue = "override"\n' if override else "")
    )
    subprocess.run(["git", "init", "--quiet", str(source)], check=True)
    result = subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--config",
            str(config),
            "--refresh-externals=always",
            "apply",
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    value = "override" if override else "catalog"
    roots = (
        list(AUTHORED_SKILL_ROOTS.values())
        if kind == "base"
        else [
            Path(f".local/share/agent-plugins/marketplace/plugins/example/{host}/skills")
            for host in ("claude", "codex", "cursor")
        ]
        + [Path(".cursor/plugins/local/example/skills")]
    )
    for relative in roots:
        target = destination / relative / "fixture"
        assert (target / "SKILL.md").read_text() == f"{value}|{destination}|{canonical}|SKILL.md\n"
        assert not (target / "SKILL.md.tmpl").exists()
        assert (target / "nested/payload.bin").read_bytes() == b"\x00\xff{{ untouched }}"
        assert (target / "nested/run").read_text() == f"#!/bin/sh\necho {value}\n"
        assert (target / "nested/run").stat().st_mode & 0o111
        assert (target / "nested/empty").read_bytes() == b""
        assert (target / "nested/name.tmpl").read_text() == "nested/name.tmpl"
    assert canonical.read_text() == contents
    assert counter.read_text() == "once\n"
    # Remove a template and reapply to check that cleanup owns rendered names.
    (skill / "nested/run.tmpl").unlink()
    counter.unlink()
    repeated = subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--config",
            str(config),
            "--refresh-externals=always",
            "apply",
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert repeated.returncode == 0, repeated.stderr
    for relative in roots:
        target = destination / relative / "fixture"
        assert (target / "SKILL.md").exists()
        assert not (target / "nested/run").exists()
        assert (target / "nested/payload.bin").read_bytes() == b"\x00\xff{{ untouched }}"
    assert counter.read_text() == "once\n"
    assert not (destination / ".local/state/chezmoi-authored-template-render.boltdb").exists()


@pytest.mark.parametrize("kind", ["base", "capability"])
@pytest.mark.parametrize("failure", ["collision", "template"])
def test_authored_templates_reject_invalid_rendering(tmp_path, kind, failure):
    """Bad templates and normalized filename collisions stop apply."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    destination.mkdir()
    externals = source / ".chezmoiexternals"
    externals.mkdir(parents=True)
    external = (
        AUTHORED_SKILLS_EXTERNAL
        if kind == "base"
        else REPOSITORY_ROOT / "src/chezmoi/.chezmoiexternals/ai-authored-capabilities.toml.tmpl"
    )
    shutil.copy2(external, externals / external.name)
    templates = REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/ai"
    shutil.copytree(templates, source / ".chezmoitemplates/ai")
    skill = source.parent / ("ai/skills/fixture" if kind == "base" else "overlay-plugins/example/skills/fixture")
    skill.mkdir(parents=True)
    (skill / "SKILL.md.tmpl").write_text('{{ fail "fixture render failed" }}' if failure == "template" else "rendered")
    if failure == "collision":
        (skill / "SKILL.md").write_text("plain")
    config = tmp_path / "chezmoi.toml"
    config.write_text(
        '[data.ai.skills.authored]\nfixture = "present"\n'
        if kind == "base"
        else '[data.ai.plugin_bridge.capabilities.example]\nsource_dir = "src/overlay-plugins/example"\nhosts = ["claude"]\n[data.ai.plugin_bridge.capabilities.example.skills]\nfixture = "present"\n'
    )
    result = subprocess.run(
        ["chezmoi", "--source", str(source), "--destination", str(destination), "--config", str(config), "apply"],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert ("collision" if failure == "collision" else "fixture render failed") in result.stderr


def _rendered_package_fixture(tmp_path: Path, kind: str) -> tuple[Path, Path, Path, Path, list[Path], list[Path]]:
    """Install real external, manifest, and cleanup templates in an isolated source."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    destination.mkdir(parents=True)
    templates = REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/ai"
    shutil.copytree(templates, source / ".chezmoitemplates/ai")
    external = (
        AUTHORED_SKILLS_EXTERNAL
        if kind == "base"
        else REPOSITORY_ROOT / "src/chezmoi/.chezmoiexternals/ai-authored-capabilities.toml.tmpl"
    )
    cleanup = (
        AUTHORED_CLEANUP_SCRIPT
        if kind == "base"
        else REPOSITORY_ROOT
        / "src/chezmoi/.chezmoiscripts/run_onchange_after_00-agent-plugin-authored-capabilities-cleanup.sh.tmpl"
    )
    for origin, target in {
        external: source / ".chezmoiexternals" / external.name,
        cleanup: source / ".chezmoiscripts" / cleanup.name,
        FILTER_INTERPRETER_TEMPLATE: source / ".chezmoitemplates/python/filter-interpreter",
        FILTER_INTERPRETER_RESOLVER: source.parent / "python/skill_filter/resolve-interpreter.sh",
    }.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, target)
    if kind == "base":
        for relative in (
            *CAPABILITY_MANIFEST_TEMPLATES,
            CURSOR_LOCAL_PLUGIN_MANIFEST.relative_to(REPOSITORY_ROOT / "src/chezmoi"),
        ):
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPOSITORY_ROOT / "src/chezmoi" / relative, target)
        roots = [destination / root / "fixture" for root in CAPABILITY_AUTHORED_SKILL_ROOTS.values()]
        manifests = [destination / ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/plugin.json"]
        manifests.extend(
            root.parent.parent / f".{host}-plugin/plugin.json"
            for host, root in zip(("claude", "codex", "cursor", "cursor"), roots[1:], strict=True)
        )
        skill = source.parent / "ai/skills/fixture"
        selection = '[data.ai.skills.authored]\nfixture = "present"\n[data.ai.skills.external]\n'
    else:
        roots = [
            destination / f".local/share/agent-plugins/marketplace/plugins/example/{host}/skills/fixture"
            for host in ("claude", "codex", "cursor")
        ]
        roots.append(destination / ".cursor/plugins/local/example/skills/fixture")
        manifests = []
        for host in ("claude", "codex", "cursor"):
            relative = Path(
                f"dot_local/share/agent-plugins/marketplace/plugins/example/{host}/dot_{host}-plugin/plugin.json.tmpl"
            )
            wrapper = source / relative
            wrapper.parent.mkdir(parents=True, exist_ok=True)
            wrapper.write_text('{{ includeTemplate "ai/authored-plugin-manifest" (dict "root" . "name" "example") }}')
            manifests.append(
                destination
                / f".local/share/agent-plugins/marketplace/plugins/example/{host}/.{host}-plugin/plugin.json"
            )
        wrapper = source / "dot_cursor/plugins/local/example/exact_dot_cursor-plugin/plugin.json.tmpl"
        wrapper.parent.mkdir(parents=True)
        wrapper.write_text('{{ includeTemplate "ai/authored-plugin-manifest" (dict "root" . "name" "example") }}')
        manifests.append(destination / ".cursor/plugins/local/example/.cursor-plugin/plugin.json")
        skill = source.parent / "overlay-plugins/example/skills/fixture"
        selection = '[data.ai.plugin_bridge.capabilities.example]\ndescription = "Fixture"\nsource_dir = "src/overlay-plugins/example"\nhosts = ["claude", "codex", "cursor"]\n[data.ai.plugin_bridge.capabilities.example.skills]\nfixture = "present"\n'
    skill.mkdir(parents=True)
    (skill / "SKILL.md.tmpl").write_text("{{ .fixture.value }}|{{ .chezmoi.targetFile }}\n")
    (skill / "name.tmpl.tmpl").write_text("{{ .fixture.value }}|{{ .chezmoi.targetFile }}\n")
    (skill / "payload.bin").write_bytes(b"\x00\xff{{ plain }}")
    config = tmp_path / "chezmoi.toml"
    config.write_text(selection + '[data.fixture]\nvalue = "first"\n')
    subprocess.run(["git", "init", "--quiet", str(source)], check=True)
    return source, destination, config, skill, roots, manifests


def _package_versions(manifests: list[Path]) -> list[str]:
    return [json.loads(path.read_text())["version"] for path in manifests]


def _technical_writing_fixture(tmp_path: Path):
    """Use the authored technical-writing source with real package output and versions."""
    source, destination, config, skill, roots, manifests = _rendered_package_fixture(tmp_path, "base")
    shutil.rmtree(skill)
    skill = skill.with_name("technical-writing")
    shutil.copytree(REPOSITORY_ROOT / "src/ai/skills/technical-writing", skill)
    config.write_text(
        '[data.ai.skills.authored]\ntechnical-writing = "present"\n[data.ai.skills.external]\n'
        '[data.local.bin.agy]\ninstallation_method = "preinstalled"\n'
    )
    roots = [root.with_name("technical-writing") for root in roots]
    roots.append(destination / AUTHORED_SKILL_ROOTS["antigravity"] / "technical-writing")
    return source, destination, config, skill, roots, manifests


@pytest.mark.parametrize(
    "optional_data",
    [
        "",
        "[data.ai.skills.content]\n",
        '[data.ai.skills.content.technical-writing]\ndescription = ""\ninstructions = ""\n',
    ],
    ids=["missing", "empty-parent", "empty-values"],
)
def test_technical_writing_default_package_preserves_original_bytes(tmp_path, optional_data):
    """Missing optional content keeps the original skill bytes in every output."""
    source, destination, config, skill, roots, manifests = _technical_writing_fixture(tmp_path)
    config.write_text(config.read_text() + optional_data)
    original_sources = {path.name: path.read_bytes() for path in skill.iterdir()}
    result = _apply_authored_cleanup(source, destination, config)
    assert result.returncode == 0, result.stderr
    for root in roots:
        deployed = (root / "SKILL.md").read_bytes()
        assert (
            hashlib.sha256(deployed).hexdigest() == "32d9ef77a08a3e57f5fd501efa30ae7e84a3a689f906def8833dae1f4eb52b7b"
        )
        assert not (root / "SKILL.md.tmpl").exists()
    versions = _package_versions(manifests)
    repeated = _apply_authored_cleanup(source, destination, config)
    assert repeated.returncode == 0, repeated.stderr
    assert _package_versions(manifests) == versions
    assert {path.name: path.read_bytes() for path in skill.iterdir()} == original_sources


def test_technical_writing_template_accepts_missing_ai_root(tmp_path):
    """The optional content path is safe when the entire ai data root is absent."""
    skill_root = REPOSITORY_ROOT / "src/ai/skills/technical-writing"
    skill_file = next(path for path in skill_root.iterdir() if path.name.startswith("SKILL.md"))
    config = tmp_path / "chezmoi.toml"
    config.write_text("")
    source = tmp_path / "source"
    source.mkdir()
    result = subprocess.run(
        ["chezmoi", "--source", str(source), "--config", str(config), "execute-template"],
        capture_output=True,
        check=False,
        input=skill_file.read_text(),
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (
        hashlib.sha256(result.stdout.encode()).hexdigest()
        == "32d9ef77a08a3e57f5fd501efa30ae7e84a3a689f906def8833dae1f4eb52b7b"
    )


@pytest.mark.parametrize("content_layer", ["catalog", "control-plane", "instructions-only"])
def test_technical_writing_content_renders_merged_data_and_changes_package_versions(tmp_path, content_layer):
    """Content data changes YAML metadata and body bytes without changing the source."""
    source, destination, config, skill, roots, manifests = _technical_writing_fixture(tmp_path)
    original_sources = {path.name: path.read_bytes() for path in skill.iterdir()}
    first = _apply_authored_cleanup(source, destination, config)
    assert first.returncode == 0, first.stderr
    original = (roots[0] / "SKILL.md").read_text()
    original_frontmatter, original_body = original.split("---\n", 2)[1:]
    original_versions = _package_versions(manifests)
    description = "Use when: \"quoted\" # content\nKeep 'single quotes' and \\paths."
    instructions = "## Additional instructions\nKeep the configured instruction.\n"
    catalog = source / ".chezmoidata/technical-writing.toml"
    catalog.parent.mkdir()
    catalog.write_text(
        "[ai.skills.content.technical-writing]\n"
        + (f"description = {json.dumps(description)}\n" if content_layer == "catalog" else "")
        + f"instructions = {json.dumps(instructions)}\n"
    )
    if content_layer == "control-plane":
        catalog.write_text(catalog.read_text() + 'description = "Catalog description"\n')
        config.write_text(
            config.read_text()
            + f"[data.ai.skills.content.technical-writing]\ndescription = {json.dumps(description)}\n"
        )
    changed = _apply_authored_cleanup(source, destination, config)
    assert changed.returncode == 0, changed.stderr
    for root in roots:
        deployed = (root / "SKILL.md").read_text()
        frontmatter, body = deployed.split("---\n", 2)[1:]
        metadata = yaml.safe_load(frontmatter)
        assert set(metadata) == {"name", "description"}
        assert metadata["name"] == "technical-writing"
        if content_layer == "instructions-only":
            assert frontmatter == original_frontmatter
        else:
            assert metadata["description"] == description
        assert body == original_body + "\n" + instructions
        assert not (root / "SKILL.md.tmpl").exists()
    versions = _package_versions(manifests)
    assert all(before != after for before, after in zip(original_versions, versions, strict=True))
    repeated = _apply_authored_cleanup(source, destination, config)
    assert repeated.returncode == 0, repeated.stderr
    assert _package_versions(manifests) == versions
    assert {path.name: path.read_bytes() for path in skill.iterdir()} == original_sources


@pytest.mark.parametrize("kind", ["base", "capability"])
def test_rendered_package_versions_follow_data_and_stable_repeats(tmp_path, kind):
    """Data overrides change rendered bytes and every real manifest version."""
    source, destination, config, skill, roots, manifests = _rendered_package_fixture(tmp_path, kind)
    first = _apply_authored_cleanup(source, destination, config)
    assert first.returncode == 0, first.stderr
    original = _package_versions(manifests)
    assert len(set(original)) == 1
    repeated = _apply_authored_cleanup(source, destination, config)
    assert repeated.returncode == 0, repeated.stderr
    assert _package_versions(manifests) == original
    stale = roots[0] / "stale-owned.md"
    stale.write_text("old output\n")
    if kind == "capability":
        ownership = destination / ".local/state/dotfiles/agent-plugin-capability-ownership.json"
        state = json.loads(ownership.read_text())
        state["paths"].append(stale.relative_to(destination).as_posix())
        ownership.write_text(json.dumps(state))
    config.write_text(config.read_text().replace('value = "first"', 'value = "second"'))
    changed = _apply_authored_cleanup(source, destination, config)
    assert changed.returncode == 0, changed.stderr
    assert not stale.exists()
    for root in roots:
        assert (root / "SKILL.md").read_text() == "second|SKILL.md\n"
        assert (root / "name.tmpl").read_text() == "second|name.tmpl\n"
    assert all(before != after for before, after in zip(original, _package_versions(manifests), strict=True))
    assert (skill / "SKILL.md.tmpl").read_text() == "{{ .fixture.value }}|{{ .chezmoi.targetFile }}\n"


@pytest.mark.parametrize("kind", ["base", "capability"])
def test_rendered_package_versions_ignore_fixture_location(tmp_path, kind):
    """Identical rendered bytes and metadata give the same versions in two checkouts."""
    versions = []
    for name in ("first", "second"):
        source, destination, config, _, _, manifests = _rendered_package_fixture(tmp_path / name, kind)
        result = _apply_authored_cleanup(source, destination, config)
        assert result.returncode == 0, result.stderr
        versions.append(_package_versions(manifests))
    assert versions[0] == versions[1]


@pytest.mark.parametrize("kind", ["base", "capability"])
def test_rendered_package_versions_follow_binary_bytes_and_executable_mode(tmp_path, kind):
    """Binary bytes and executable mode are part of all manifest versions."""
    source, destination, config, skill, roots, manifests = _rendered_package_fixture(tmp_path, kind)
    first = _apply_authored_cleanup(source, destination, config)
    assert first.returncode == 0, first.stderr
    original = _package_versions(manifests)
    payload = skill / "payload.bin"
    payload.write_bytes(b"\x00\xfe{{ plain }}")
    changed = _apply_authored_cleanup(source, destination, config)
    assert changed.returncode == 0, changed.stderr
    binary_versions = _package_versions(manifests)
    assert all(before != after for before, after in zip(original, binary_versions, strict=True))
    payload.chmod(0o755)
    executable = _apply_authored_cleanup(source, destination, config)
    assert executable.returncode == 0, executable.stderr
    assert all(before != after for before, after in zip(binary_versions, _package_versions(manifests), strict=True))
    for root in roots:
        assert (root / "payload.bin").read_bytes() == b"\x00\xfe{{ plain }}"
        assert (root / "payload.bin").stat().st_mode & 0o111


@pytest.mark.parametrize("kind", ["base", "capability"])
def test_rendered_package_cleanup_removes_renamed_and_deleted_templates(tmp_path, kind):
    """Cleanup tracks rendered names, keeps sibling skills, and converges on repeat apply."""
    source, destination, config, skill, roots, _ = _rendered_package_fixture(tmp_path, kind)
    first = _apply_authored_cleanup(source, destination, config)
    assert first.returncode == 0, first.stderr
    sibling = roots[0].parent / "local-sibling/SKILL.md"
    sibling.parent.mkdir()
    sibling.write_text("keep\n")
    (skill / "name.tmpl.tmpl").rename(skill / "renamed.tmpl")
    renamed = _apply_authored_cleanup(source, destination, config)
    assert renamed.returncode == 0, renamed.stderr
    for root in roots:
        assert not (root / "name.tmpl").exists()
        assert (root / "renamed").read_text() == "first|renamed\n"
    (skill / "renamed.tmpl").unlink()
    for _ in range(2):
        deleted = _apply_authored_cleanup(source, destination, config)
        assert deleted.returncode == 0, deleted.stderr
        for root in roots:
            assert not (root / "renamed").exists()
            assert (root / "SKILL.md").is_file()
        assert sibling.read_text() == "keep\n"


def test_authored_manifest_normalization_rejects_template_plain_collision(tmp_path):
    """Manifest normalization rejects collisions even without file externals."""
    source, destination, config, skill, _, _ = _rendered_package_fixture(tmp_path, "capability")
    shutil.rmtree(source / ".chezmoiexternals")
    (skill / "SKILL.md").write_text("plain")
    result = _apply_authored_cleanup(source, destination, config)
    assert result.returncode != 0
    assert "collision" in result.stderr


@pytest.mark.parametrize(
    ("kind", "state"),
    [
        ("base", "absent"),
        ("base", "unlisted"),
        ("base", "antigravity"),
        ("capability", "absent"),
        ("capability", "unlisted"),
    ],
)
def test_rendered_package_does_not_evaluate_inactive_skill_templates(tmp_path, kind, state):
    """Inactive authored templates must not require data for an enabled package."""
    source, destination, config, skill, _, manifests = _rendered_package_fixture(tmp_path, kind)
    inactive = skill.parent / "inactive/SKILL.md.tmpl"
    inactive.parent.mkdir()
    inactive.write_text('{{ fail "inactive template rendered" }}')
    if state != "unlisted":
        config.write_text(
            config.read_text().replace('fixture = "present"', f'fixture = "present"\ninactive = "{state}"')
        )
    result = _apply_authored_cleanup(source, destination, config)
    assert result.returncode == 0, result.stderr
    assert all(path.is_file() for path in manifests)
    versions = _package_versions(manifests)
    inactive.write_text('{{ fail "inactive source changed" }}')
    changed = _apply_authored_cleanup(source, destination, config)
    assert changed.returncode == 0, changed.stderr
    assert all(before != after for before, after in zip(versions, _package_versions(manifests), strict=True))
    for path in destination.rglob("inactive"):
        assert not path.is_dir()


def test_rendered_package_does_not_evaluate_disabled_environment_templates(tmp_path):
    """A disabled capability cannot stop active package manifests or apply."""
    source, destination, config, _, roots, manifests = _rendered_package_fixture(tmp_path, "capability")
    config.write_text(
        config.read_text()
        + '\n[data.ai.plugin_bridge]\nenvironment = "mydev"\n'
        + '[data.ai.plugin_bridge.capabilities.disabled]\nsource_dir = "src/overlay-plugins/disabled"\n'
        + 'hosts = ["claude"]\nenvironments = ["mydata"]\n'
        + '[data.ai.plugin_bridge.capabilities.disabled.skills]\nexample = "present"\n'
    )
    inactive = source.parent / "overlay-plugins/disabled/skills/example/SKILL.md.tmpl"
    inactive.parent.mkdir(parents=True)
    inactive.write_text('{{ fail "disabled environment template evaluated" }}')

    result = _apply_authored_cleanup(source, destination, config)
    assert result.returncode == 0, result.stderr
    assert all(path.is_file() for path in manifests)
    assert all((root / "SKILL.md").is_file() for root in roots)
    versions = _package_versions(manifests)

    inactive.write_text('{{ fail "disabled environment source changed" }}')
    changed = _apply_authored_cleanup(source, destination, config)
    assert changed.returncode == 0, changed.stderr
    assert _package_versions(manifests) == versions
    assert not list(destination.rglob("disabled"))
