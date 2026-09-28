import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

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
FILTER_INTERPRETER_TEMPLATE = REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/python/filter-interpreter"
FILTER_INTERPRETER_RESOLVER = REPOSITORY_ROOT / "src/python/skill_filter/resolve-interpreter.sh"
AUTHORED_SKILL_ROOTS = {
    "portable": Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills"),
    "claude": Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/claude/skills"),
    "codex": Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/codex/skills"),
    "cursor": Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/cursor/skills"),
    "antigravity": Path(".gemini/antigravity-cli/skills"),
}


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
    source_files = [
        (AUTHORED_CLEANUP_SCRIPT, Path(".chezmoiscripts") / AUTHORED_CLEANUP_SCRIPT.name),
        (FILTER_INTERPRETER_TEMPLATE, Path(".chezmoitemplates/python/filter-interpreter")),
        (FILTER_INTERPRETER_RESOLVER, Path("src/python/skill_filter/resolve-interpreter.sh")),
    ]
    if include_external:
        source_files.append((AUTHORED_SKILLS_EXTERNAL, Path(".chezmoiexternals") / AUTHORED_SKILLS_EXTERNAL.name))
    for source_file, relative_target in source_files:
        assert source_file.is_file(), f"missing cleanup fixture dependency: {source_file}"
        target = source / relative_target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)
    subprocess.run(["git", "init", "--quiet", str(source)], check=True)


@pytest.mark.parametrize(
    ("state", "antigravity_enabled", "expected_roots"),
    [
        ("present", True, frozenset(AUTHORED_SKILL_ROOTS)),
        ("claude", True, frozenset({"claude"})),
        ("antigravity", True, frozenset({"antigravity"})),
        ("present", False, frozenset({"portable", "claude", "codex", "cursor"})),
        ("antigravity", False, frozenset()),
    ],
)
def test_authored_skill_cleanup_prunes_renamed_nested_file_only_from_selected_roots(
    tmp_path, state, antigravity_enabled, expected_roots
):
    """A selected authored skill's old nested path is removed on the next apply."""
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    destination.mkdir()
    _initialize_authored_cleanup_source(source, include_external=True)

    skill_source = source / "overlay-skills" / "fixture"
    (skill_source / "references").mkdir(parents=True)
    (skill_source / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")
    stale_source = skill_source / "references" / "old-name.md"
    stale_source.write_text("old\n", encoding="utf-8")

    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.skills]",
                'overlay_authored_source = "overlay-skills"',
                "",
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

    for root_name, root in AUTHORED_SKILL_ROOTS.items():
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
    for root in AUTHORED_SKILL_ROOTS.values():
        assert (destination / root / "fixture/SKILL.md").is_file()
        assert (destination / root / "fixture/references/old-name.md").is_file()

    stale_source.rename(skill_source / "references" / "new-name.md")

    second_apply = _apply_authored_cleanup(source, destination, config)
    assert second_apply.returncode == 0, second_apply.stderr
    for root_name, root in AUTHORED_SKILL_ROOTS.items():
        stale_target = destination / root / "fixture/references/old-name.md"
        assert stale_target.exists() is (root_name not in expected_roots)
        assert (destination / root / "fixture/references/new-name.md").exists() is (root_name in expected_roots)
        assert (destination / root / "fixture/SKILL.md").is_file()
        assert (destination / root / "external-skill/SKILL.md").is_file()


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

    skill_source = source / "overlay-skills" / "fixture"
    skill_source.mkdir(parents=True)
    (skill_source / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")
    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.skills]",
                'overlay_authored_source = "overlay-skills"',
                "",
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

    skill_source = source / "overlay-skills" / "fixture"
    skill_source.mkdir(parents=True)
    (skill_source / "SKILL.md").write_text("# Fixture\n", encoding="utf-8")
    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.skills]",
                'overlay_authored_source = "overlay-skills"',
                "",
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

    skill_source = source / "overlay-skills" / "fixture"
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
                "[data.ai.skills]",
                'overlay_authored_source = "overlay-skills"',
                "",
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
def test_direct_skill_dir_deployed_and_valid(chezmoi_dest, relative_dir, allowed_marker_files):
    """Verify each direct skill consumer receives a non-empty valid skill tree."""
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
    assert manifest["skills"] == "./skills"
    assert manifest["version"].startswith("1.0.0+")


@pytest.mark.integration
def test_marketplace_manifests_deployed_and_valid(chezmoi_dest):
    """Verify marketplace manifests and bridge provenance are deployed and valid."""
    agents_marketplace = chezmoi_dest / ".local/share/agent-plugins/marketplace/.agents/plugins/marketplace.json"
    assert agents_marketplace.is_file(), f"{agents_marketplace} does not exist after chezmoi apply"
    agents_data = json.loads(agents_marketplace.read_text(encoding="utf-8"))
    assert agents_data["name"] == "dotfiles"
    assert agents_data["plugins"][0]["name"] == "mkobit-dotfiles"
    assert agents_data["plugins"][0]["source"]["path"] == "./plugins/mkobit-dotfiles/codex"

    claude_marketplace = chezmoi_dest / ".local/share/agent-plugins/marketplace/.claude-plugin/marketplace.json"
    assert claude_marketplace.is_file(), f"{claude_marketplace} does not exist after chezmoi apply"
    claude_data = json.loads(claude_marketplace.read_text(encoding="utf-8"))
    assert claude_data["name"] == "dotfiles"
    assert claude_data["plugins"][0]["name"] == "mkobit-dotfiles"
    claude_source = claude_data["plugins"][0]["source"]
    claude_path = claude_source["path"] if isinstance(claude_source, dict) else claude_source
    assert claude_path == "./plugins/mkobit-dotfiles/claude"

    provenance_path = chezmoi_dest / ".local/share/agent-plugins/marketplace/bridge-provenance.json"
    assert provenance_path.is_file(), f"{provenance_path} does not exist after chezmoi apply"
    json.loads(provenance_path.read_text(encoding="utf-8"))


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
