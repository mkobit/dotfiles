import pytest


@pytest.mark.integration
def test_claude_version(host):
    """Verify that the claude CLI is accessible and operational."""
    result = host.run("claude --version")
    assert result.rc == 0, f"claude --version failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"


@pytest.mark.integration
def test_claude_settings_json_deployed(host, chezmoi_dest):
    """Verify ~/.claude/settings.json exists after chezmoi apply."""
    settings_file = host.file(str(chezmoi_dest / ".claude" / "settings.json"))
    assert settings_file.exists, "~/.claude/settings.json does not exist"
