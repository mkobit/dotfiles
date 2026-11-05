"""Check native permission values with disposable chezmoi trees."""

import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / "src/chezmoi"
TEMPLATES = {
    "claude": "dot_claude/modify_settings.json",
    "antigravity": "dot_gemini/antigravity-cli/modify_settings.json",
    "codex": "dot_codex/modify_private_config.toml",
    "unattended": "dot_codex/modify_private_unattended.config.toml",
}
SELECTED = {
    "git push --set-upstream origin HEAD",
    "gh pr create",
    "gh pr ready",
    "gh pr merge",
    "gh issue create",
    "gh issue view",
    "gh issue list",
    "gh run view",
    "gh run list",
    "gh run watch",
    "gh repo view",
    "mise run agent:architect",
    "mise run agent:work",
    "mise run pr:ship",
    "mise run repo:bootstrap",
    "mise run verify",
}


@pytest.fixture
def tree(tmp_path: Path) -> tuple[Path, Path]:
    source, target = tmp_path / "source", tmp_path / "target"
    shutil.copytree(ROOT / ".chezmoidata", source / ".chezmoidata")
    for name in [*TEMPLATES.values(), ".chezmoiignore.tmpl"]:
        if (ROOT / name).exists():
            destination = source / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
    target.mkdir()
    return source, target


def _run(tree: tuple[Path, Path], *args: str, stdin: str = "") -> str:
    source, target = tree
    result = subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(source),
            "--destination",
            str(target),
            *args,
        ],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _render(tree: tuple[Path, Path], tool: str, live: str = "", override: dict | None = None) -> str:
    data = {"local": {"bin": {"agy": {"installation_method": "preinstalled"}}}}
    data.update(override or {})
    return _run(
        tree,
        "execute-template",
        "-f",
        "--with-stdin",
        "--override-data",
        json.dumps(data),
        str(tree[0] / TEMPLATES[tool]),
        stdin=live,
    )


def _entry(tool: str, head: str) -> str:
    return f"Bash({head}:*)" if tool == "claude" else f"command({head})"


def _settings(tool: str, permissions: dict) -> dict:
    if tool == "claude":
        return {"claude_code": {"settings": {"permissions": permissions}}}
    return {"gemini": {"permissions": permissions}}


@pytest.mark.parametrize("tool", ["claude", "antigravity"])
def test_selected_heads_render_without_broad_grants(tree: tuple[Path, Path], tool: str) -> None:
    permissions = json.loads(_render(tree, tool))["permissions"]
    allow = permissions["allow"]
    for head in SELECTED | {"gh pr checks", "gh pr diff", "gh pr list", "gh pr status", "gh pr view"}:
        assert _entry(tool, head) in allow
    for head in ["mise", "bd", "sbx", "git push", "git reset", "git clean", "git push --force", "gh auth"]:
        assert _entry(tool, head) not in allow
    assert not any("../" in entry for entry in permissions.get("deny", []))


@pytest.mark.parametrize("tool", ["claude", "antigravity"])
@pytest.mark.parametrize("mode", ["ask", "deny"])
def test_explicit_mode_removes_exact_previous_allow(tree: tuple[Path, Path], tool: str, mode: str) -> None:
    head = "gh pr create"
    entry, broad, unrelated = (_entry(tool, cmd) for cmd in [head, "gh pr", "custom inspect"])
    live = json.dumps({"permissions": {"allow": [broad, unrelated], "ask": ["custom ask"], "other": 7}})
    first = _render(tree, tool, live, {"ai": {"command_policy": {"commands": {head: "allow"}}}})
    assert entry in json.loads(first)["permissions"]["allow"]
    override = {"ai": {"command_policy": {"commands": {head: mode}}}}
    second = _render(tree, tool, first, override)
    permissions = json.loads(second)["permissions"]
    assert entry not in permissions["allow"]
    assert broad in permissions["allow"]  # Broader live grants have not been revoked.
    assert unrelated in permissions["allow"]
    assert permissions["ask"] == ["custom ask"]
    assert permissions["other"] == 7
    assert (entry in permissions.get("deny", [])) == (mode == "deny")
    assert _render(tree, tool, second, override) == second


