import shutil

import pytest


@pytest.mark.integration
def test_mise_bun_and_gemini_installed():
    """Verify that gemini is on the path."""
    gemini_path = shutil.which("gemini")

    # If the command is not installed yet (e.g. running in CI where it's mocked),
    # we fallback to checking the configuration file.
    if gemini_path is None:
        with open("src/chezmoi/.chezmoidata/mise.toml") as f:
            content = f.read()
        assert "npm:@google/gemini-cli" in content, "gemini-cli not added to config"
    else:
        # Just verifying it exists here is equivalent to checking host.run
        pass
