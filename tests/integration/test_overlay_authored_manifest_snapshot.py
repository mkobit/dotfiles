"""Integration coverage for overlay authored manifest source snapshots."""

import dataclasses
import json
import shutil


def test_manifest_version_uses_assembled_authored_plugin_snapshot(agent_source_fixture):
    """Preparation reads the assembled-like tree, so checkout-only edits never change the version."""
    checkout = agent_source_fixture
    assembled = checkout.repo / ".chezmoiroot.assembled"
    shutil.move(str(checkout.source), str(assembled / "chezmoi"))
    (checkout.repo / ".chezmoiroot").write_text(".chezmoiroot.assembled/chezmoi\n", encoding="utf-8")
    fixture = dataclasses.replace(checkout, source=assembled / "chezmoi", authored=assembled)
    fixture.write_config()

    identity = {"description": "Domain Intelligence workflows.", "skills_source_dir": "src/overlay-skills"}
    for tree in (checkout, fixture):
        tree.write_plugin("domain-brain", identity, wrappers={"claude": {"source.txt": f"{tree.authored.name} v1\n"}})
        skill = tree.authored / "overlay-skills/records/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(f"{tree.authored.name} skill\n", encoding="utf-8")
    manifest = (
        fixture.destination
        / ".local/share/agent-plugins/marketplace/plugins/domain-brain/claude/.claude-plugin/plugin.json"
    )
    skill_target = manifest.parents[1] / "skills/records/SKILL.md"

    def render_version() -> str:
        result = fixture.run("apply")
        assert result.returncode == 0, result.stderr
        return json.loads(manifest.read_text(encoding="utf-8"))["version"]

    initial = render_version()
    assert skill_target.read_text(encoding="utf-8") == ".chezmoiroot.assembled skill\n"
    assert not (checkout.repo / "src/chezmoi").exists()
    (checkout.authored / "overlay-plugins/domain-brain/wrappers/claude/source.txt").write_text("src v2\n")
    assert render_version() == initial
    (checkout.authored / "overlay-skills/records/SKILL.md").write_text("src skill v2\n")
    assert render_version() == initial

    (assembled / "overlay-plugins/domain-brain/wrappers/claude/source.txt").write_text("assembled v2\n")
    source_updated = render_version()
    assert source_updated != initial
    (assembled / "overlay-skills/records/SKILL.md").write_text("assembled skill v2\n")
    assert render_version() != source_updated
    assert skill_target.read_text(encoding="utf-8") == "assembled skill v2\n"
