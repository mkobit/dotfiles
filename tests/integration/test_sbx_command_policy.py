"""Check central SBX decisions through disposable Chezmoi apply."""

import json
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest
from test_sbx_command_retirement import ALLOW_HEADS, PROMPT_HEADS, ROOT, TEMPLATES, rule


def documented_decision(tool: str, permissions: dict, command: str) -> str:
    """Model the documented token-prefix and deny > ask > allow contract.

    This test model does not execute a native permission evaluator.
    Sources: https://code.claude.com/docs/en/permissions#manage-permissions
    https://antigravity.google/docs/permissions/#cli-fine-grained-permissions
    """
    tokens = shlex.split(command)
    for action in ("deny", "ask", "allow"):
        for entry in permissions.get(action, []):
            if tool == "claude":
                if not entry.startswith("Bash(") or not entry.endswith(":*)"):
                    continue
                head = entry[5:-3]
            else:
                if not entry.startswith("command(") or not entry.endswith(")"):
                    continue
                head = entry[8:-1]
            prefix = shlex.split(head)
            if tokens[: len(prefix)] == prefix:
                return action
    return "ask"


@pytest.mark.parametrize("tool", TEMPLATES)
def test_apply_preserves_native_permissions_and_prompts(tool: str, tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    shutil.copytree(ROOT / "src/chezmoi/.chezmoidata", source / ".chezmoidata")
    relative = TEMPLATES[tool].relative_to(ROOT / "src/chezmoi")
    template = source / relative
    template.parent.mkdir(parents=True)
    shutil.copyfile(TEMPLATES[tool], template)
    destination = tmp_path / "destination"
    destination.mkdir()
    target = destination / (".claude/settings.json" if tool == "claude" else ".gemini/antigravity-cli/settings.json")
    target.parent.mkdir(parents=True)
    broad = "Bash(sbx:*)" if tool == "claude" else "command(sbx)"
    denial = rule(tool, "sbx env exec")
    live_ask = rule(tool, "custom ask")
    target.write_text(json.dumps({"custom": 7, "permissions": {"allow": [broad], "ask": [live_ask], "deny": [denial]}}))
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "data": {
                    "local": {"bin": {"agy": {"installation_method": "preinstalled"}}},
                    "ai": {"command_policy": {"commands": {"custom deny": "deny"}}},
                }
            }
        )
    )
    command = [
        "chezmoi",
        "--source",
        str(source),
        "--destination",
        str(destination),
        "--config",
        str(config),
        "--persistent-state",
        str(tmp_path / "state.boltdb"),
    ]
    preview = subprocess.run([*command, "diff"], capture_output=True, text=True, check=True)
    assert preview.stdout
    subprocess.run([*command, "apply"], capture_output=True, text=True, check=True)
    first = target.read_bytes()
    rendered = json.loads(first)
    permissions = rendered["permissions"]
    assert {rule(tool, head) for head in ALLOW_HEADS} <= set(permissions["allow"])
    assert {rule(tool, head) for head in PROMPT_HEADS} <= set(permissions["ask"])
    assert broad in permissions["allow"]
    assert live_ask in permissions["ask"]
    assert {denial, rule(tool, "custom deny")} <= set(permissions["deny"])
    assert rendered["custom"] == 7
    # Exercise the documented contract against the real applied settings.
    # This is contract coverage, not native runtime enforcement evidence.
    for head in PROMPT_HEADS:
        expected = "deny" if head == "sbx env exec" else "ask"
        assert documented_decision(tool, permissions, f"{head} pilot -- echo ready") == expected
    for head in ALLOW_HEADS:
        assert documented_decision(tool, permissions, f"{head} pilot") == "allow"
    # Remove the seeded broad grant to check the generated token boundaries.
    selected = {**permissions, "allow": [entry for entry in permissions["allow"] if entry != broad]}
    for sample in (
        "sbx runner pilot",
        "sbx executor pilot",
        "sbx listing",
        "sbx kit inspection",
        "sbx prune",
        "sbx secret set",
    ):
        assert documented_decision(tool, selected, sample) == "ask"
    assert not subprocess.run([*command, "diff"], capture_output=True, text=True, check=True).stdout
    subprocess.run([*command, "apply"], capture_output=True, text=True, check=True)
    assert target.read_bytes() == first
