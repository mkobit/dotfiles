"""Check SBX plugin packaging without custom command approval hooks."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "src/ai/skills/sbx-sandboxes"
BUNDLE = Path("src/chezmoi/dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles")
MANIFESTS = {"codex": BUNDLE / "codex/dot_codex-plugin/plugin.json.tmpl", "antigravity": BUNDLE / "plugin.json.tmpl"}


def _render(path: Path, state: str, source: Path = ROOT) -> dict:
    result = subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(source),
            "execute-template",
            "--override-data",
            json.dumps({"ai": {"skills": {"authored": {"sbx-sandboxes": state}}}}),
            "-f",
            str(source / path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("host", MANIFESTS)
def test_skill_changes_plugin_version(host: str, tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(ROOT / "src/chezmoi/.chezmoidata", source / "src/chezmoi/.chezmoidata")
    (source / ".chezmoiroot").write_text("src/chezmoi\n")
    manifest = MANIFESTS[host]
    target = source / manifest
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / manifest, target)
    skill = source / "src/ai/skills/sbx-sandboxes/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# SBX sandboxes\n")
    before = _render(manifest, "present", source)["version"]
    skill.write_text("# SBX sandboxes\nUpdated skill.\n")
    assert _render(manifest, "present", source)["version"] != before


def test_retired_hook_files_are_removed_on_apply(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    shutil.copy2(ROOT / BUNDLE / ".chezmoiremove.tmpl", source / ".chezmoiremove.tmpl")
    destination = tmp_path / "destination"
    destination.mkdir()
    paths = ("hooks.json", "codex/hooks/hooks.json")
    for path in paths:
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('{"hooks":{}}\n')
    sibling = destination / "notes.json"
    sibling.write_text('{"keep":true}\n')
    config = tmp_path / "chezmoi.toml"
    config.write_text("")
    result = subprocess.run(
        [
            "chezmoi",
            "--config",
            str(config),
            "--config-format",
            "toml",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--override-data",
            json.dumps({"ai": {}}),
            "apply",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert all(not (destination / path).exists() for path in paths)
    assert sibling.read_text() == '{"keep":true}\n'


@pytest.mark.skipif(shutil.which("agy") is None, reason="AGY is not installed")
def test_portable_plugin_passes_native_agy_validation(tmp_path: Path) -> None:
    manifest = _render(BUNDLE / "plugin.json.tmpl", "present")
    (tmp_path / "plugin.json").write_text(json.dumps(manifest))
    shutil.copytree(SKILL, tmp_path / "skills/sbx-sandboxes")
    result = subprocess.run(
        ["agy", "plugin", "validate", str(tmp_path), "--json"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["components"]["hooks"] == 0
    assert report["components"]["skills"] == 1
