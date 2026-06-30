import pytest

BETTERLEAKS_BIN = ".local/bin/betterleaks"
CONFIG_REL = ".config/betterleaks/betterleaks.toml"
HOOK_REL = ".dotfiles/git/hooks/pre-commit"

# Format-valid but fake GitHub PAT — betterleaks' default ruleset flags it.
# The trailing allow comment keeps this fixture from tripping our own pre-commit hook.
FAKE_SECRET = "ghp_0123456789abcdefghijABCDEFGHIJ012345"  # gitleaks:allow betterleaks:allow


@pytest.mark.integration
def test_betterleaks_installed(host, chezmoi_dest):
    """The betterleaks scanner binary is deployed and runnable."""
    binary = chezmoi_dest / BETTERLEAKS_BIN
    assert host.file(str(binary)).exists, "betterleaks binary not deployed"
    result = host.run(f'"{binary}" version')
    assert result.rc == 0, f"betterleaks not runnable.\nstderr: {result.stderr}"


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
def test_scan_blocks_staged_secret(host, chezmoi_dest):
    """A staged secret is flagged by betterleaks using the managed config (non-zero exit)."""
    result = host.run(_staged_scan(chezmoi_dest, FAKE_SECRET))
    assert result.rc != 0, f"expected the staged secret to be flagged.\nstdout: {result.stdout}"


@pytest.mark.integration
def test_scan_passes_clean_content(host, chezmoi_dest):
    """Clean staged content passes the scan (zero exit)."""
    result = host.run(_staged_scan(chezmoi_dest, "just a normal line of config"))
    assert result.rc == 0, f"clean content should pass.\nstdout: {result.stdout}\nstderr: {result.stderr}"


def _staged_scan(chezmoi_dest, content):
    """Shell snippet: stage `content` in a throwaway repo and scan it with the managed config."""
    binary = chezmoi_dest / BETTERLEAKS_BIN
    config = chezmoi_dest / CONFIG_REL
    return (
        'd=$(mktemp -d); cd "$d" || exit 99; '
        "git init -q; git config user.email t@e.st; git config user.name test; "
        f"printf %s '{content}' > sample.txt; git add sample.txt; "
        f'"{binary}" git --staged --no-banner --redact -c "{config}"; '
        'rc=$?; cd /; rm -rf "$d"; exit $rc'
    )
