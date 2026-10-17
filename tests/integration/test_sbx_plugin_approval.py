"""Check packaged SBX approval hooks without running an agent or SBX."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "src/ai/skills/sbx-sandboxes"
BUNDLE = Path("src/chezmoi/dot_local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles")
HOOKS = {"codex": BUNDLE / "codex/hooks/hooks.json.tmpl", "antigravity": BUNDLE / "hooks.json.tmpl"}
APPROVAL = {"hookSpecificOutput": {"hookEventName": "PermissionRequest", "decision": {"behavior": "allow"}}}


def _call(host: str, command: str, script: Path | None = None) -> dict:
    payload = (
        {"hook_event_name": "PermissionRequest", "tool_name": "Bash", "tool_input": {"command": command}}
        if host == "codex"
        else {"toolCall": {"name": "run_command", "args": {"CommandLine": command}}}
    )
    return _run(host, json.dumps(payload), script)


def _run(host: str, payload: str, script: Path | None = None) -> dict:
    result = subprocess.run(
        [sys.executable, str(script or SKILL / "scripts/command_approval.py"), host],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    return json.loads(result.stdout)


@pytest.mark.parametrize("host", HOOKS)
@pytest.mark.parametrize(
    "command",
    [
        "sbx --help",
        "sbx help",
        "sbx env --help",
        "sbx env create --help",
        "sbx daemon restart --help",
        "sbx list --format json",
        "sbx diagnose --format json",
        "sbx env plan .sbx/sbxenv.yaml",
        "sbx kit validate .sbx/kit",
        "sbx exec project bun test",
        "sbx env exec .sbx/sbxenv.yaml -- bun test",
        'sbx env exec "/tmp/project with spaces/env.yaml" -- sh -c \'echo "$PATH"; bun test\'',
    ],
)
def test_matching_command_uses_native_hook_approval(host: str, command: str) -> None:
    assert _call(host, command) == (APPROVAL if host == "codex" else {"decision": "auto_approve"})


@pytest.mark.parametrize("host", HOOKS)
@pytest.mark.parametrize(
    "command",
    [
        "sbx rm project",
        "sbx env create .sbx/sbxenv.yaml",
        "sbx diagnose --upload",
        "sbx diagnose --format json --upload",
        "sbx kit add project kit",
        "sbx rm 'project --help'",
        "sbx rm -- --help",
        "sbx diagnose '--format json'",
        "sbx env --help; touch /tmp/host",
        "sbx env --help && touch /tmp/host",
        "sbx exec project true | touch /tmp/host",
        "sbx exec project true > /tmp/host",
        "sbx exec project true\ntouch /tmp/host",
        "sbx exec project $(touch /tmp/host)",
        'sbx exec project "$(touch /tmp/host)"',
        "sbx exec project `touch /tmp/host`",
        "sbx exec project *.json",
        "sbx exec project $HOST_COMMAND",
        "sbx exec project <(touch /tmp/host)",
        "sbx exec project true &",
        "sbx exec project true # comment",
        "env sbx --help",
        "bash -c 'sbx --help'",
        "/tmp/sbx --help",
        "sbx exec project 'unterminated",
    ],
)
def test_other_commands_keep_normal_approval(host: str, command: str) -> None:
    assert _call(host, command) == ({} if host == "codex" else {"decision": "allow"})


@pytest.mark.parametrize("host", HOOKS)
@pytest.mark.parametrize("payload", ["not json", "[]", "null", "{}", '{"tool_input":{"command":7}}'])
def test_invalid_input_keeps_normal_approval(host: str, payload: str) -> None:
    assert _run(host, payload) == ({} if host == "codex" else {"decision": "allow"})


@pytest.mark.parametrize(
    ("host", "payload"),
    [
        ("codex", {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "sbx --help"}}),
        (
            "codex",
            {"hook_event_name": "PermissionRequest", "tool_name": "Edit", "tool_input": {"command": "sbx --help"}},
        ),
        ("antigravity", {"toolCall": {"name": "write_to_file", "args": {"CommandLine": "sbx --help"}}}),
    ],
)
def test_other_events_do_not_get_command_grants(host: str, payload: dict) -> None:
    assert _run(host, json.dumps(payload)) == ({} if host == "codex" else {"decision": "allow"})


@pytest.mark.parametrize("host", HOOKS)
def test_packaged_skill_is_the_policy_source(host: str, tmp_path: Path) -> None:
    script = tmp_path / "scripts/command_approval.py"
    script.parent.mkdir()
    shutil.copy2(SKILL / "scripts/command_approval.py", script)
    policy = tmp_path / "SKILL.md"
    policy.write_text("---\nname: test\nallowed-tools:\n  - Bash(sbx custom)\n---\n")
    approve = APPROVAL if host == "codex" else {"decision": "auto_approve"}
    abstain = {} if host == "codex" else {"decision": "allow"}
    assert _call(host, "sbx custom", script) == approve
    assert _call(host, "sbx --help", script) == abstain
    policy.write_text("---\nallowed-tools: [Bash(sbx *)]\n---\n")
    assert _call(host, "sbx custom", script) == abstain
    policy.unlink()
    assert _call(host, "sbx custom", script) == abstain


def _render(path: Path, state: str, source: Path = ROOT) -> dict:
    result = subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(source),
            "execute-template",
            "--override-data",
            json.dumps({"ai": {"skills": {"authored": {"sbx-sandboxes": state}}}}),
            "-f",
            str(source / path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("host", HOOKS)
@pytest.mark.parametrize("state", ["present", "codex", "antigravity", "absent"])
def test_hooks_follow_skill_selection(host: str, state: str) -> None:
    rendered = _render(HOOKS[host], state)
    enabled = state == "present" or (host == "codex" and state == "codex")
    if not enabled:
        assert rendered == ({} if host == "antigravity" else {"hooks": {}})
        return
    if host == "codex":
        entry = rendered["hooks"]["PermissionRequest"][0]
        assert entry["matcher"] == "^Bash$"
    else:
        entry = rendered["sbx-command-approval"]["PreToolUse"][0]
        assert entry["matcher"] == "^run_command$"
    command = entry["hooks"][0]["command"]
    assert "command_approval.py" in command
    assert command.endswith(host)
    assert "{{" not in command
    assert "~" not in command


@pytest.mark.parametrize("host", HOOKS)
def test_hook_registration_changes_plugin_version(host: str, tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(ROOT / "src/chezmoi/.chezmoidata", source / "src/chezmoi/.chezmoidata")
    (source / ".chezmoiroot").write_text("src/chezmoi\n")
    manifest = BUNDLE / ("codex/dot_codex-plugin/plugin.json.tmpl" if host == "codex" else "plugin.json.tmpl")
    for path in (HOOKS[host], manifest):
        target = source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, target)
    before = _render(manifest, "present", source)["version"]
    with (source / HOOKS[host]).open("a") as stream:
        stream.write("\n")
    assert _render(manifest, "present", source)["version"] != before


@pytest.mark.skipif(shutil.which("agy") is None, reason="AGY is not installed")
def test_portable_plugin_passes_native_agy_validation(tmp_path: Path) -> None:
    manifest = _render(BUNDLE / "plugin.json.tmpl", "present")
    (tmp_path / "plugin.json").write_text(json.dumps(manifest))
    shutil.copytree(SKILL, tmp_path / "skills/sbx-sandboxes")
    (tmp_path / "hooks.json").write_text(json.dumps(_render(HOOKS["antigravity"], "present")))
    result = subprocess.run(
        ["agy", "plugin", "validate", str(tmp_path), "--json"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["components"]["hooks"] == 1
    assert report["components"]["skills"] == 1
