"""Integration coverage for overlay authored manifest source snapshots."""

import json
import shutil
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AUTHORED_TEMPLATE_ROOT = REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/ai"


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
            "apply",
        ],
        capture_output=True,
        check=False,
        cwd=destination.parent,
        text=True,
    )


def test_manifest_version_uses_assembled_authored_plugin_snapshot(tmp_path):
    """Manifest inputs follow assembled plugin files and ignore checkout-only edits."""
    checkout = tmp_path / "overlay"
    source = checkout / ".chezmoiroot.assembled/chezmoi"
    destination = tmp_path / "destination"
    destination.mkdir()

    templates = source / ".chezmoitemplates/ai"
    templates.mkdir(parents=True)
    for template_name in ("authored-plugins", "authored-plugin-manifest"):
        shutil.copy2(AUTHORED_TEMPLATE_ROOT / template_name, templates / template_name)

    wrapper = source / "dot_local/share/plugin.json.tmpl"
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text(
        '{{ includeTemplate "ai/authored-plugin-manifest" (dict "root" . "name" "domain-brain") }}\n',
        encoding="utf-8",
    )

    checkout_plugin = checkout / "src/overlay-plugins/domain-brain"
    assembled_plugin = checkout / ".chezmoiroot.assembled/overlay-plugins/domain-brain"
    checkout_skills = checkout / "src/overlay-skills/records"
    assembled_skills = checkout / ".chezmoiroot.assembled/overlay-skills/records"
    checkout_plugin.mkdir(parents=True)
    assembled_plugin.mkdir(parents=True)
    checkout_skills.mkdir(parents=True)
    assembled_skills.mkdir(parents=True)
    (checkout_plugin / "source.txt").write_text("checkout v1\n", encoding="utf-8")
    (assembled_plugin / "source.txt").write_text("assembled v1\n", encoding="utf-8")
    (checkout_skills / "SKILL.md").write_text("checkout skill\n", encoding="utf-8")
    (assembled_skills / "SKILL.md").write_text("assembled skill\n", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet", str(checkout)], check=True)

    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.plugin_bridge.capabilities.domain-brain]",
                'description = "Domain Intelligence workflows."',
                'source_dir = "src/overlay-plugins/domain-brain"',
                'skills_source_dir = "src/overlay-skills"',
                'hosts = ["claude"]',
                "",
                "[data.ai.plugin_bridge.capabilities.domain-brain.skills]",
                'records = "present"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    def render_version() -> str:
        result = _apply(source, destination, config)
        assert result.returncode == 0, result.stderr
        return json.loads((destination / ".local/share/plugin.json").read_text(encoding="utf-8"))["version"]

    initial_version = render_version()
    (checkout_plugin / "source.txt").write_text("checkout v2\n", encoding="utf-8")
    assert render_version() == initial_version
    (checkout_skills / "SKILL.md").write_text("checkout skill v2\n", encoding="utf-8")
    assert render_version() == initial_version

    (assembled_plugin / "source.txt").write_text("assembled v2\n", encoding="utf-8")
    source_updated_version = render_version()
    assert source_updated_version != initial_version
    (assembled_skills / "SKILL.md").write_text("assembled skill v2\n", encoding="utf-8")
    assert render_version() != source_updated_version