@pytest.mark.parametrize("tool", ["claude", "antigravity"])
@pytest.mark.parametrize("mode", ["ask", "deny"])
@pytest.mark.parametrize("remove", [False, True])
def test_exact_ensure_exception_respects_deny_and_remove(
    tree: tuple[Path, Path], tool: str, mode: str, remove: bool
) -> None:
    head = "gh pr create"
    entry, unrelated = (_entry(tool, cmd) for cmd in [head, "custom ensured"])
    first = _render(tree, tool, "", {"ai": {"command_policy": {"commands": {head: "allow"}}}})
    assert entry in json.loads(first)["permissions"]["allow"]
    override = _settings(tool, {"allow": [entry, unrelated], "remove": [entry] if remove else []})
    override["ai"] = {"command_policy": {"commands": {head: mode}}}
    second = _render(tree, tool, first, override)
    permissions = json.loads(second)["permissions"]
    assert (entry in permissions["allow"]) == (mode == "ask" and not remove)
    assert unrelated in permissions["allow"]
    assert (entry in permissions.get("deny", [])) == (mode == "deny")
    assert "remove" not in permissions
    assert _render(tree, tool, second, override) == second


@pytest.mark.parametrize("tool", ["claude", "antigravity"])
@pytest.mark.parametrize("mode", ["allow", "ask"])
def test_preexisting_exact_native_denial_survives_catalog_relaxation(
    tree: tuple[Path, Path], tool: str, mode: str
) -> None:
    head = "gh pr create"
    entry, unrelated = (_entry(tool, cmd) for cmd in [head, "custom denied"])
    live = json.dumps({"permissions": {"deny": [entry, unrelated]}})
    first = _render(tree, tool, live, {"ai": {"command_policy": {"commands": {head: "deny"}}}})
    override = _settings(tool, {"allow": [entry]})
    override["ai"] = {"command_policy": {"commands": {head: mode}}}
    second = _render(tree, tool, first, override)
    permissions = json.loads(second)["permissions"]
    assert entry in permissions["deny"]
    assert unrelated in permissions["deny"]
    assert _render(tree, tool, second, override) == second


@pytest.mark.parametrize("tool", ["claude", "antigravity"])
def test_native_denials_merge_and_allow_controls_survive(tree: tuple[Path, Path], tool: str) -> None:
    native = ["Read(.private/**)", "Edit(.private/**)"]
    if tool == "antigravity":
        native = ["read_file(.private/)", "write_file(.private/)"]
    removed, ensured, denied = (_entry(tool, cmd) for cmd in ["git status", "custom inspect", "gh pr merge"])
    override = _settings(tool, {"allow": [ensured, removed], "remove": [removed], "deny": native})
    override["ai"] = {"command_policy": {"commands": {"gh pr merge": "deny"}}}
    live = json.dumps({"permissions": {"allow": [removed], "deny": ["custom live denial"]}, "custom": True})
    defaults = json.loads(_render(tree, tool))["permissions"].get("deny", [])
    first = _render(tree, tool, live, override)
    rendered = json.loads(first)
    assert rendered["permissions"]["deny"] == sorted({*defaults, *native, denied, "custom live denial"})
    assert ensured in rendered["permissions"]["allow"]
    assert removed not in rendered["permissions"]["allow"]
    assert "remove" not in rendered["permissions"]
    assert rendered["custom"] is True
    assert _render(tree, tool, first, override) == first


@pytest.mark.parametrize("tool", ["claude", "antigravity"])
def test_omission_preserves_previous_live_allow(tree: tuple[Path, Path], tool: str) -> None:
    head = "custom inspect"
    first = _render(tree, tool, "", {"ai": {"command_policy": {"commands": {head: "allow"}}}})
    assert _entry(tool, head) in json.loads(_render(tree, tool, first))["permissions"]["allow"]


