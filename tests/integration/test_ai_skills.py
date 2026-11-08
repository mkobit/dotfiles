import hashlib
import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest
from chezmoi_test_data import installation_method

# Antigravity remains a direct skill consumer.
DIRECT_SKILL_DIRS = [
    pytest.param(Path(".gemini/antigravity-cli/skills"), frozenset(), id="antigravity"),
]

# Claude, Codex, and Cursor share one mkobit-dotfiles plugin folder; each reads its own manifest.
PLUGIN_DIR = Path(".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles")
PLUGIN_HOSTS = ["claude", "codex", "cursor"]

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src/chezmoi"
BUNDLE_SOURCE = SOURCE_ROOT / "dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles"


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


def _apply(source: Path, destination: Path, config: Path) -> subprocess.CompletedProcess[str]:
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


def _render(relative: str) -> str:
    """Render one real source template with catalog data only."""
    result = subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPOSITORY_ROOT),
            "execute-template",
            "--file",
            str(SOURCE_ROOT / relative),
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


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
@pytest.mark.parametrize("plugin_host", PLUGIN_HOSTS)
def test_plugin_host_manifest_deployed_and_valid(chezmoi_dest, plugin_host):
    """Every host reads its own manifest in the shared plugin folder, and no direct copies remain."""
    plugin_dir = chezmoi_dest / PLUGIN_DIR
    manifest = json.loads((plugin_dir / f".{plugin_host}-plugin/plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "mkobit-dotfiles"
    assert manifest["version"].startswith("1.0.0+")
    assert manifest["author"] == {"name": "mkobit"}
    skills = manifest["skills"] if isinstance(manifest["skills"], list) else [manifest["skills"]]
    assert "./skills" in skills
    for path in skills:
        assert_entries_are_valid_skills(plugin_dir / path)
    if plugin_host == "codex":
        assert set(manifest["interface"]["capabilities"]) >= {path.name for path in _entries(plugin_dir / "skills")}
    direct_skills_dir = chezmoi_dest / f".{plugin_host}" / "skills"
    for plugin_skill in _entries(plugin_dir / "skills"):
        assert not (direct_skills_dir / plugin_skill.name).exists(), (
            f"{plugin_skill.name} remains in {direct_skills_dir}"
        )


@pytest.mark.integration
def test_antigravity_plugin_manifest_deployed_and_valid(chezmoi_dest):
    """Antigravity reads the plugin root manifest and its skills."""
    manifest = json.loads((chezmoi_dest / PLUGIN_DIR / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "mkobit-dotfiles"
    assert manifest["skills"] == ["./skills"]
    assert manifest["version"].startswith("1.0.0+")


@pytest.mark.integration
def test_marketplace_manifests_deployed_and_valid(chezmoi_dest):
    """Verify marketplace manifests and bridge provenance are deployed and valid."""
    marketplace = chezmoi_dest / ".local/share/agent-plugins/marketplace"
    codex = json.loads((marketplace / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    assert codex["name"] == "dotfiles"
    codex_plugins = {plugin["name"]: plugin for plugin in codex["plugins"]}
    assert codex_plugins["mkobit-dotfiles"]["source"]["path"] == "./plugins/mkobit-dotfiles"
    for host_path in (".claude-plugin/marketplace.json", ".cursor-plugin/marketplace.json"):
        data = json.loads((marketplace / host_path).read_text(encoding="utf-8"))
        assert data["name"] == "dotfiles"
        plugins = {plugin["name"]: plugin["source"] for plugin in data["plugins"]}
        assert plugins["mkobit-dotfiles"] == "./plugins/mkobit-dotfiles"

    superpowers_root = chezmoi_dest / ".local/share/agent-plugins/marketplaces/superpowers-marketplace"
    superpowers_agents = json.loads((superpowers_root / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    assert superpowers_agents["name"] == "superpowers-marketplace"
    superpowers_agents_plugins = {plugin["name"]: plugin for plugin in superpowers_agents["plugins"]}
    assert superpowers_agents_plugins["superpowers"]["source"]["path"] == "./plugins/superpowers"
    superpowers_claude = json.loads((superpowers_root / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    superpowers_claude_plugins = {plugin["name"]: plugin for plugin in superpowers_claude["plugins"]}
    assert superpowers_claude_plugins["superpowers"]["source"] == "./plugins/superpowers"

    json.loads((marketplace / "bridge-provenance.json").read_text(encoding="utf-8"))


def test_host_skill_roots_tombstone_base_and_retired_skills():
    """Old direct copies of base bare and retired skills are removed from every host skill root."""
    for relative, prefix in (
        ("dot_claude/.chezmoiremove.tmpl", "skills/"),
        ("dot_codex/.chezmoiremove.tmpl", "skills/"),
        ("dot_cursor/.chezmoiremove.tmpl", "skills/"),
    ):
        lines = set(_render(relative).splitlines())
        for name in ("beads", "technical-writing", "docker-sandboxes", "example_skill"):
            assert f"{prefix}{name}" in lines, (relative, name)
    cursor = set(_render("dot_cursor/.chezmoiremove.tmpl").splitlines())
    assert "plugins/local/mkobit-dotfiles" not in cursor


GLOBAL_MODERN_WEB_PATHS = (
    ".cursor/plugins/local/modern-web-guidance",
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
def test_global_modern_web_guidance_removed(chezmoi_dest):
    """Global guidance copies are absent after apply."""
    for relative in GLOBAL_MODERN_WEB_PATHS:
        assert not (chezmoi_dest / relative).exists(), relative
    for agent in (".claude", ".codex"):
        cache = chezmoi_dest / agent / "plugins/cache/dotfiles/mkobit-dotfiles"
        for skill in ("modern-web-guidance", "chrome-extensions"):
            assert not list(cache.glob(f"*/skills/{skill}")), (agent, skill)


@pytest.mark.integration
def test_plugin_bridge_ownership_state(chezmoi_dest):
    """Verify agent-plugin ownership records have five tab-separated fields with a provenance."""
    state_file = chezmoi_dest / ".local/state/dotfiles/agent-plugin-ownership"
    if not state_file.is_file():
        return
    for line in state_file.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        fields = line.split("\t")
        assert len(fields) == 5, f"expected 5 tab-separated fields in {line!r}, got {len(fields)}"
        assert fields[4] in {"owned", "ambiguous"}, line


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


def test_technical_writing_template_accepts_missing_ai_root(tmp_path):
    """The optional content path is safe when the entire ai data root is absent."""
    skill_root = BUNDLE_SOURCE / "exact_skills/exact_technical-writing"
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
