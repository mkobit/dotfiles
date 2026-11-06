from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from skill_filter import agent_source_cleanup

MARKET = ".local/share/agent-plugins/marketplace/plugins"
BUNDLE = f"{MARKET}/mkobit-dotfiles"
STATE = ".local/state/dotfiles/agent-source-roots.json"
LEGACY = ".local/state/dotfiles/agent-plugin-capability-ownership.json"


def _touch(destination: Path, relative: str, text: str = "x") -> Path:
    path = destination / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _write_state(destination: Path, roots: list[str]) -> None:
    _touch(destination, STATE, json.dumps({"version": 1, "roots": roots}))


def _run(
    destination: Path,
    desired: list[str],
    protected: list[str] | None = None,
    *,
    legacy: bool = False,
):
    command = [
        sys.executable,
        "-S",
        agent_source_cleanup.__file__,
        "--destination",
        str(destination),
        "--state",
        str(destination / STATE),
    ]
    if legacy:
        command += ["--legacy-state", str(destination / LEGACY)]
    return subprocess.run(
        command,
        input=json.dumps({"desired": desired, "protected": protected or []}),
        capture_output=True,
        text=True,
        check=False,
    )


def _state(destination: Path) -> list[str]:
    return json.loads((destination / STATE).read_text())["roots"]


def test_removes_previous_roots_not_desired(tmp_path):
    _touch(tmp_path, f"{MARKET}/gone/claude/skills/a/SKILL.md")
    _touch(tmp_path, f"{MARKET}/kept/claude/skills/a/SKILL.md")
    _touch(tmp_path, ".gemini/antigravity-cli/skills/old/SKILL.md")
    _write_state(
        tmp_path,
        [f"{MARKET}/gone", f"{MARKET}/kept", ".gemini/antigravity-cli/skills/old"],
    )

    result = _run(tmp_path, [f"{MARKET}/kept"])

    assert result.returncode == 0, result.stderr
    assert not (tmp_path / MARKET / "gone").exists()
    assert not (tmp_path / ".gemini/antigravity-cli/skills/old").exists()
    assert (tmp_path / MARKET / "kept/claude/skills/a/SKILL.md").is_file()
    assert _state(tmp_path) == [f"{MARKET}/kept"]


def test_keeps_desired_child_inside_removed_parent(tmp_path):
    _touch(tmp_path, f"{MARKET}/p/codex/skills/keep/SKILL.md")
    _touch(tmp_path, f"{MARKET}/p/codex/skills/drop/SKILL.md")
    _touch(tmp_path, f"{MARKET}/p/claude/skills/a/SKILL.md")
    _touch(tmp_path, f"{MARKET}/p/README")
    _write_state(tmp_path, [f"{MARKET}/p"])

    result = _run(tmp_path, [f"{MARKET}/p/codex/skills/keep"])

    assert result.returncode == 0, result.stderr
    assert (tmp_path / MARKET / "p/codex/skills/keep/SKILL.md").is_file()
    assert not (tmp_path / MARKET / "p/codex/skills/drop").exists()
    assert not (tmp_path / MARKET / "p/claude").exists()
    assert not (tmp_path / MARKET / "p/README").exists()


def test_preserves_unowned_siblings_in_shared_skill_dirs(tmp_path):
    _touch(tmp_path, f"{BUNDLE}/claude/skills/mine/SKILL.md")
    _touch(tmp_path, f"{BUNDLE}/claude/skills/upstream/SKILL.md")
    _touch(tmp_path, f"{BUNDLE}/claude/other.txt")
    _write_state(tmp_path, [f"{BUNDLE}/claude/skills/mine"])

    result = _run(tmp_path, [])

    assert result.returncode == 0, result.stderr
    assert not (tmp_path / BUNDLE / "claude/skills/mine").exists()
    assert (tmp_path / BUNDLE / "claude/skills/upstream/SKILL.md").is_file()
    assert (tmp_path / BUNDLE / "claude/other.txt").is_file()


def test_protected_external_roots_are_never_removed(tmp_path):
    external = f"{BUNDLE}/claude/skills/ext"
    _touch(tmp_path, f"{external}/SKILL.md")
    _write_state(tmp_path, [external])

    result = _run(tmp_path, [], [external])

    assert result.returncode == 0, result.stderr
    assert (tmp_path / external / "SKILL.md").is_file()
    assert _state(tmp_path) == []


@pytest.mark.parametrize(
    "root",
    [
        MARKET,
        f"{MARKET}/mkobit-dotfiles",
        f"{BUNDLE}/claude",
        f"{BUNDLE}/claude/skills",
        f"{MARKET}/p/claude/skills",
        ".claude/skills/x",
        ".gemini/antigravity-cli/skills",
        ".cursor/plugins/local/mkobit-dotfiles",
        ".cursor/plugins/local",
        f"{MARKET}/p/../../x",
        "/etc",
    ],
)
def test_rejects_roots_outside_allowed_patterns(tmp_path, root):
    _touch(tmp_path, f"{MARKET}/p/claude/skills/a/SKILL.md")
    _write_state(tmp_path, [f"{MARKET}/p"])

    from_input = _run(tmp_path, [root])
    assert from_input.returncode == 1
    _write_state(tmp_path, [f"{MARKET}/p", root])
    from_state = _run(tmp_path, [])
    assert from_state.returncode == 1
    assert (tmp_path / MARKET / "p/claude/skills/a/SKILL.md").is_file()


