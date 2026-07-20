import re

import pytest


def test_repo_mise_toml_stays_locked(repo_root):
    """locked = true keeps uv pinned to the committed mise.lock."""
    content = (repo_root / "mise.toml").read_text()
    assert re.search(r"^locked\s*=\s*true", content, re.MULTILINE)


def test_convergence_script_has_no_lock_bypass(chezmoiscript_path):
    """A run_onchange script that installs from the repo-tracked mise.toml must never
    disable locked-mode enforcement; see dot_config/mise/AGENTS.md."""
    content = chezmoiscript_path.read_text()
    if ".chezmoi.workingTree" not in content or "mise.toml" not in content:
        pytest.skip(f"{chezmoiscript_path.name} does not install from the repo-tracked mise.toml")
    assert not re.search(r"MISE_LOCKED=0|--no-locked", content)


def test_workflow_uv_sync_always_frozen(workflow_path):
    """Every uv sync in a workflow must pin to the committed uv.lock."""
    content = workflow_path.read_text()
    offending = [
        line for line in content.splitlines() if "uv sync" in line and "--frozen" not in line and "--locked" not in line
    ]
    assert not offending
