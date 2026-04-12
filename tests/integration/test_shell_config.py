import subprocess
import pytest

@pytest.mark.asyncio
async def test_zsh_config_syntax():
    """Ensure compiled config.zsh evaluates correctly without syntax errors."""
    try:
        # Template the zsh config
        result = subprocess.run(
            ["chezmoi", "--source", "src/chezmoi", "execute-template"],
            input=open("src/chezmoi/dot_dotfiles/zsh/config.zsh.tmpl", "rb").read(),
            capture_output=True,
            check=True
        )

        # Write to a temporary file
        with open("/tmp/config.zsh", "wb") as f:
            f.write(result.stdout)

        # Verify syntax with zsh -n
        subprocess.run(["zsh", "-n", "/tmp/config.zsh"], check=True)
    except FileNotFoundError:
        pytest.skip("zsh not installed")


@pytest.mark.asyncio
async def test_bash_config_syntax():
    """Ensure compiled config.bash evaluates correctly without syntax errors."""
    # Template the bash config
    result = subprocess.run(
        ["chezmoi", "--source", "src/chezmoi", "execute-template"],
        input=open("src/chezmoi/dot_dotfiles/bash/config.bash.tmpl", "rb").read(),
        capture_output=True,
        check=True
    )

    # Write to a temporary file
    with open("/tmp/config.bash", "wb") as f:
        f.write(result.stdout)

    # Verify syntax with bash -n
    subprocess.run(["bash", "-n", "/tmp/config.bash"], check=True)
