import subprocess

import pytest

BETTERLEAKS_BIN = ".local/bin/betterleaks"
CONFIG_REL = ".config/betterleaks/betterleaks.toml"
HOOK_REL = ".dotfiles/git/hooks/pre-commit"

# Format-valid but fake GitHub PAT — betterleaks' default ruleset flags it.
# The trailing allow comment keeps this fixture from tripping our own hook.
FAKE_SECRET = "ghp_0123456789abcdefghijABCDEFGHIJ012345"  # gitleaks:allow betterleaks:allow


@pytest.fixture()
def scan_staged(tmp_path, chezmoi_dest):
    """Stage content in a throwaway git repo and scan it with the managed config.

    Yields a callable: scan_staged(content) -> betterleaks exit code
    (0 = clean, non-zero = leak found).
    """
    binary = str(chezmoi_dest / BETTERLEAKS_BIN)
    config = str(chezmoi_dest / CONFIG_REL)
    git = ("git", "-C", str(tmp_path))
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "config", "user.email", "test@example.com"], check=True)
    subprocess.run([*git, "config", "user.name", "test"], check=True)

    def _scan(content):
        (tmp_path / "sample.txt").write_text(content)
        subprocess.run([*git, "add", "sample.txt"], check=True)
        return subprocess.run(
            [binary, "git", "--staged", "--no-banner", "--redact", "-c", config],
            cwd=tmp_path,
            check=False,
        ).returncode

    return _scan


@pytest.mark.integration
def test_betterleaks_installed(host, chezmoi_dest):
    """The betterleaks scanner binary is deployed and runnable."""
    binary = chezmoi_dest / BETTERLEAKS_BIN
    assert host.file(str(binary)).exists, "betterleaks binary not deployed"
    assert host.run(f'"{binary}" version').rc == 0


@pytest.mark.integration
def test_global_config_deployed_and_valid(host, chezmoi_dest):
    """The chezmoi-managed global config exists and passes `betterleaks config check`."""
    binary = chezmoi_dest / BETTERLEAKS_BIN
    config = chezmoi_dest / CONFIG_REL
    assert host.file(str(config)).exists, f"{config} is missing"
    result = host.run(f'"{binary}" config check -c "{config}"')
    assert result.rc == 0, f"config did not validate.\nstdout: {result.stdout}\nstderr: {result.stderr}"


@pytest.mark.integration
def test_pre_commit_hook_deployed_and_executable(host, chezmoi_dest):
    """The pre-commit hook is deployed and executable."""
    hook = host.file(str(chezmoi_dest / HOOK_REL))
    assert hook.exists, "pre-commit hook is missing"
    assert hook.mode & 0o111, "pre-commit hook is not executable"


@pytest.mark.integration
def test_scan_blocks_staged_secret(scan_staged):
    """A staged secret is flagged by betterleaks (non-zero exit)."""
    assert scan_staged(f'token = "{FAKE_SECRET}"\n') != 0


@pytest.mark.integration
def test_scan_passes_clean_content(scan_staged):
    """Clean staged content passes the scan (zero exit)."""
    assert scan_staged("just a normal line of config\n") == 0
