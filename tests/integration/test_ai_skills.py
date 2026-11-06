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


BUNDLE_MANIFESTS = (
    Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/plugin.json"),
    *(
        Path(f".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/{host}/.{host}-plugin/plugin.json")
        for host in ("claude", "codex", "cursor")
    ),
    Path(".cursor/plugins/local/mkobit-dotfiles/.cursor-plugin/plugin.json"),
)
ANTIGRAVITY_ON = '[data.local.bin.agy]\ninstallation_method = "preinstalled"\n'


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


def _has_files(directory: Path) -> bool:
    """Return whether a skill root holds files.

    A generated ignore pattern also hides a deselected root from .chezmoiremove,
    so the legacy cleanup empties that root but leaves the directory itself.
    """
    return any(path.is_file() for path in directory.rglob("*"))


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


def _initialize_authored_cleanup_source(source: Path) -> None:
    """Add the legacy cleanup script and its removal templates; agent_source_fixture deploys skills."""
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
        for name in ("agent-sources", "authored-render-context", "authored-file-digest", "authored-base-version")
    )
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


def test_capability_manifest_versions_ignore_legacy_overlay_source(agent_source_fixture, tmp_path):
    """Base capability versions only depend on base-projected skill inputs."""
    fixture = agent_source_fixture
    _write_skill(fixture, "base", {"SKILL.md": "# Base\n"})
    first_overlay = tmp_path / "first-overlay"
    second_overlay = tmp_path / "second-overlay"
    first_overlay.mkdir()
    second_overlay.mkdir()
    (first_overlay / "SKILL.md").write_text("# First\n", encoding="utf-8")
    (second_overlay / "SKILL.md").write_text("# Second\n", encoding="utf-8")

    def versions_for(overlay_source: Path) -> dict[str, str]:
        fixture.write_config(
            f"[data.ai.skills]\noverlay_authored_source = {json.dumps(str(overlay_source))}\n"
            "[data.ai.skills.external]\n"
        )
        return _render_capability_manifest_versions(fixture.repo, fixture.destination, fixture.config)

    assert versions_for(first_overlay) == versions_for(second_overlay)


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
    agent_source_fixture, state, antigravity_enabled, expected_roots
):
    """A renamed authored skill file converges every catalog-owned package root."""
    source = agent_source_fixture.repo
    destination = agent_source_fixture.destination
    _initialize_authored_cleanup_source(source)

    skill_source = source / "src/ai/skills" / "fixture"
    (skill_source / "references").mkdir(parents=True)
    (skill_source / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")
    stale_source = skill_source / "references" / "old-name.md"
    stale_source.write_text("old\n", encoding="utf-8")

    config = agent_source_fixture.config
    agent_source_fixture.write_config(
        "\n".join(
            [
                "[data.ai.skills.authored]",
                f'fixture = "{state}"',
                "",
                "[data.local.bin.agy]",
                f'installation_method = "{"system" if antigravity_enabled else "none"}"',
                "",
            ]
        )
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
        assert _has_files(destination / root / "fixture") is (root_name in expected_roots)
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


def test_authored_skill_cleanup_removes_disabled_canonical_skill_from_every_capability_package_root(
    agent_source_fixture,
):
    """Disabling an authored skill removes its package copies, including Cursor's local plugin."""
    source = agent_source_fixture.repo
    destination = agent_source_fixture.destination
    _initialize_authored_cleanup_source(source)

    skill_source = source / "src/ai/skills/fixture"
    skill_source.mkdir(parents=True)
    (skill_source / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")

    config = agent_source_fixture.config
    agent_source_fixture.write_config(
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
        )
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

    agent_source_fixture.write_config(
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
        )
    )

    second_apply = _apply_authored_cleanup(source, destination, config)
    assert second_apply.returncode == 0, second_apply.stderr
    for root in CAPABILITY_AUTHORED_SKILL_ROOTS.values():
        assert not _has_files(destination / root / "fixture")


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
            else "marketplace\tcodex\tgooglechrome\t\towned\nplugin\tclaude\tgooglechrome\tmodern-web-guidance\towned\n"
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
        assert len(fields) == 5, f"expected 5 tab-separated fields in {line!r}, got {len(fields)}"
        assert fields[4] in {"owned", "ambiguous"}, f"invalid provenance in {line!r}"


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


def _assert_bare_templates_render_effective_data(fixture, tmp_path: Path, override: bool) -> None:
    """Chezmoi renders generated bare skill templates natively, once, with effective data."""
    data = fixture.source / ".chezmoidata/defaults.toml"
    data.write_text('[fixture]\nvalue = "catalog"\n')
    contents = "{{ .fixture.value }}|{{ .chezmoi.destDir }}|{{ .chezmoi.sourceFile }}|{{ .chezmoi.targetFile }}\n"
    skill = _write_skill(
        fixture,
        "fixture",
        {
            "SKILL.md.tmpl": contents,
            "nested/payload.bin": b"\x00\xff{{ untouched }}",
            "nested/run.tmpl": "#!/bin/sh\necho {{ .fixture.value }}\n",
            "nested/name.tmpl.tmpl": "{{ .chezmoi.targetFile }}",
            "nested/empty.tmpl": '{{- "" -}}',
        },
    )
    (skill / "nested/run.tmpl").chmod(0o755)
    counter = tmp_path / "hook-count"
    fixture.write_config(ANTIGRAVITY_ON + ('[data.fixture]\nvalue = "override"\n' if override else ""), counter=counter)
    _apply_and_check(fixture)
    assert counter.read_text() == "once\n"
    value = "override" if override else "catalog"
    for root in AUTHORED_SKILL_ROOTS.values():
        target = fixture.destination / root / "fixture"
        source_path = fixture.run("source-path", str(target / "SKILL.md"))
        assert source_path.returncode == 0, source_path.stderr
        generated = Path(source_path.stdout.strip()).relative_to(fixture.source).as_posix()
        assert generated.endswith("/exact_fixture/SKILL.md.tmpl")
        expected = f"{value}|{fixture.destination}|{generated}|{target / 'SKILL.md'}\n"
        assert (target / "SKILL.md").read_text() == expected
        assert not (target / "SKILL.md.tmpl").exists()
        assert (target / "nested/payload.bin").read_bytes() == b"\x00\xff{{ untouched }}"
        assert (target / "nested/run").read_text() == f"#!/bin/sh\necho {value}\n"
        assert (target / "nested/run").stat().st_mode & 0o111
        # Native chezmoi skips a template that renders empty unless the source has empty_.
        assert not (target / "nested/empty").exists()
        assert (target / "nested/name.tmpl").read_text() == str(target / "nested/name.tmpl")
    assert (skill / "SKILL.md.tmpl").read_text() == contents
    # Remove a template and reapply: exact skill roots prune the rendered name.
    (skill / "nested/run.tmpl").unlink()
    counter.unlink()
    _apply_and_check(fixture)
    for root in AUTHORED_SKILL_ROOTS.values():
        target = fixture.destination / root / "fixture"
        assert (target / "SKILL.md").exists()
        assert not (target / "nested/run").exists()
        assert (target / "nested/payload.bin").read_bytes() == b"\x00\xff{{ untouched }}"
    assert counter.read_text() == "once\n"
    assert not (fixture.destination / ".local/state/chezmoi-authored-template-render.boltdb").exists()


@pytest.mark.parametrize("kind", ["base", "capability"])
@pytest.mark.parametrize("override", [False, True])
def test_authored_templates_render_effective_data_without_child_hooks(tmp_path, agent_source_factory, kind, override):
    """Template entries render parent data once and preserve plain binary resources."""
    if kind == "base":
        _assert_bare_templates_render_effective_data(agent_source_factory(tmp_path), tmp_path, override)
        return
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    destination.mkdir()
    external = REPOSITORY_ROOT / "src/chezmoi/.chezmoiexternals/ai-authored-capabilities.toml.tmpl"
    externals = source / ".chezmoiexternals"
    externals.mkdir(parents=True)
    shutil.copy2(external, externals / external.name)
    template_root = source / ".chezmoitemplates/ai"
    template_root.mkdir(parents=True)
    for name in (
        "agent-sources",
        "authored-render-context",
        "authored-file-entry",
        "authored-file-digest",
        "authored-base-version",
    ):
        origin = REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/ai" / name
        shutil.copy2(origin, template_root / name)
    cleanup_name = "capabilities"
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
    skill = source.parent / "overlay-plugins/example/skills/fixture"
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
    selection = '[data.ai.plugin_bridge.capabilities.example]\nsource_dir = "src/overlay-plugins/example"\nhosts = ["claude", "codex", "cursor"]\n[data.ai.plugin_bridge.capabilities.example.skills]\nfixture = "present"\n'
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
    roots = [
        Path(f".local/share/agent-plugins/marketplace/plugins/example/{host}/skills")
        for host in ("claude", "codex", "cursor")
    ] + [Path(".cursor/plugins/local/example/skills")]
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
def test_authored_templates_reject_invalid_rendering(tmp_path, agent_source_factory, kind, failure):
    """Bad templates and normalized filename collisions stop apply."""
    if kind == "base":
        fixture = agent_source_factory(tmp_path)
        skill = fixture.authored / "ai/skills/fixture"
    else:
        source = tmp_path / "source"
        destination = tmp_path / "destination"
        destination.mkdir()
        externals = source / ".chezmoiexternals"
        externals.mkdir(parents=True)
        external = REPOSITORY_ROOT / "src/chezmoi/.chezmoiexternals/ai-authored-capabilities.toml.tmpl"
        shutil.copy2(external, externals / external.name)
        templates = REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/ai"
        shutil.copytree(templates, source / ".chezmoitemplates/ai")
        skill = source.parent / "overlay-plugins/example/skills/fixture"
    skill.mkdir(parents=True)
    (skill / "SKILL.md.tmpl").write_text('{{ fail "fixture render failed" }}' if failure == "template" else "rendered")
    if failure == "collision":
        (skill / "SKILL.md").write_text("plain")
    if kind == "base":
        result = fixture.run("apply")
        # Preparation rejects a template and a plain file with the same target name.
        collision = "two sources map to SKILL.md"
    else:
        config = tmp_path / "chezmoi.toml"
        config.write_text(
            '[data.ai.plugin_bridge.capabilities.example]\nsource_dir = "src/overlay-plugins/example"\nhosts = ["claude"]\n[data.ai.plugin_bridge.capabilities.example.skills]\nfixture = "present"\n'
        )
        result = subprocess.run(
            ["chezmoi", "--source", str(source), "--destination", str(destination), "--config", str(config), "apply"],
            capture_output=True,
            check=False,
            text=True,
            timeout=30,
        )
        collision = "collision"
    assert result.returncode != 0
    assert (collision if failure == "collision" else "fixture render failed") in result.stderr


def _rendered_package_fixture(
    tmp_path: Path, kind: str, agent_sources
) -> tuple[Path, Path, Path, Path, list[Path], list[Path]]:
    """Install real templates in an isolated source.

    Base packages come from the preparation hook in an agent source fixture.
    Capability packages still use the authored capability externals and cleanup.
    """
    if kind == "base":
        fixture = agent_sources(tmp_path)
        source, destination, config = fixture.source, fixture.destination, fixture.config
        roots = [destination / root / "fixture" for root in CAPABILITY_AUTHORED_SKILL_ROOTS.values()]
        manifests = [destination / path for path in BUNDLE_MANIFESTS]
        skill = fixture.authored / "ai/skills/fixture"
        selection = '[data.ai.skills.authored]\nfixture = "present"\n[data.ai.skills.external]\n'
    else:
        source = tmp_path / "source"
        destination = tmp_path / "destination"
        destination.mkdir(parents=True)
        config = tmp_path / "chezmoi.toml"
        templates = REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/ai"
        shutil.copytree(templates, source / ".chezmoitemplates/ai")
        external = REPOSITORY_ROOT / "src/chezmoi/.chezmoiexternals/ai-authored-capabilities.toml.tmpl"
        cleanup = (
            REPOSITORY_ROOT
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
        subprocess.run(["git", "init", "--quiet", str(source)], check=True)
    skill.mkdir(parents=True)
    (skill / "SKILL.md.tmpl").write_text("{{ .fixture.value }}|{{ .chezmoi.targetFile }}\n")
    (skill / "name.tmpl.tmpl").write_text("{{ .fixture.value }}|{{ .chezmoi.targetFile }}\n")
    (skill / "payload.bin").write_bytes(b"\x00\xff{{ plain }}")
    if kind == "base":
        fixture.write_config(selection + '[data.fixture]\nvalue = "first"\n')
    else:
        config.write_text(selection + '[data.fixture]\nvalue = "first"\n')
    return source, destination, config, skill, roots, manifests


def _rendered_target_file(kind: str, root: Path, name: str) -> str:
    """Return .chezmoi.targetFile as a package template sees it.

    Native chezmoi rendering gives the absolute target path; capability file
    externals give the package-relative name.
    """
    return str(root / name) if kind == "base" else name


def _package_versions(manifests: list[Path]) -> list[str]:
    return [json.loads(path.read_text())["version"] for path in manifests]


def _technical_writing_fixture(agent_source_fixture):
    """Use the authored technical-writing source with real package output and versions."""
    fixture = agent_source_fixture
    skill = fixture.authored / "ai/skills/technical-writing"
    shutil.copytree(REPOSITORY_ROOT / "src/ai/skills/technical-writing", skill)
    fixture.write_config(
        '[data.ai.skills.authored]\ntechnical-writing = "present"\n[data.ai.skills.external]\n' + ANTIGRAVITY_ON
    )
    roots = [fixture.destination / root / "technical-writing" for root in AUTHORED_SKILL_ROOTS.values()]
    manifests = [fixture.destination / path for path in BUNDLE_MANIFESTS]
    return fixture.source, fixture.destination, fixture.config, skill, roots, manifests


@pytest.mark.parametrize(
    "optional_data",
    [
        "",
        "[data.ai.skills.content]\n",
        '[data.ai.skills.content.technical-writing]\ndescription = ""\ninstructions = ""\n',
    ],
    ids=["missing", "empty-parent", "empty-values"],
)
def test_technical_writing_default_package_preserves_original_bytes(agent_source_fixture, optional_data):
    """Missing optional content keeps the original skill bytes in every output."""
    source, destination, config, skill, roots, manifests = _technical_writing_fixture(agent_source_fixture)
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
def test_technical_writing_content_renders_merged_data_and_changes_package_versions(
    agent_source_fixture, content_layer
):
    """Content data changes YAML metadata and body bytes without changing the source."""
    source, destination, config, skill, roots, manifests = _technical_writing_fixture(agent_source_fixture)
    original_sources = {path.name: path.read_bytes() for path in skill.iterdir()}
    first = _apply_authored_cleanup(source, destination, config)
    assert first.returncode == 0, first.stderr
    original = (roots[0] / "SKILL.md").read_text()
    original_frontmatter, original_body = original.split("---\n", 2)[1:]
    original_versions = _package_versions(manifests)
    description = "Use when: \"quoted\" # content\nKeep 'single quotes' and \\paths."
    instructions = "## Additional instructions\nKeep the configured instruction.\n"
    catalog = source / ".chezmoidata/technical-writing.toml"
    catalog.parent.mkdir(exist_ok=True)
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
def test_rendered_package_versions_follow_data_and_stable_repeats(tmp_path, agent_source_factory, kind):
    """Data overrides change rendered bytes and every real manifest version."""
    source, destination, config, skill, roots, manifests = _rendered_package_fixture(
        tmp_path, kind, agent_source_factory
    )
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
        assert (root / "SKILL.md").read_text() == f"second|{_rendered_target_file(kind, root, 'SKILL.md')}\n"
        assert (root / "name.tmpl").read_text() == f"second|{_rendered_target_file(kind, root, 'name.tmpl')}\n"
    assert all(before != after for before, after in zip(original, _package_versions(manifests), strict=True))
    assert (skill / "SKILL.md.tmpl").read_text() == "{{ .fixture.value }}|{{ .chezmoi.targetFile }}\n"


@pytest.mark.parametrize("kind", ["base", "capability"])
def test_rendered_package_versions_ignore_fixture_location(tmp_path, agent_source_factory, kind):
    """Identical rendered bytes and metadata give the same versions in two checkouts."""
    versions = []
    for name in ("first", "second"):
        source, destination, config, _, _, manifests = _rendered_package_fixture(
            tmp_path / name, kind, agent_source_factory
        )
        result = _apply_authored_cleanup(source, destination, config)
        assert result.returncode == 0, result.stderr
        versions.append(_package_versions(manifests))
    assert versions[0] == versions[1]


@pytest.mark.parametrize("kind", ["base", "capability"])
def test_rendered_package_versions_follow_binary_bytes_and_executable_mode(tmp_path, agent_source_factory, kind):
    """Binary bytes and executable mode are part of all manifest versions."""
    source, destination, config, skill, roots, manifests = _rendered_package_fixture(
        tmp_path, kind, agent_source_factory
    )
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
def test_rendered_package_cleanup_removes_renamed_and_deleted_templates(tmp_path, agent_source_factory, kind):
    """Cleanup tracks rendered names, keeps sibling skills, and converges on repeat apply."""
    source, destination, config, skill, roots, _ = _rendered_package_fixture(tmp_path, kind, agent_source_factory)
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
        assert (root / "renamed").read_text() == f"first|{_rendered_target_file(kind, root, 'renamed')}\n"
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
    source, destination, config, skill, _, _ = _rendered_package_fixture(tmp_path, "capability", None)
    shutil.rmtree(source / ".chezmoiexternals")
    (skill / "SKILL.md").write_text("plain")
    result = _apply_authored_cleanup(source, destination, config)
    assert result.returncode != 0
    assert "collision" in result.stderr


@pytest.mark.parametrize(
    ("kind", "state"),
    [
        ("base", "absent"),
        ("base", "antigravity"),
        ("capability", "absent"),
        ("capability", "unlisted"),
    ],
)
def test_rendered_package_does_not_evaluate_inactive_skill_templates(tmp_path, agent_source_factory, kind, state):
    """Inactive authored templates must not require data for an enabled package."""
    source, destination, config, skill, _, manifests = _rendered_package_fixture(tmp_path, kind, agent_source_factory)
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
    source, destination, config, _, roots, manifests = _rendered_package_fixture(tmp_path, "capability", None)
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


def _write_skill(fixture, name: str, files: dict[str, str | bytes]) -> Path:
    skill = fixture.authored / "ai/skills" / name
    for relative, contents in files.items():
        path = skill / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(contents, bytes):
            path.write_bytes(contents)
        else:
            path.write_text(contents, encoding="utf-8")
    return skill


def _managed_files(fixture) -> set[str]:
    result = fixture.run("managed", "--include=files")
    assert result.returncode == 0, result.stderr
    return set(result.stdout.splitlines())


def _skill_views(managed: set[str], skill: str) -> set[str]:
    return {view for view, root in AUTHORED_SKILL_ROOTS.items() if f"{root}/{skill}/SKILL.md" in managed}


def _bundle_versions(fixture) -> list[str]:
    return [json.loads((fixture.destination / path).read_text())["version"] for path in BUNDLE_MANIFESTS]


def _apply_and_check(fixture) -> None:
    result = fixture.run("apply")
    assert result.returncode == 0, result.stderr


def _assert_stable(fixture) -> None:
    result = fixture.run("--no-pager", "diff")
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_hook_prepares_bare_skills_for_managed_cat_data_and_diff(agent_source_fixture):
    """The read-source-state hook publishes every view before chezmoi reads the source state."""
    fixture = agent_source_fixture
    fixture.write_config(ANTIGRAVITY_ON)
    _write_skill(fixture, "alpha", {"SKILL.md": "# Alpha\n", "references/notes.md": "notes\n"})
    assert not (fixture.source / ".agent-sources-manifest.json").exists()

    managed = _managed_files(fixture)
    assert _skill_views(managed, "alpha") == set(AUTHORED_SKILL_ROOTS)
    assert all(f"{root}/alpha/references/notes.md" in managed for root in AUTHORED_SKILL_ROOTS.values())
    manifest = json.loads((fixture.source / ".agent-sources-manifest.json").read_text())
    assert manifest["state"] == "complete"

    target = fixture.destination / AUTHORED_SKILL_ROOTS["claude"] / "alpha/SKILL.md"
    cat = fixture.run("cat", str(target))
    assert cat.returncode == 0, cat.stderr
    assert cat.stdout == "# Alpha\n"
    data = fixture.run("data", "--format=json")
    assert data.returncode == 0, data.stderr
    inventory = json.loads(data.stdout)["agent_source_inventory"]
    assert inventory["generator"] == "skill_filter.agent_sources"
    assert set(inventory["bare_skills"]) == {"alpha"}
    diff = fixture.run("--no-pager", "diff")
    assert diff.returncode == 0, diff.stderr
    assert "alpha/SKILL.md" in diff.stdout

    _apply_and_check(fixture)
    for root in AUTHORED_SKILL_ROOTS.values():
        assert (fixture.destination / root / "alpha/SKILL.md").read_text() == "# Alpha\n"
    _assert_stable(fixture)


def test_added_bare_skill_deploys_without_catalog_entry(agent_source_fixture):
    """A new skill directory deploys to every default view and changes the bundle version."""
    fixture = agent_source_fixture
    _write_skill(fixture, "alpha", {"SKILL.md": "# Alpha\n"})
    _apply_and_check(fixture)
    versions = _bundle_versions(fixture)

    _write_skill(fixture, "beta", {"SKILL.md": "# Beta\n"})
    _apply_and_check(fixture)
    for view, root in AUTHORED_SKILL_ROOTS.items():
        assert (fixture.destination / root / "beta/SKILL.md").is_file() is (view != "antigravity")
    changed = _bundle_versions(fixture)
    assert all(before != after for before, after in zip(versions, changed, strict=True))
    _assert_stable(fixture)
    assert _bundle_versions(fixture) == changed


@pytest.mark.parametrize("antigravity", [True, False], ids=["gate-on", "gate-off"])
@pytest.mark.parametrize(
    ("state", "expected"),
    [("absent", set()), ("claude", {"claude"}), ("antigravity", {"antigravity"})],
)
def test_bare_skill_exceptions_ignore_absent_single_host_and_antigravity_gate(
    agent_source_fixture, state, expected, antigravity
):
    """Exceptions and the Antigravity gate select views through the generated ignore files."""
    fixture = agent_source_fixture
    fixture.write_config(f'[data.ai.skills.authored]\nfixture = "{state}"\n' + (ANTIGRAVITY_ON if antigravity else ""))
    _write_skill(fixture, "fixture", {"SKILL.md": "# Fixture\n"})
    _write_skill(fixture, "other", {"SKILL.md": "# Other\n"})
    if not antigravity:
        expected = expected - {"antigravity"}
    everything = set(AUTHORED_SKILL_ROOTS) if antigravity else set(AUTHORED_SKILL_ROOTS) - {"antigravity"}

    managed = _managed_files(fixture)
    assert _skill_views(managed, "fixture") == expected
    assert _skill_views(managed, "other") == everything
    _apply_and_check(fixture)
    for view, root in AUTHORED_SKILL_ROOTS.items():
        assert (fixture.destination / root / "fixture").exists() is (view in expected)
    _assert_stable(fixture)


@pytest.mark.parametrize(("state", "succeeds"), [("present", False), ("claude", False), ("absent", True)])
def test_bare_skill_exception_for_missing_skill_fails_unless_absent(agent_source_fixture, state, succeeds):
    """Only an absent exception may name a skill without a source directory."""
    fixture = agent_source_fixture
    fixture.write_config(f'[data.ai.skills.authored]\nmissing = "{state}"\n')
    _write_skill(fixture, "alpha", {"SKILL.md": "# Alpha\n"})
    result = fixture.run("managed", "--include=files")
    assert (result.returncode == 0) is succeeds, result.stderr
    if not succeeds:
        assert "ai.skills.authored.missing" in result.stderr


def test_bare_skill_template_change_updates_content_and_base_version(agent_source_fixture):
    """Editing a SKILL.md.tmpl updates every target and every bundle version on the next apply."""
    fixture = agent_source_fixture
    fixture.write_config('[data.fixture]\nvalue = "data"\n')
    skill = _write_skill(fixture, "alpha", {"SKILL.md.tmpl": "first {{ .fixture.value }}\n"})
    roots = [root for view, root in AUTHORED_SKILL_ROOTS.items() if view != "antigravity"]
    _apply_and_check(fixture)
    assert all((fixture.destination / root / "alpha/SKILL.md").read_text() == "first data\n" for root in roots)
    versions = _bundle_versions(fixture)

    (skill / "SKILL.md.tmpl").write_text("second {{ .fixture.value }}\n", encoding="utf-8")
    _apply_and_check(fixture)
    assert all((fixture.destination / root / "alpha/SKILL.md").read_text() == "second data\n" for root in roots)
    changed = _bundle_versions(fixture)
    assert all(before != after for before, after in zip(versions, changed, strict=True))
    _apply_and_check(fixture)
    assert _bundle_versions(fixture) == changed
    _assert_stable(fixture)


def test_literal_dot_executable_empty_and_attribute_like_names_deploy(agent_source_fixture):
    """Canonical names deploy literally; modes and empty files survive the projection."""
    fixture = agent_source_fixture
    files: dict[str, str | bytes] = {
        "SKILL.md": "# Alpha\n",
        ".hidden": "hidden\n",
        ".config/settings": "settings\n",
        "run.sh": "#!/bin/sh\necho run\n",
        "empty.txt": b"",
        "exact_name.md": "exact\n",
        "dot_name": "dot\n",
        "executable_tool": "tool\n",
        "private_dir/run_me": "nested\n",
    }
    skill = _write_skill(fixture, "alpha", files)
    (skill / "run.sh").chmod(0o755)
    _apply_and_check(fixture)
    for view, root in AUTHORED_SKILL_ROOTS.items():
        target = fixture.destination / root / "alpha"
        if view == "antigravity":
            assert not target.exists()
            continue
        deployed = {path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()}
        assert deployed == set(files)
        for relative, contents in files.items():
            expected = contents if isinstance(contents, bytes) else contents.encode()
            assert (target / relative).read_bytes() == expected
        assert (target / "run.sh").stat().st_mode & 0o111
        assert not (target / "executable_tool").stat().st_mode & 0o111
    _assert_stable(fixture)


def test_failed_preparation_keeps_previous_generated_tree(agent_source_fixture):
    """Invalid sources stop chezmoi and leave the previous generated tree untouched."""
    fixture = agent_source_fixture
    _write_skill(fixture, "alpha", {"SKILL.md": "# Alpha\n"})
    _managed_files(fixture)
    manifest = fixture.source / ".agent-sources-manifest.json"
    inventory = fixture.source / ".chezmoidata/agent-source-inventory.json"
    before = (manifest.read_bytes(), inventory.read_bytes())

    broken = _write_skill(fixture, "broken", {"notes.md": "no skill file\n"})
    failed = fixture.run("managed", "--include=files")
    assert failed.returncode != 0
    assert "missing SKILL.md" in failed.stderr
    assert (manifest.read_bytes(), inventory.read_bytes()) == before

    shutil.rmtree(broken)
    assert _skill_views(_managed_files(fixture), "alpha") == set(AUTHORED_SKILL_ROOTS) - {"antigravity"}


def test_generated_paths_are_gitignored(tmp_path, checkout_config):
    """Every path that preparation publishes into the real checkout is ignored by git."""
    source = REPOSITORY_ROOT / "src/chezmoi"
    result = subprocess.run(
        [
            "chezmoi",
            "--source",
            str(REPOSITORY_ROOT),
            "--destination",
            str(tmp_path / "home"),
            "--config",
            str(checkout_config),
            "--persistent-state",
            str(tmp_path / "chezmoistate.boltdb"),
            "--cache",
            str(tmp_path / "cache"),
            "managed",
            "--include=files",
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, result.stderr
    manifest = json.loads((source / ".agent-sources-manifest.json").read_text())
    generated = [f"src/chezmoi/{path}" for path in (*manifest["paths"], ".agent-sources-manifest.json")]
    assert generated
    for path in generated:
        ignored = subprocess.run(["git", "-C", str(REPOSITORY_ROOT), "check-ignore", "-q", path], check=False)
        assert ignored.returncode == 0, f"{path} is not ignored by git"
    status = subprocess.run(
        ["git", "-C", str(REPOSITORY_ROOT), "status", "--porcelain", "--untracked-files=all", "--", *generated],
        capture_output=True,
        check=True,
        text=True,
    )
    assert status.stdout == ""


def test_capability_cleanup_keeps_cursor_manifest_with_default_hosts(agent_source_fixture):
    """Default hosts keep the owned Cursor manifest in the capability cleanup's desired set."""
    fixture = agent_source_fixture
    cleanup = "run_onchange_after_00-agent-plugin-authored-capabilities-cleanup.sh.tmpl"
    target = fixture.source / ".chezmoiscripts" / cleanup
    target.parent.mkdir(parents=True)
    shutil.copy2(REPOSITORY_ROOT / "src/chezmoi/.chezmoiscripts" / cleanup, target)
    _write_skill(fixture, "alpha", {"SKILL.md": "# Alpha\n"})
    manifest = ".cursor/plugins/local/mkobit-dotfiles/.cursor-plugin/plugin.json"
    state = fixture.destination / ".local/state/dotfiles/agent-plugin-capability-ownership.json"
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({"version": 1, "paths": [manifest]}) + "\n")

    _apply_and_check(fixture)
    assert json.loads((fixture.destination / manifest).read_text())["name"] == "mkobit-dotfiles"
    assert json.loads(state.read_text())["paths"] == [manifest]


@pytest.mark.parametrize("bare_state", ["present", "absent"])
def test_external_skill_named_like_bare_skill_fails(agent_source_fixture, bare_state):
    """An external skill cannot share a bare skill name, whatever the bare skill state."""
    fixture = agent_source_fixture
    external = REPOSITORY_ROOT / "src/chezmoi/.chezmoiexternals/ai-skills.toml.tmpl"
    target = fixture.source / ".chezmoiexternals" / external.name
    target.parent.mkdir(parents=True)
    shutil.copy2(external, target)
    fixture.write_config(
        f'[data.ai.skills.authored]\nalpha = "{bare_state}"\n'
        '[data.ai.skills.hosts.github]\nurl_format = "https://example.invalid/{repo}/{ref}.tar.gz"\n'
        '[data.ai.skills.external.upstream]\nrepo = "owner/repo"\nref = "0123456789abcdef"\nsha256 = "00"\n'
        '[data.ai.skills.external.upstream.skills]\nalpha = "present"\n'
    )
    _write_skill(fixture, "alpha", {"SKILL.md": "# Alpha\n"})
    result = fixture.run("managed", "--include=files")
    assert result.returncode != 0
    assert "ai.skills.external.upstream.skills.alpha: name equals bare skill" in result.stderr
