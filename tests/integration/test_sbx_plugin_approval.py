"""Check SBX plugin packaging without custom command approval hooks."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles"
SKILL = BUNDLE / "exact_skills/exact_sbx-sandboxes"


def _render(path: Path) -> dict:
    result = subprocess.run(
        [
            *("chezmoi", "--config", "/dev/null", "--config-format", "toml", "--source", str(ROOT)),
            *("execute-template", "--file", str(path)),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.skipif(shutil.which("agy") is None, reason="AGY is not installed")
def test_portable_plugin_passes_native_agy_validation(tmp_path: Path) -> None:
    (tmp_path / "plugin.json").write_text(json.dumps(_render(BUNDLE / "plugin.json.tmpl")))
    # The source folders carry exact_; the deployed skill tree does not.
    skill = tmp_path / "skills/sbx-sandboxes"
    for path in SKILL.rglob("*"):
        if path.is_file():
            target = skill / Path(*(part.removeprefix("exact_") for part in path.relative_to(SKILL).parts))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    result = subprocess.run(
        ["agy", "plugin", "validate", str(tmp_path), "--json"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["components"]["hooks"] == 0
    assert report["components"]["skills"] == 1
