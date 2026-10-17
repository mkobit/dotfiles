import fnmatch
import shutil
import tomllib
from pathlib import Path

import pytest
import yaml
from test_ai_skills import (
    CAPABILITY_AUTHORED_SKILL_ROOTS,
    _apply_authored_cleanup,
    _initialize_authored_cleanup_source,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "src" / "ai" / "skills" / "sbx-sandboxes"
SKILL_FILE = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"
TEMPLATES_DIR = SKILL_DIR / "templates"


@pytest.mark.parametrize(
    "command",
    [
        "sbx --help",
        "sbx env exec --help",
        "sbx ls --format json",
        "sbx diagnose --format json",
        "sbx env exec .sbx/sbxenv.yaml -- find / -name agy",
        "sbx env exec /tmp/project/.sbx/custom.yaml -- bun test",
        "sbx env exec ../other/environment.yaml -- codex exec task",
        "sbx env exec .sbx/base.yaml .sbx/override.yaml -- pytest",
        'sbx env exec "/tmp/project with spaces/environment.yaml" -- bun test',
        "sbx exec routine-flow-agy which agy",
        "sbx exec routine-flow-agy agy --help",
    ],
)
def test_skill_grants_execution_and_discovery(command: str) -> None:
    """Cover discovery and guest execution patterns in the package metadata."""
    metadata = yaml.safe_load(SKILL_FILE.read_text(encoding="utf-8").split("---", 2)[1])
    patterns = [entry.removeprefix("Bash(").removesuffix(")") for entry in metadata["allowed-tools"]]
    assert any(fnmatch.fnmatchcase(command, pattern) for pattern in patterns)


@pytest.mark.parametrize(
    "command",
    [
        "sbx rm task",
        "sbx reset",
        "sbx kit add task kit",
        "sbx diagnose --upload",
        "sbx diagnose --format json --upload",
        "sbx env create environment.yaml",
    ],
)
def test_skill_does_not_grant_lifecycle_or_upload(command: str) -> None:
    """Keep lifecycle changes and report uploads outside the grants."""
    metadata = yaml.safe_load(SKILL_FILE.read_text(encoding="utf-8").split("---", 2)[1])
    patterns = [entry.removeprefix("Bash(").removesuffix(")") for entry in metadata["allowed-tools"]]
    assert not any(fnmatch.fnmatchcase(command, pattern) for pattern in patterns)


def test_renamed_skill_deploys_and_removes_old_copies(tmp_path: Path) -> None:
    """Deploy the renamed package and remove only retired skill copies."""
    source, destination = tmp_path / "source", tmp_path / "destination"
    destination.mkdir()
    _initialize_authored_cleanup_source(source, include_external=True)
    catalog = tomllib.loads((REPO_ROOT / "src/chezmoi/.chezmoidata/ai/skills/authored.toml").read_text())
    selected = {name: catalog["ai"]["skills"]["authored"][name] for name in ("docker-sandboxes", "sbx-sandboxes")}
    shutil.copytree(SKILL_DIR, source / "src/ai/skills/sbx-sandboxes")
    direct_roots = (".claude/skills", ".codex/skills", ".cursor/skills", ".gemini/antigravity-cli/skills")
    for root in (*CAPABILITY_AUTHORED_SKILL_ROOTS.values(), *direct_roots):
        old = destination / root / "docker-sandboxes/SKILL.md"
        old.parent.mkdir(parents=True, exist_ok=True)
        old.write_text("old skill")
    for host in (".claude", ".codex"):
        for package, skill in (
            ("mkobit-dotfiles", "docker-sandboxes"),
            ("mkobit-dotfiles", "other-skill"),
            ("other-plugin", "docker-sandboxes"),
        ):
            cached = destination / host / "plugins/cache/dotfiles" / package / "1.0.0/skills" / skill / "SKILL.md"
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_text("cached")
    for target in ("dot_claude", "dot_codex", "dot_cursor", "dot_gemini"):
        (source / "src/chezmoi" / target).mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            REPO_ROOT / "src/chezmoi" / target / ".chezmoiremove.tmpl",
            source / "src/chezmoi" / target / ".chezmoiremove.tmpl",
        )
    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "[data.ai.skills.authored]\n"
        + "".join(f'{name} = "{state}"\n' for name, state in selected.items())
        + '\n[data.ai.skills.external]\n[data.ai.agents.external]\n[data.local.bin.agy]\ninstallation_method = "system"\n'
    )
    result = _apply_authored_cleanup(source, destination, config)
    assert result.returncode == 0, result.stderr
    for root in (*CAPABILITY_AUTHORED_SKILL_ROOTS.values(), *direct_roots):
        assert not (destination / root / "docker-sandboxes").exists()
    for host in (".claude", ".codex"):
        cache = destination / host / "plugins/cache/dotfiles"
        assert not (cache / "mkobit-dotfiles/1.0.0/skills/docker-sandboxes").exists()
        assert (cache / "mkobit-dotfiles/1.0.0/skills/other-skill/SKILL.md").is_file()
        assert (cache / "other-plugin/1.0.0/skills/docker-sandboxes/SKILL.md").is_file()
    for root in CAPABILITY_AUTHORED_SKILL_ROOTS.values():
        deployed = destination / root / "sbx-sandboxes"
        assert (deployed / "SKILL.md").read_bytes() == SKILL_FILE.read_bytes()
        assert (deployed / "references/subagent-task.md").is_file()


