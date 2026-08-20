import pytest


@pytest.mark.integration
def test_codex_config_toml_deployed(host, chezmoi_dest):
    """Verify ~/.codex/config.toml exists after chezmoi apply."""
    config_file = host.file(str(chezmoi_dest / ".codex" / "config.toml"))
    assert config_file.exists, "~/.codex/config.toml does not exist"


@pytest.mark.integration
def test_codex_config_toml_is_valid(host, chezmoi_dest):
    """Verify ~/.codex/config.toml parses as TOML."""
    config_path = chezmoi_dest / ".codex" / "config.toml"
    result = host.run(
        f'python3 -c "import pathlib, tomllib; tomllib.loads(pathlib.Path({str(config_path)!r}).read_text())"'
    )
    assert result.rc == 0, f"~/.codex/config.toml is invalid TOML.\nstderr: {result.stderr}"


@pytest.mark.integration
@pytest.mark.chezmoi_installation("local.bin.codex", methods={"github_releases"})
def test_codex_version(host):
    """Verify codex --version runs successfully on supported platforms."""
    result = host.run("codex --version")
    assert result.rc == 0, f"'codex --version' failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"
