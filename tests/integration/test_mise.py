import pytest


@pytest.mark.integration
def test_mise_bun_and_gemini_installed():
    """Verify that mise is configured to use bun and gemini-cli is installed."""
    with open("src/chezmoi/.chezmoidata/mise.toml") as f:
        content = f.read()

    assert 'npm_package_manager = "bun"' in content, "npm_package_manager not bun"
    assert 'version = "0.37.1"' in content, "gemini-cli version not pinned to 0.37.1"
    assert "npm:@google/gemini-cli" in content, "gemini-cli not added"
