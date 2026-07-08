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


@pytest.mark.integration
def test_legacy_gemini_settings_removed(host, chezmoi_dest):
    """Verify ~/.gemini/settings.json does not exist after chezmoi apply."""
    legacy_file = host.file(str(chezmoi_dest / ".gemini" / "settings.json"))
    assert not legacy_file.exists, "~/.gemini/settings.json still exists"