@pytest.mark.parametrize(
    ("existing", "modern"),
    [
        ('default_permissions = ":read-only"\n', True),
        ('default_permissions = "audit"\n[permissions.audit]\nextends = ":read-only"\n', True),
        ('sandbox_mode = "read-only"\n[sandbox_workspace_write]\nnetwork_access = false\n', False),
        ("", True),
    ],
)
def test_codex_host_and_explicit_profile_use_compatible_schemes(
    tree: tuple[Path, Path], existing: str, modern: bool
) -> None:
    existing = 'approval_policy = "never"\nmodel = "preserve"\n' + existing
    base = _render(tree, "codex", existing)
    host = tomllib.loads(base)
    assert host["approval_policy"] == "on-request"
    assert host["model"] == "preserve"
    if modern:
        assert host["default_permissions"] == ":workspace"
        assert "sandbox_mode" not in host
        assert "sandbox_workspace_write" not in host
    else:
        assert host["sandbox_mode"] == "workspace-write"
        assert host["sandbox_workspace_write"] == {"network_access": False}
        assert "default_permissions" not in host
    if "permissions" in tomllib.loads(existing):
        assert host["permissions"] == tomllib.loads(existing)["permissions"]
    matching = "# Preserve this comment and spacing.\n" + base
    assert _render(tree, "codex", matching) == matching
    path = tree[1] / ".codex/config.toml"
    path.parent.mkdir()
    path.write_text(base)
    # The old profile uses the opposite scheme. Reconcile only managed keys.
    old = 'model = "profile-preserve"\n' + (
        'sandbox_mode = "read-only"\n[sandbox_workspace_write]\nnetwork_access = false\n'
        if modern
        else 'default_permissions = ":read-only"\n'
    )
    old += '[permissions.profile_audit]\nextends = ":read-only"\n'
    profile_text = _render(tree, "unattended", old)
    profile = tomllib.loads(profile_text)
    layered = host | profile
    assert profile["approval_policy"] == "never"
    assert profile["model"] == "profile-preserve"
    assert profile["permissions"] == tomllib.loads(old)["permissions"]
    if modern:
        assert layered["default_permissions"] == ":danger-full-access"
        assert "sandbox_mode" not in layered
        assert "sandbox_workspace_write" not in layered
    else:
        assert layered["sandbox_mode"] == "danger-full-access"
        assert "default_permissions" not in layered
    assert "profiles" not in profile
    assert _render(tree, "unattended", profile_text) == profile_text


@pytest.mark.parametrize("enabled", [None, False, True])
def test_unattended_profile_deployment_gate(tree: tuple[Path, Path], enabled: bool | None) -> None:
    source, target = tree
    # A disposable apply contains only the new modifier and the real ignore template.
    for tool in ["claude", "antigravity", "codex"]:
        (source / TEMPLATES[tool]).unlink()
    config = source.parent / "test.toml"
    config.write_text(
        "[data]\n" + ("" if enabled is None else f"[data.ai.workflow]\nenabled = {str(enabled).lower()}\n")
    )
    path = target / ".codex/unattended.config.toml"
    path.parent.mkdir()
    original = '# Unowned profile\nmodel = "preserve"\n'
    path.write_text(original)
    _run(tree, "--config", str(config), "apply", "--force")
    if not enabled:
        assert path.read_text() == original
        path.unlink()
        _run(tree, "--config", str(config), "apply", "--force")
        assert not path.exists()
    else:
        assert tomllib.loads(path.read_text())["approval_policy"] == "never"
        assert path.stat().st_mode & 0o777 == 0o600
        first = path.read_bytes()
        _run(tree, "--config", str(config), "apply", "--force")
        assert path.read_bytes() == first
        path.unlink()
        _run(tree, "--config", str(config), "apply", "--force")
        assert tomllib.loads(path.read_text())["default_permissions"] == ":danger-full-access"
        assert path.stat().st_mode & 0o777 == 0o600
    assert not (ROOT / TEMPLATES["unattended"]).stat().st_mode & 0o111
