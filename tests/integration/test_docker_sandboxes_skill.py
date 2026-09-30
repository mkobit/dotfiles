from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "src" / "ai" / "skills" / "docker-sandboxes"
SKILL_FILE = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"
TEMPLATES_DIR = SKILL_DIR / "templates"


def test_skill_describes_host_coordinated_repository_sandboxes():
    """Keep host coordination and repository ownership explicit."""
    skill = SKILL_FILE.read_text(encoding="utf-8")

    for required in (
        "Docker Sandbox",
        "AGENTS.md",
        "repository-owned",
        "clone: false",
        "immediately visible",
        "commits, signing, and pushes",
        "private clone",
        "sbx env create",
        "sbx env rm",
        "references/repository-setup.md",
        "references/environment-files.md",
        "references/agents.md",
        "references/nested-execution.md",
    ):
        assert required in skill, f"Missing {required!r} in {SKILL_FILE}"


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
