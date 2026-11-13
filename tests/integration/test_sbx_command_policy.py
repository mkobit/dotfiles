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


@pytest.fixture
def codex_rules(tmp_path: Path):
    """Apply the managed rules without replacing user rule files."""
    source = tmp_path / "source"
    source.mkdir()
    shutil.copytree(ROOT / "src/chezmoi/.chezmoidata", source / ".chezmoidata")
    relative = Path("dot_codex/rules/dotfiles-sbx.rules.tmpl")
    template = source / relative
    template.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "src/chezmoi" / relative, template)
    destination = tmp_path / "destination"
    rules = destination / ".codex/rules"
    rules.mkdir(parents=True)
    user_files = {
        "default.rules": 'prefix_rule(pattern=["sbx"], decision="allow")\n',
        "personal.rules": (
            'prefix_rule(pattern=["sbx", "env", "exec"], decision="forbidden")\n'
            'prefix_rule(pattern=["sbx", "rm"], decision="forbidden")\n'
        ),
    }
    for name, content in user_files.items():
        (rules / name).write_text(content)
    config = tmp_path / "config.json"
    config.write_text("{}")
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

    def apply(commands: dict[str, str] | None = None, *, empty_catalog: bool = False) -> Path:
        if empty_catalog:
            shutil.rmtree(source / ".chezmoidata")
        data = {} if empty_catalog else {"ai": {"command_policy": {"commands": commands or {}}}}
        config.write_text(json.dumps({"data": data}))
        preview = subprocess.run([*command, "diff"], capture_output=True, text=True, check=True)
        assert preview.stdout
        subprocess.run([*command, "apply"], capture_output=True, text=True, check=True)
        target = rules / "dotfiles-sbx.rules"
        first = target.read_bytes()
        assert not subprocess.run([*command, "diff"], capture_output=True, text=True, check=True).stdout
        subprocess.run([*command, "apply"], capture_output=True, text=True, check=True)
        assert target.read_bytes() == first
        for name, content in user_files.items():
            assert (rules / name).read_text() == content
        return target

    return apply


def native_codex_decision(rules: list[Path], command: str) -> dict:
    """Evaluate rendered rules with Codex, without executing the command."""
    if shutil.which("codex") is None:
        pytest.skip("Native Codex execpolicy check requires the Codex CLI")
    arguments = ["codex", "execpolicy", "check"]
    for path in rules:
        arguments.extend(["--rules", str(path)])
    result = subprocess.run([*arguments, "--", *shlex.split(command)], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_codex_apply_preserves_user_rules(codex_rules) -> None:
    target = codex_rules()
    assert target.read_text().strip()


def test_codex_native_policy_heads_and_precedence(codex_rules) -> None:
    target = codex_rules()
    for head in ALLOW_HEADS:
        assert native_codex_decision([target], f"{head} pilot")["decision"] == "allow"
    for head in PROMPT_HEADS:
        assert native_codex_decision([target], f"{head} pilot -- echo ready")["decision"] == "prompt"
    default = target.parent / "default.rules"
    personal = target.parent / "personal.rules"
    for head in PROMPT_HEADS:
        assert native_codex_decision([target, default], f"{head} pilot")["decision"] == "prompt"
    for head in ("sbx env exec", "sbx rm"):
        assert native_codex_decision([target, default, personal], f"{head} pilot")["decision"] == "forbidden"
    for command in (
        "sbx runner pilot",
        "sbx executor pilot",
        "sbx listing",
        "sbx kit inspection",
        "sbx prune",
        "sbx secret set",
        "sbx cp",
        "sbx diagnose --upload",
        "sbx ports",
        "sbx",
        "sbx-other list",
        "git status",
    ):
        assert native_codex_decision([target], command) == {"matchedRules": []}


def test_codex_native_overlay_decisions(codex_rules) -> None:
    target = codex_rules(
        {
            "sbx list": "deny",
            "sbx inspect": "prompt",
            "sbx exec": "allow",
            "sbx rm": "ask",
            "sbx custom": "allow",
            "sbx custom-deny": "deny",
            "sbx-other custom": "allow",
            "other custom": "allow",
        }
    )
    for command, decision in (
        ("sbx list", "forbidden"),
        ("sbx inspect", "prompt"),
        ("sbx exec", "allow"),
        ("sbx custom", "allow"),
        ("sbx custom-deny", "forbidden"),
    ):
        assert native_codex_decision([target], command)["decision"] == decision
    for command in ("sbx rm", "sbx-other custom", "other custom"):
        assert native_codex_decision([target], command) == {"matchedRules": []}


def test_codex_apply_without_catalog(codex_rules) -> None:
    target = codex_rules(empty_catalog=True)
    assert "prefix_rule" not in target.read_text()