def test_refuses_symlinked_components_without_deleting_outside(tmp_path):
    outside = tmp_path / "outside"
    _touch(outside, "p/SKILL.md", "keep")
    destination = tmp_path / "dest"
    (destination / MARKET).parent.mkdir(parents=True)
    (destination / MARKET).symlink_to(outside, target_is_directory=True)
    _write_state(destination, [f"{MARKET}/p"])

    result = _run(destination, [])

    assert result.returncode == 1
    assert "symlink" in result.stderr
    assert (outside / "p/SKILL.md").read_text() == "keep"

    (destination / MARKET).unlink()
    (destination / MARKET).mkdir()
    (destination / MARKET / "p").symlink_to(outside / "p", target_is_directory=True)
    result = _run(destination, [])
    assert result.returncode == 1
    assert (outside / "p/SKILL.md").read_text() == "keep"


def test_state_unchanged_on_failure_and_retry_succeeds(tmp_path):
    first = f"{MARKET}/a"
    second = f"{MARKET}/b"
    _touch(tmp_path, f"{first}/SKILL.md")
    locked = _touch(tmp_path, f"{second}/sub/SKILL.md")
    _write_state(tmp_path, [first, second])
    before = (tmp_path / STATE).read_text()
    locked.parent.chmod(0o500)
    try:
        if os.access(str(locked.parent), os.W_OK):
            pytest.skip("directory permissions are not enforced for this user")
        failed = _run(tmp_path, [])
        assert failed.returncode == 1
        assert (tmp_path / STATE).read_text() == before
    finally:
        locked.parent.chmod(0o700)

    retried = _run(tmp_path, [])

    assert retried.returncode == 0, retried.stderr
    assert not (tmp_path / first).exists()
    assert not (tmp_path / second).exists()
    assert _state(tmp_path) == []


def test_migrates_legacy_capability_file_state_to_roots(tmp_path):
    paths = [
        f"{MARKET}/gone/codex/skills/s/SKILL.md",
        f"{MARKET}/gone/codex/.codex-plugin/plugin.json",
        f"{MARKET}/live/claude/.mcp.json",
        f"{MARKET}/live/claude/skills/old/SKILL.md",
        f"{BUNDLE}/claude/.claude-plugin/plugin.json",
        f"{BUNDLE}/cursor/skills/bare/SKILL.md",
        ".cursor/plugins/local/gone/rules/r.mdc",
        ".cursor/plugins/local/mkobit-dotfiles/.cursor-plugin/plugin.json",
    ]
    _touch(tmp_path, LEGACY, json.dumps({"version": 1, "paths": paths}))
    for path in paths:
        _touch(tmp_path, path)
    _touch(tmp_path, f"{MARKET}/gone/codex/user.txt")

    result = _run(tmp_path, [f"{MARKET}/live", f"{MARKET}/live/claude"], legacy=True)

    assert result.returncode == 0, result.stderr
    assert not (tmp_path / LEGACY).exists()
    assert not (tmp_path / MARKET / "gone/codex").exists()
    assert not (tmp_path / ".cursor/plugins/local/gone").exists()
    assert not (tmp_path / BUNDLE / "cursor/skills/bare").exists()
    assert not (tmp_path / MARKET / "live/claude/skills/old").exists()
    # Desired roots, bundle manifests, and natively managed files survive.
    assert (tmp_path / MARKET / "live/claude/.mcp.json").is_file()
    assert (tmp_path / BUNDLE / "claude/.claude-plugin/plugin.json").is_file()
    assert (
        tmp_path / ".cursor/plugins/local/mkobit-dotfiles/.cursor-plugin/plugin.json"
    ).is_file()
    assert _state(tmp_path) == [f"{MARKET}/live", f"{MARKET}/live/claude"]


def test_legacy_native_plugin_file_survives_while_plugin_is_desired(tmp_path):
    native = f"{MARKET}/live/codex/.codex-plugin/plugin.json"
    _touch(tmp_path, LEGACY, json.dumps({"version": 1, "paths": [native]}))
    _touch(tmp_path, native)

    result = _run(tmp_path, [f"{MARKET}/live", f"{MARKET}/live/codex"], legacy=True)

    assert result.returncode == 0, result.stderr
    assert (tmp_path / native).is_file()
    assert not (tmp_path / LEGACY).exists()


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        "[]",
        json.dumps({"version": 2, "roots": []}),
        json.dumps({"version": 1, "roots": "x"}),
        json.dumps({"version": 1, "roots": [], "extra": 1}),
        json.dumps({"version": 1, "roots": [3]}),
    ],
)
def test_rejects_malformed_state(tmp_path, content):
    _touch(tmp_path, f"{MARKET}/p/SKILL.md")
    _touch(tmp_path, STATE, content)

    result = _run(tmp_path, [])

    assert result.returncode == 1
    assert (tmp_path / STATE).read_text() == content
    assert (tmp_path / MARKET / "p/SKILL.md").is_file()
