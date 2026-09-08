import json
import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.chezmoi_installation("agy", methods={"dotfiles.script", "preinstalled"})
def test_antigravity_version(host):
    """Verify that the agy CLI is operational when enabled."""
    result = host.run("agy --version")
    assert result.rc == 0, f"'agy --version' failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"


@pytest.mark.integration
def test_antigravity_settings_deployed(host, chezmoi_dest):
    """Verify ~/.gemini/antigravity-cli/settings.json exists after chezmoi apply."""
    settings_file = host.file(str(chezmoi_dest / ".gemini" / "antigravity-cli" / "settings.json"))
    assert settings_file.exists, "~/.gemini/antigravity-cli/settings.json does not exist"


def _render_antigravity_settings(stdin: str, agy_method: str) -> subprocess.CompletedProcess[str]:
    template = Path.cwd() / "src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json"
    return subprocess.run(
        [
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
            "--override-data",
            json.dumps({"agy": {"installation_method": agy_method}}),
            str(template),
        ],
        input=stdin,
        capture_output=True,
        check=False,
        text=True,
    )


@pytest.mark.integration
def test_antigravity_statusline_template_is_configured() -> None:
    result = _render_antigravity_settings(
        '{"title":"stale","statusLine":{"type":"command","command":"stale","enabled":false}}',
        "preinstalled",
    )
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert rendered["statusLine"] == {
        "type": "command",
        "command": "statusline antigravity render",
        "enabled": True,
    }
    assert "title" not in rendered


@pytest.mark.integration
def test_antigravity_statusline_template_removes_stale_settings_when_disabled() -> None:
    result = _render_antigravity_settings(
        '{"title":"stale","statusLine":{"type":"command","command":"stale","enabled":false}}',
        "none",
    )
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert "statusLine" not in rendered
    assert "title" not in rendered


@pytest.mark.integration
def test_legacy_gemini_settings_removed(host, chezmoi_dest):
    """Verify ~/.gemini/settings.json does not exist after chezmoi apply."""
    legacy_file = host.file(str(chezmoi_dest / ".gemini" / "settings.json"))
    assert not legacy_file.exists, "~/.gemini/settings.json still exists"


@pytest.mark.integration
def test_antigravity_show_feedback_survey_disabled() -> None:
    result = _render_antigravity_settings("{}", "preinstalled")
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert rendered.get("general", {}).get("showFeedbackSurvey") is False


@pytest.mark.integration
def test_antigravity_vim_mode_settings() -> None:
    result = _render_antigravity_settings("{}", "preinstalled")
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert rendered.get("editorMode") == "vim"
    assert rendered.get("vimInsertFirst") is True


def _render_antigravity_keybindings(
    override_data: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    template = Path.cwd() / "src/chezmoi/dot_gemini/antigravity-cli/keybindings.json.tmpl"
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
    ]
    if override_data is not None:
        command.extend(["--override-data", json.dumps(override_data)])
    command.append(str(template))
    return subprocess.run(
        command,
        capture_output=True,
        check=False,
        text=True,
    )


@pytest.mark.integration
def test_antigravity_keybindings_renders_configured_mappings() -> None:
    result = _render_antigravity_keybindings()
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert rendered["vim.insert.insert_newline"] == ["alt+enter", "ctrl+j", "shift+enter"]
    assert rendered["vim.insert.submit"] == ["ctrl+enter", "ctrl+s", "enter"]


@pytest.mark.integration
def test_antigravity_keybindings_empty_when_no_keybindings_configured() -> None:
    result = _render_antigravity_keybindings(override_data={"gemini": {"keybindings": None}})
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
