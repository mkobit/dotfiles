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
    result = _render_antigravity_settings('{"title":"stale"}', "preinstalled")
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert rendered["statusLine"] == {
        "type": "command",
        "command": "statusline antigravity render",
        "enabled": True,
    }
    assert "title" not in rendered


@pytest.mark.integration
def test_antigravity_statusline_template_has_no_statusline_when_disabled() -> None:
    result = _render_antigravity_settings("{}", "none")
    assert result.returncode == 0, result.stderr
    rendered = json.loads(result.stdout)
    assert "statusLine" not in rendered


@pytest.mark.integration
def test_legacy_gemini_settings_removed(host, chezmoi_dest):
    """Verify ~/.gemini/settings.json does not exist after chezmoi apply."""
    legacy_file = host.file(str(chezmoi_dest / ".gemini" / "settings.json"))
    assert not legacy_file.exists, "~/.gemini/settings.json still exists"
