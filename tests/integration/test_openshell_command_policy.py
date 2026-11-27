"""Check host-gated OpenShell command policy decisions through Chezmoi templates and apply."""

import json
import shlex
import shutil
from pathlib import Path

import pytest

from chezmoi_cli import ChezmoiCli

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = {
    "claude": ROOT / "src/chezmoi/dot_claude/modify_settings.json",
    "antigravity": ROOT / "src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json",
}

ALLOW_HEADS = {
    "openshell --help",
    "openshell --version",
    "openshell doctor",
    "openshell forward list",
    "openshell gateway info",
    "openshell gateway list",
    "openshell help",
    "openshell logs",
    "openshell policy get",
    "openshell profile describe",
    "openshell profile export",
    "openshell profile lint",
    "openshell profile list",
    "openshell provider list",
    "openshell rule get",
    "openshell sandbox get",
    "openshell sandbox list",
    "openshell sandbox ssh-config",
    "openshell status",
}

PROMPT_HEADS = {
    "openshell forward start",
    "openshell forward stop",
    "openshell gateway add",
    "openshell gateway destroy",
    "openshell gateway login",
    "openshell gateway logout",
    "openshell gateway remove",
    "openshell gateway select",
    "openshell gateway start",
    "openshell gateway stop",
    "openshell policy set",
    "openshell policy update",
    "openshell profile import",
    "openshell provider create",
    "openshell provider delete",
    "openshell provider refresh",
    "openshell provider update",
    "openshell rule approve",
    "openshell rule reject",
    "openshell sandbox connect",
    "openshell sandbox create",
    "openshell sandbox delete",
    "openshell sandbox exec",
    "openshell sandbox start",
    "openshell sandbox stop",
}


def rule(tool: str, head: str) -> str:
    return f"Bash({head}:*)" if tool == "claude" else f"command({head})"


def documented_decision(tool: str, permissions: dict, command: str) -> str:
    """Model the documented token-prefix and deny > ask > allow contract."""
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


def _render(
    tool: str,
    live: dict | None = None,
    override: dict | None = None,
    source: Path = ROOT,
) -> dict:
    data: dict = {
        "local": {
            "bin": {
                "agy": {"installation_method": "preinstalled"},
                "openshell": {"installation_method": "github_releases"},
            }
        }
    }
    if override:
        data.update(override)
    result = (
        ChezmoiCli(config="/dev/null", config_format="toml", source=source)
        .execute_template(
            file=source / TEMPLATES[tool].relative_to(ROOT),
            with_stdin=True,
            override_data=data,
        )
        .run(input=json.dumps(live or {}))
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("tool", TEMPLATES)
def test_enabled_openshell_grants_host_commands(tool: str) -> None:
    rendered = _render(tool)
    permissions = rendered["permissions"]
    actual_allow = {
        entry for entry in permissions["allow"] if entry.startswith(("Bash(openshell ", "command(openshell "))
    }
    actual_ask = {
        entry for entry in permissions.get("ask", []) if entry.startswith(("Bash(openshell ", "command(openshell "))
    }
    assert actual_allow == {rule(tool, head) for head in ALLOW_HEADS}
    assert actual_ask == {rule(tool, head) for head in PROMPT_HEADS}


@pytest.mark.parametrize("tool", TEMPLATES)
def test_disabled_or_omitted_openshell_omits_host_commands(tool: str) -> None:
    disabled_override = {
        "local": {
            "bin": {
                "agy": {"installation_method": "preinstalled"},
                "openshell": {"installation_method": "none"},
            }
        }
    }
    rendered_disabled = _render(tool, override=disabled_override)
    permissions_disabled = rendered_disabled["permissions"]
    assert not any(
        entry.startswith(("Bash(openshell ", "command(openshell ")) for entry in permissions_disabled["allow"]
    )
    assert not any(
        entry.startswith(("Bash(openshell ", "command(openshell ")) for entry in permissions_disabled.get("ask", [])
    )

    omitted_override = {
        "local": {
            "bin": {
                "agy": {"installation_method": "preinstalled"},
            }
        }
    }
    rendered_omitted = _render(tool, override=omitted_override)
    permissions_omitted = rendered_omitted["permissions"]
    assert not any(
        entry.startswith(("Bash(openshell ", "command(openshell ")) for entry in permissions_omitted["allow"]
    )
    assert not any(
        entry.startswith(("Bash(openshell ", "command(openshell ")) for entry in permissions_omitted.get("ask", [])
    )


@pytest.mark.parametrize("tool", TEMPLATES)
def test_commands_table_overrides_host_commands(tool: str) -> None:
    override = {
        "ai": {
            "command_policy": {
                "commands": {
                    "openshell status": "deny",
                    "openshell sandbox exec": "allow",
                }
            }
        }
    }
    permissions = _render(tool, override=override)["permissions"]
    assert rule(tool, "openshell status") in permissions["deny"]
    assert rule(tool, "openshell status") not in permissions["allow"]
    assert rule(tool, "openshell sandbox exec") in permissions["allow"]
    assert rule(tool, "openshell sandbox exec") not in permissions.get("ask", [])


@pytest.mark.parametrize("tool", TEMPLATES)
def test_apply_preserves_native_permissions_and_prompts_for_openshell(tool: str, tmp_path: Path) -> None:
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
    broad = "Bash(openshell:*)" if tool == "claude" else "command(openshell)"
    denial = rule(tool, "openshell sandbox exec")
    target.write_text(json.dumps({"custom": 7, "permissions": {"allow": [broad], "deny": [denial]}}))

    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "data": {
                    "local": {
                        "bin": {
                            "agy": {"installation_method": "preinstalled"},
                            "openshell": {"installation_method": "github_releases"},
                        }
                    }
                }
            }
        )
    )
    ChezmoiCli(
        source=source,
        destination=destination,
        config=config,
        persistent_state=tmp_path / "state.boltdb",
    ).apply().run(check=True)
    rendered = json.loads(target.read_bytes())
    permissions = rendered["permissions"]

    for head in PROMPT_HEADS:
        expected = "deny" if head == "openshell sandbox exec" else "ask"
        assert documented_decision(tool, permissions, f"{head} pilot") == expected
    for head in ALLOW_HEADS:
        assert documented_decision(tool, permissions, f"{head} pilot") == "allow"

    selected = {**permissions, "allow": [entry for entry in permissions["allow"] if entry != broad]}
    for sample in (
        "openshell unknown",
        "openshell sandbox unknown",
        "openshell provider get",
    ):
        assert documented_decision(tool, selected, sample) == "ask"
