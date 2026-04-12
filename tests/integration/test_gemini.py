import pytest


@pytest.mark.integration
def test_gemini_cli_available(host):
    """Verify that gemini CLI is available and executable in the shell environment."""
    result = host.run("zsh -i -c 'command -v gemini'")

    assert result.rc == 0, (
        f"gemini command not found in zsh environment.\n"
        f"stderr: {result.stderr}\nstdout: {result.stdout}"
    )
    assert "gemini" in result.stdout, (
        f"command -v gemini did not print a path containing 'gemini'.\n"
        f"stdout: {result.stdout}"
    )
