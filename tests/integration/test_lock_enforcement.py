import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_TOOLS_SCRIPT = (
    REPO_ROOT
    / "src/chezmoi/.chezmoiscripts"
    / "run_onchange_after_07_trust-install-repo-mise-tools.sh.tmpl"
)


def test_repo_mise_toml_stays_locked():
    """locked = true keeps uv pinned to the committed mise.lock."""
    content = (REPO_ROOT / "mise.toml").read_text()
    assert re.search(r"^locked\s*=\s*true", content, re.MULTILINE)


def test_repo_tools_script_has_no_lock_bypass():
    """Script 07 must never disable locked-mode enforcement; see dot_config/mise/AGENTS.md."""
    content = REPO_TOOLS_SCRIPT.read_text()
    assert not re.search(r"MISE_LOCKED=0|--no-locked", content)


def test_ci_uv_sync_always_frozen():
    """Every uv sync in ci.yml must pin to the committed uv.lock."""
    content = (REPO_ROOT / ".github/workflows/ci.yml").read_text()
    offending = [
        line
        for line in content.splitlines()
        if "uv sync" in line and "--frozen" not in line and "--locked" not in line
    ]
    assert not offending
