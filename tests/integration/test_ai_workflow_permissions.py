"""Check explicit prompts and the existing ask contract."""

import pytest
from test_sbx_command_retirement import ALLOW_HEADS, PROMPT_HEADS, TEMPLATES, _render, rule


@pytest.mark.parametrize("tool", TEMPLATES)
def test_sbx_policy_has_no_broad_allow(tool: str) -> None:
    permissions = _render(tool)["permissions"]
    actual = {entry for entry in permissions["allow"] if entry.startswith(("Bash(sbx", "command(sbx"))}
    assert actual == {rule(tool, head) for head in ALLOW_HEADS}
    assert {rule(tool, head) for head in PROMPT_HEADS} <= set(permissions["ask"])


@pytest.mark.parametrize("tool", TEMPLATES)
def test_ask_stays_absent_and_prompt_merges_live_asks(tool: str) -> None:
    live = {"permissions": {"ask": [rule(tool, "retained")], "deny": [rule(tool, "retained deny")]}}
    override = {"ai": {"command_policy": {"commands": {"custom ask": "ask", "literal a.b+": "prompt"}}}}
    permissions = _render(tool, live, override)["permissions"]
    assert rule(tool, "custom ask") not in permissions["ask"]
    expected = rule(tool, "literal a.b+")
    assert expected in permissions["ask"]
    assert rule(tool, "retained") in permissions["ask"]
    assert rule(tool, "retained deny") in permissions["deny"]


@pytest.mark.parametrize("tool", TEMPLATES)
@pytest.mark.parametrize(
    "head",
    [
        "sbx runner",
        "sbx executor",
        "sbx kit",
        "sbx diagnose",
        "sbx ports",
        "sbx prune",
        "sbx secret",
        "sbx policy allow",
    ],
)
def test_unselected_heads_have_no_automatic_grant(tool: str, head: str) -> None:
    assert rule(tool, head) not in _render(tool)["permissions"]["allow"]


@pytest.mark.parametrize("tool", TEMPLATES)
def test_overlay_prompt_retains_configured_asks_and_denials(tool: str) -> None:
    ask, deny = rule(tool, "configured ask"), rule(tool, "configured deny")
    override = {"ai": {"command_policy": {"commands": {"sbx list": "prompt", "sbx inspect": "ask"}}}}
    if tool == "claude":
        override["claude_code"] = {"settings": {"permissions": {"ask": [ask], "deny": [deny]}}}
    else:
        override["gemini"] = {"permissions": {"ask": [ask], "deny": [deny]}}
    permissions = _render(tool, override=override)["permissions"]
    assert rule(tool, "sbx list") in permissions["ask"]
    assert rule(tool, "sbx list") not in permissions["allow"]
    assert rule(tool, "sbx inspect") not in permissions["ask"]
    assert rule(tool, "sbx inspect") not in permissions["allow"]
    assert ask in permissions["ask"]
    assert deny in permissions["deny"]
