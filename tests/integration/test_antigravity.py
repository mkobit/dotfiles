import json
import subprocess
from pathlib import Path
from typing import Any

import pytest


@pytest.mark.integration
@pytest.mark.chezmoi_installation("local.bin.agy", methods={"github_releases", "preinstalled"})
def test_antigravity_version(host):
    """Verify that the agy CLI is operational when enabled."""
    result = host.run("agy --version")
    assert result.rc == 0, f"'agy --version' failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"


@pytest.mark.integration
def test_antigravity_settings_deployed(host, chezmoi_dest):
    """Verify ~/.gemini/antigravity-cli/settings.json exists after chezmoi apply."""
    settings_file = host.file(str(chezmoi_dest / ".gemini" / "antigravity-cli" / "settings.json"))
    assert settings_file.exists, "~/.gemini/antigravity-cli/settings.json does not exist"


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def _render_antigravity_settings(
    stdin: str,
    agy_method: str,
    override_data: dict[str, Any] | None = None,
) -> subprocess.CompletedProcess[str]:
    template = Path.cwd() / "src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json"
    data: dict[str, Any] = {"local": {"bin": {"agy": {"installation_method": agy_method}}}}
    if override_data is not None:
        _deep_merge(data, override_data)
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
            json.dumps(data),
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
    assert rendered.get("showFeedbackSurvey") is False
    assert "showFeedbackSurvey" not in rendered.get("general", {})


@pytest.mark.integration
def test_antigravity_vim_mode_settings() -> None:
    result = _render_antigravity_settings("{}", "preinstalled")
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert rendered.get("editorMode") == "vim"
    assert rendered.get("vimInsertFirst") is True


@pytest.mark.integration
def test_antigravity_agent_mode_default() -> None:
    result = _render_antigravity_settings("{}", "preinstalled")
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert rendered.get("agentMode") == "accept-edits"


@pytest.mark.integration
def test_antigravity_permissions_merges_live_and_configured_urls() -> None:
    result = _render_antigravity_settings(
        '{"permissions":{"allow":["read_url(example.com)"]}}',
        "preinstalled",
    )
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    allow = rendered.get("permissions", {}).get("allow", [])
    assert "read_url(example.com)" in allow
    assert "read_url(antigravity.google)" in allow


