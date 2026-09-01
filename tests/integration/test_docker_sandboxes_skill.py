from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "src" / "ai" / "skills" / "docker-sandboxes"
SKILL_FILE = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"
TEMPLATES_DIR = SKILL_DIR / "templates"


def test_skill_routes_repository_setup_through_progressive_references():
    """Keep repository sandbox setup reusable without host-owned launcher details."""
    skill = SKILL_FILE.read_text(encoding="utf-8")

    for required in (
        "sbx version",
        "AGENTS.md",
        ".agents/skills",
        "CI",
        "confirmation",
        "references/repository-setup.md",
        "references/environment-files.md",
        "references/agents.md",
        "references/optional-host-overlays.md",
    ):
        assert required in skill, f"Missing {required!r} in {SKILL_FILE}"


def test_skill_ships_clone_only_agent_environment_templates():
    """Keep Codex and AGY project environments separate and host-safe by default."""
    codex = yaml.safe_load((TEMPLATES_DIR / "codex.sbxenv.yaml").read_text(encoding="utf-8"))
    agy = yaml.safe_load((TEMPLATES_DIR / "agy.sbxenv.yaml").read_text(encoding="utf-8"))

    assert codex["schemaVersion"] == "1"
    assert codex["agent"] == "codex"
    assert codex["workspace"] == {"path": "..", "clone": True}

    assert agy["schemaVersion"] == "1"
    assert agy["agent"] == "agy"
    assert agy["workspace"] == {"path": "..", "clone": True}
    assert agy["kits"] == [
        "git+https://github.com/shelajev/agy-sbx-kit.git#ref=3e7016f108f3cf09922cf351b55a49e38d97f9f2"
    ]

    for environment in (codex, agy):
        assert not {"secrets", "bindings", "registries", "mcp", "additionalWorkspaces"} & set(environment)


def test_skill_references_record_the_pinned_agy_supply_chain_and_safety_boundary():
    """Keep the experimental AGY path auditable and avoid host-authority project config."""
    pin = (REFERENCES_DIR / "upstream-pins.md").read_text(encoding="utf-8")
    environment_files = (REFERENCES_DIR / "environment-files.md").read_text(encoding="utf-8")

    assert "3e7016f108f3cf09922cf351b55a49e38d97f9f2" in pin
    assert "cd2fec52b532a9136550ba0051bde6eb5ea17cb8f86ad9c0cb1475c54dc17d1a" in pin
    for prohibited in ("secrets", "bindings", "registries", "local-command MCP", "direct mount"):
        assert prohibited in environment_files
