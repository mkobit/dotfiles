import subprocess
import tomllib
from pathlib import Path


def _render_codex_config(template: Path, stdin: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "chezmoi",
            "--source",
            str(Path.cwd()),
            "execute-template",
            "-f",
            "--with-stdin",
            str(template),
        ],
        input=stdin,
        capture_output=True,
        check=False,
        text=True,
    )


def test_codex_tui_modifier_preserves_matching_toml() -> None:
    template = Path.cwd() / "src/chezmoi/dot_codex/modify_private_config.toml"
    matching = """[tui]
vim_mode_default = true
status_line = ["model-with-reasoning", "current-dir", "project-name", "git-branch", "run-state", "permissions", "context-remaining", "workspace-headline", "task-progress"]
status_line_use_colors = true

[runtime]
value = "preserve"
"""

    result = _render_codex_config(template, matching)

    assert result.returncode == 0, result.stderr
    assert result.stdout == matching
    assert result.stderr == ""


def test_codex_tui_modifier_reconciles_only_tui_preferences() -> None:
    template = Path.cwd() / "src/chezmoi/dot_codex/modify_private_config.toml"
    changed = """[tui]
vim_mode_default = false
status_line = ["current-dir"]
status_line_use_colors = false

[runtime]
value = "preserve"
"""

    result = _render_codex_config(template, changed)

    assert result.returncode == 0, result.stderr
    rendered = tomllib.loads(result.stdout)
    assert rendered["tui"] == {
        "vim_mode_default": True,
        "status_line": [
            "model-with-reasoning",
            "current-dir",
            "project-name",
            "git-branch",
            "run-state",
            "permissions",
            "context-remaining",
            "workspace-headline",
            "task-progress",
        ],
        "status_line_use_colors": True,
    }
    assert rendered["runtime"] == {"value": "preserve"}
    assert "Codex TUI settings changed" in result.stderr