def _render_antigravity_keybindings(
    stdin: str = "",
    override_data: dict[str, Any] | None = None,
) -> subprocess.CompletedProcess[str]:
    template = Path.cwd() / "src/chezmoi/dot_gemini/antigravity-cli/modify_keybindings.json"
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
        command.extend(["--override-data", json.dumps(override_data)])
    command.append(str(template))
    return subprocess.run(
        command,
        input=stdin,
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


@pytest.mark.integration
def test_antigravity_keybindings_upserts_and_preserves_existing_keys() -> None:
    initial = {
        "edit.yank": ["ctrl+y"],
        "vim.insert.submit": ["alt+s"],
    }
    result = _render_antigravity_keybindings(stdin=json.dumps(initial))
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert rendered["edit.yank"] == ["ctrl+y"]
    assert rendered["vim.insert.insert_newline"] == ["alt+enter", "ctrl+j", "shift+enter"]
    assert rendered["vim.insert.submit"] == ["ctrl+enter", "ctrl+s", "enter"]


@pytest.mark.integration
def test_antigravity_keybindings_preserves_exact_stdin_when_matching() -> None:
    initial = '{\n  "custom.action": ["ctrl+k"],\n  "vim.insert.insert_newline": ["alt+enter", "ctrl+j", "shift+enter"],\n  "vim.insert.submit": ["ctrl+enter", "ctrl+s", "enter"]\n}\n'
    result = _render_antigravity_keybindings(stdin=initial)
    assert result.returncode == 0, result.stderr
    assert result.stdout == initial


@pytest.mark.integration
def test_antigravity_keybindings_matches_regardless_of_shortcut_list_order() -> None:
    initial = '{\n  "vim.insert.insert_newline": ["ctrl+j", "alt+enter", "shift+enter"],\n  "vim.insert.submit": ["enter", "ctrl+s", "ctrl+enter"]\n}\n'
    result = _render_antigravity_keybindings(stdin=initial)
    assert result.returncode == 0, result.stderr
    assert result.stdout == initial


@pytest.mark.integration
def test_antigravity_keybindings_updates_when_chord_modifiers_differ() -> None:
    initial = '{\n  "vim.insert.insert_newline": ["alt+enter", "ctrl+j", "shift+enter"],\n  "vim.insert.submit": ["enter+ctrl", "ctrl+s", "enter"]\n}\n'
    result = _render_antigravity_keybindings(stdin=initial)
    assert result.returncode == 0, result.stderr
    assert result.stdout != initial
    rendered = json.loads(result.stdout)
    assert rendered["vim.insert.submit"] == ["ctrl+enter", "ctrl+s", "enter"]


@pytest.mark.integration
def test_antigravity_keybindings_deletes_key_via_remove_list() -> None:
    initial = json.dumps(
        {
            "to.delete": ["ctrl+d"],
            "vim.insert.insert_newline": ["alt+enter", "ctrl+j", "shift+enter"],
            "vim.insert.submit": ["ctrl+enter", "ctrl+s", "enter"],
        }
    )
    result = _render_antigravity_keybindings(
        stdin=initial,
        override_data={"gemini": {"keybindings_remove": ["to.delete"]}},
    )
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert "to.delete" not in rendered


@pytest.mark.integration
def test_antigravity_keybindings_deletes_key_via_boolean_false() -> None:
    initial = json.dumps(
        {
            "to.delete": ["ctrl+d"],
            "vim.insert.insert_newline": ["alt+enter", "ctrl+j", "shift+enter"],
            "vim.insert.submit": ["ctrl+enter", "ctrl+s", "enter"],
        }
    )
    result = _render_antigravity_keybindings(
        stdin=initial,
        override_data={"gemini": {"keybindings": {"to.delete": False}}},
    )
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert "to.delete" not in rendered


@pytest.mark.integration
def test_antigravity_auto_update_disabled_in_shell_configs() -> None:
    for shell_file in ["dot_dotfiles/bash/config.bash.tmpl", "dot_dotfiles/zsh/config.zsh.tmpl"]:
        template = Path.cwd() / "src/chezmoi" / shell_file
        result = subprocess.run(
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
                str(template),
            ],
            capture_output=True,
            check=False,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "export AGY_CLI_DISABLE_AUTO_UPDATE=true" in result.stdout


@pytest.mark.integration
def test_antigravity_auto_update_enabled_omits_shell_export() -> None:
    for shell_file in ["dot_dotfiles/bash/config.bash.tmpl", "dot_dotfiles/zsh/config.zsh.tmpl"]:
        template = Path.cwd() / "src/chezmoi" / shell_file
        result = subprocess.run(
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
                "--override-data",
                json.dumps({"local": {"bin": {"agy": {"auto_update": True}}}}),
                str(template),
            ],
            capture_output=True,
            check=False,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "export AGY_CLI_DISABLE_AUTO_UPDATE=true" not in result.stdout


@pytest.mark.integration
def test_antigravity_settings_auto_update_gated_by_init_var() -> None:
    default_res = _render_antigravity_settings("{}", "preinstalled")
    assert default_res.returncode == 0, default_res.stderr
    assert json.loads(default_res.stdout)["general"]["enableAutoUpdate"] is False

    enabled_res = _render_antigravity_settings(
        "{}",
        "preinstalled",
        override_data={"local": {"bin": {"agy": {"auto_update": True}}}},
    )
    assert enabled_res.returncode == 0, enabled_res.stderr
    assert json.loads(enabled_res.stdout)["general"]["enableAutoUpdate"] is True
