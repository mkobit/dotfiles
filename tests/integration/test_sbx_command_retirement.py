"""Check SBX permission migration through real chezmoi templates."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = {
    "claude": ROOT / "src/chezmoi/dot_claude/modify_settings.json",
    "antigravity": ROOT / "src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json",
}
OLD = {
    "claude": (
        "Bash(sbx kit:*)",
        "Bash(sbx env exec:*)",
        "Bash(sbx kit pack:*)",
        "Bash(sbx --help:*)",
        "Bash(sbx --version:*)",
        "Bash(sbx help:*)",
        "Bash(sbx ls:*)",
        "Bash(sbx list:*)",
        "Bash(sbx version:*)",
    ),
    "antigravity": (
        "command(sbx kit)",
        "command(sbx env exec)",
        "command(sbx kit pack)",
        "command(sbx --help)",
        "command(sbx --version)",
        "command(sbx help)",
        "command(sbx ls)",
        "command(sbx list)",
        "command(sbx version)",
    ),
}
KEEP = {
    "claude": ("Bash(sbx env exec .sbx/sbxenv.yaml:*)", "Bash(sbx custom:*)", "Read(./notes.md)"),
    "antigravity": (
        "command(sbx env exec .sbx/sbxenv.yaml)",
        "command(sbx custom)",
        "read_url(example.com)",
    ),
}


def _render(tool: str, live: dict | None = None, override: dict | None = None, source: Path = ROOT) -> dict:
    data = {"local": {"bin": {"agy": {"installation_method": "preinstalled"}}}}
    if override:
        data.update(override)
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
            "-f",
            "--with-stdin",
            "--override-data",
            json.dumps(data),
            str(source / TEMPLATES[tool].relative_to(ROOT)),
        ],
        input=json.dumps(live or {}),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("tool", TEMPLATES)
def test_fresh_settings_do_not_grant_global_sbx_commands(tool: str) -> None:
    allow = _render(tool)["permissions"]["allow"]
    actual = {entry for entry in allow if entry.startswith(("Bash(sbx ", "command(sbx "))}
    assert actual == set()


@pytest.mark.parametrize("tool", TEMPLATES)
def test_retirement_removes_exact_live_grants_only(tool: str) -> None:
    live = {"permissions": {"allow": [*OLD[tool], *KEEP[tool]], "unknown": 7}, "custom": True}
    rendered = _render(tool, live)
    allow = rendered["permissions"]["allow"]
    assert all(entry not in allow for entry in OLD[tool])
    assert all(entry in allow for entry in KEEP[tool])
    assert rendered["permissions"]["unknown"] == 7
    assert rendered["custom"] is True


@pytest.mark.parametrize("tool", TEMPLATES)
@pytest.mark.parametrize("head", ["sbx env exec", "sbx list"])
def test_overlay_command_grant_survives_retirement(tool: str, head: str) -> None:
    entry = f"Bash({head}:*)" if tool == "claude" else f"command({head})"
    override = {"ai": {"command_policy": {"commands": {head: "allow"}}}}
    allow = _render(tool, {"permissions": {"allow": [entry]}}, override)["permissions"]["allow"]
    assert entry in allow


@pytest.mark.parametrize("tool", TEMPLATES)
def test_configured_ensure_survives_retirement(tool: str) -> None:
    entry = OLD[tool][1]
    if tool == "claude":
        override = {"claude_code": {"settings": {"permissions": {"allow": [entry]}}}}
    else:
        override = {"gemini": {"permissions": {"allow": [entry]}}}
    allow = _render(tool, {"permissions": {"allow": [entry]}}, override)["permissions"]["allow"]
    assert entry in allow


@pytest.mark.parametrize("tool", TEMPLATES)
def test_explicit_removal_wins_over_computed_ensure_and_live(tool: str) -> None:
    entry = OLD[tool][1]
    override = {"ai": {"command_policy": {"commands": {"sbx env exec": "allow"}}}}
    if tool == "claude":
        override["claude_code"] = {"settings": {"permissions": {"allow": [entry], "remove": [entry]}}}
    else:
        override["gemini"] = {"permissions": {"allow": [entry], "remove": [entry]}}
    allow = _render(tool, {"permissions": {"allow": [entry]}}, override)["permissions"]["allow"]
    assert entry not in allow


@pytest.mark.parametrize("tool", TEMPLATES)
def test_retirement_render_is_idempotent(tool: str) -> None:
    live = {"permissions": {"allow": [OLD[tool][0], KEEP[tool][0]]}, "custom": True}
    first = _render(tool, live)
    assert _render(tool, first) == first


def test_disabled_antigravity_path_keeps_live_permissions() -> None:
    override = {"local": {"bin": {"agy": {"installation_method": "none"}}}}
    live = {"permissions": {"allow": [OLD["antigravity"][0]]}}
    assert _render("antigravity", live, override) == live


@pytest.mark.parametrize("tool", TEMPLATES)
def test_false_retirement_flag_keeps_live_grant(tool: str) -> None:
    override = {"ai": {"command_policy": {"retired_commands": {"sbx env exec": False}}}}
    allow = _render(tool, {"permissions": {"allow": [OLD[tool][1]]}}, override)["permissions"]["allow"]
    assert OLD[tool][1] in allow


@pytest.mark.parametrize("tool", TEMPLATES)
def test_missing_retirement_data_is_safe(tool: str, tmp_path: Path) -> None:
    source = tmp_path / "checkout"
    shutil.copytree(ROOT / "src/chezmoi", source / "src/chezmoi")
    (source / "src/chezmoi/.chezmoidata/ai/command_policy/sbx.toml").unlink()
    live = {"permissions": {"allow": [OLD[tool][1]]}}
    assert OLD[tool][1] in _render(tool, live, source=source)["permissions"]["allow"]