def test_skill_describes_host_coordinated_repository_sandboxes():
    """Keep host coordination and repository ownership explicit."""
    skill = SKILL_FILE.read_text(encoding="utf-8")

    for required in (
        "sbx",
        "repository-owned",
        "clone: false",
        "immediately visible",
        "commits, signing, and pushes",
        "private clone",
        "references/repository-setup.md",
        "references/environment-files.md",
        "references/agents.md",
        "references/nested-execution.md",
    ):
        assert required in skill, f"Missing {required!r} in {SKILL_FILE}"

    setup_file = REFERENCES_DIR / "repository-setup.md"
    setup = setup_file.read_text(encoding="utf-8")
    for required in (
        "sbx env create .sbx/sbxenv.yaml",
        "Remove the environment only when authorized",
    ):
        assert required in setup, f"Missing {required!r} in {setup_file}"


def test_skill_ships_direct_mounted_project_environment_templates():
    """Keep every harness project-owned and direct-mounted by default."""
    codex = yaml.safe_load((TEMPLATES_DIR / "codex.sbxenv.yaml").read_text(encoding="utf-8"))
    agy = yaml.safe_load((TEMPLATES_DIR / "agy.sbxenv.yaml").read_text(encoding="utf-8"))
    claude = yaml.safe_load((TEMPLATES_DIR / "claude.sbxenv.yaml").read_text(encoding="utf-8"))

    assert codex["schemaVersion"] == "1"
    assert codex["agent"] == "codex"
    assert codex["workspace"] == {"path": "..", "clone": False}
    assert codex["kits"] == ["./kit"]

    assert agy["schemaVersion"] == "1"
    assert agy["agent"] == "antigravity"
    assert agy["workspace"] == {"path": "..", "clone": False}
    assert agy["kits"] == [
        "./kit",
        "git+https://github.com/docker/sbx-kits-contrib.git#ref=21e1928b5fe0036163307ea8047e48390f2d6fec&dir=antigravity",
    ]

    assert claude["schemaVersion"] == "1"
    assert claude["agent"] == "claude"
    assert claude["workspace"] == {"path": "..", "clone": False}
    assert claude["kits"] == ["./kit"]

    for environment in (codex, agy, claude):
        assert not {"secrets", "bindings", "registries", "mcp", "additionalWorkspaces"} & set(environment)


def test_skill_references_record_the_pinned_agy_supply_chain_and_boundary():
    """Keep the experimental AGY path auditable and repository-owned."""
    pin = (REFERENCES_DIR / "upstream-pins.md").read_text(encoding="utf-8")
    environment_files = (REFERENCES_DIR / "environment-files.md").read_text(encoding="utf-8")

    assert "21e1928b5fe0036163307ea8047e48390f2d6fec" in pin
    assert "6fba87a5f2e3b76003e9efe3410572cbb47d925adc8b1aaafeab2f786841b0e9" in pin
    for prohibited in ("secrets", "bindings", "registries", "local-command MCP"):
        assert prohibited in environment_files


def test_skill_documents_the_confirmation_gated_agy_kit_allowlist_prerequisite():
    """Keep the Git-pinned AGY kit usable without silently broadening host policy."""
    agents = (REFERENCES_DIR / "agents.md").read_text(encoding="utf-8")

    for required in ("kit.allowedSources", "github.com/docker/", "confirmation", "preserv"):
        assert required in agents


def test_skill_has_no_host_managed_guest_customization_paths():
    """Keep guest contents wholly owned by the consuming repository."""
    prohibited = (
        "optional-host-overlays",
        "personal.sbxenv",
        "shareSkills",
        "skills-kit",
        "codex-kit",
        ".local/share/sbx/personal",
        "tool-cache",
        "sbx.personal",
    )

    for path in SKILL_DIR.rglob("*"):
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            for phrase in prohibited:
                assert phrase not in content, f"Unexpected {phrase!r} in {path}"
