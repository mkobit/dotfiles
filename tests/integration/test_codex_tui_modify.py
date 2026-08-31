import subprocess
import tomllib
from pathlib import Path


def _render_codex_config(
    template: Path,
    stdin: str,
    override_data: str | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [
        "chezmoi",
        "--config",
        "/dev/null",
        "--config-format",
        "toml",
        "--source",
        str(Path.cwd()),
        "execute-template",
        "-f",
        "--with-stdin",
    ]
    if override_data is not None:
        command.extend(["--override-data", override_data])
    command.append(str(template))
    return subprocess.run(
        command,
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
    assert "Codex managed settings changed" in result.stderr


def test_codex_tui_modifier_adds_managed_defaults_to_base_only_config() -> None:
    template = Path.cwd() / "src/chezmoi/dot_codex/modify_private_config.toml"
    base_only = "# preserve this comment\n[runtime]\nvalue='preserve'\n"

    result = _render_codex_config(template, base_only)

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
    assert "Codex managed settings changed" in result.stderr


def test_codex_modifier_adds_optional_auto_compaction_limit() -> None:
    template = Path.cwd() / "src/chezmoi/dot_codex/modify_private_config.toml"
    existing = """[runtime]\nvalue = \"preserve\"\n"""
    result = _render_codex_config(
        template,
        existing,
        '{"ai":{"context_management":{"codex":{"auto_compact_token_limit":176700}}}}',
    )
    assert result.returncode == 0, result.stderr
    rendered = tomllib.loads(result.stdout)
    assert rendered["model_auto_compact_token_limit"] == 176700
    assert rendered["runtime"] == {"value": "preserve"}
    assert rendered["tui"]["vim_mode_default"] is True


def test_codex_modifier_preserves_exactly_matching_optional_limit_byte_for_byte() -> None:
    template = Path.cwd() / "src/chezmoi/dot_codex/modify_private_config.toml"
    existing = """# preserve this comment
model_auto_compact_token_limit = 176700

[tui]
vim_mode_default = true
status_line = ["model-with-reasoning", "current-dir", "project-name", "git-branch", "run-state", "permissions", "context-remaining", "workspace-headline", "task-progress"]
status_line_use_colors = true

[runtime]
value='preserve'
"""

    result = _render_codex_config(
        template,
        existing,
        '{"ai":{"context_management":{"codex":{"auto_compact_token_limit":176700}}}}',
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == existing
    assert result.stderr == ""


def test_codex_modifier_replaces_stale_optional_limit_and_preserves_unrelated_settings() -> None:
    template = Path.cwd() / "src/chezmoi/dot_codex/modify_private_config.toml"
    existing = """model_auto_compact_token_limit = 100000

[tui]
vim_mode_default = true
status_line = ["model-with-reasoning", "current-dir", "project-name", "git-branch", "run-state", "permissions", "context-remaining", "workspace-headline", "task-progress"]
status_line_use_colors = true

[runtime]
value = "preserve"
"""

    result = _render_codex_config(
        template,
        existing,
        '{"ai":{"context_management":{"codex":{"auto_compact_token_limit":176700}}}}',
    )

    assert result.returncode == 0, result.stderr
    rendered = tomllib.loads(result.stdout)
    assert rendered["model_auto_compact_token_limit"] == 176700
    assert "model_auto_compact_token_limit" not in rendered["tui"]
    assert rendered["runtime"] == {"value": "preserve"}
    assert "Codex managed settings changed" in result.stderr


def test_codex_modifier_manages_preferences_in_explicit_empty_tui_table() -> None:
    template = Path.cwd() / "src/chezmoi/dot_codex/modify_private_config.toml"
    existing = '[tui]\n\n[runtime]\nvalue = "preserve"\n'

    result = _render_codex_config(template, existing)

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
