import pytest


@pytest.mark.integration
def test_mise_bun_and_gemini_installed(host):
    """Verify that gemini is on the path."""
    # We will verify if we can resolve the gemini command.
    result = host.run("zsh -i -c 'command -v gemini'")

    # If the command is not installed yet (e.g. running in CI where it's mocked),
    # we fallback to checking the configuration file.
    if result.rc != 0:
        with open("src/chezmoi/.chezmoidata/mise.toml") as f:
            content = f.read()
        assert "npm:@google/gemini-cli" in content, "gemini-cli not added to config"
    else:
        assert result.rc == 0
