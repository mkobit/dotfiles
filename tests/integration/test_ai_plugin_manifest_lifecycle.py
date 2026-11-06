"""Integration coverage for authored plugin manifest convergence."""

import json
import shutil

import pytest

MARKET = ".local/share/agent-plugins/marketplace/plugins/domain-brain"
CURSOR_LOCAL = ".cursor/plugins/local/domain-brain"
MANIFESTS = {
    "claude": f"{MARKET}/claude/.claude-plugin/plugin.json",
    "codex": f"{MARKET}/codex/.codex-plugin/plugin.json",
    "cursor": f"{MARKET}/cursor/.cursor-plugin/plugin.json",
    "cursor-local": f"{CURSOR_LOCAL}/.cursor-plugin/plugin.json",
}


def _write_config(fixture, *, hosts: tuple[str, ...], environment: str) -> None:
    fixture.write_config(
        '[data.ai.plugin_bridge.capabilities.domain-brain]\nenvironments = ["personal"]\n'
        f"hosts = {json.dumps(list(hosts))}\n"
    )
    text = fixture.config.read_text(encoding="utf-8")
    hosts_line = 'default_hosts = ["claude", "codex", "cursor"]\n'
    fixture.config.write_text(text.replace(hosts_line, f"{hosts_line}environment = {json.dumps(environment)}\n", 1))


def _snapshot(fixture) -> dict[str, bytes]:
    roots = (fixture.destination / MARKET, fixture.destination / CURSOR_LOCAL)
    return {
        path.relative_to(fixture.destination).as_posix(): path.read_bytes()
        for root in roots
        if root.exists()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize(
    ("change", "expected_hosts"),
    [
        ("host_removed", {"claude", "codex"}),
        ("environment_disabled", set()),
        ("declaration_removed", set()),
    ],
)
def test_disabled_capability_manifest_cleanup_converges_on_repeat_apply(agent_source_fixture, change, expected_hosts):
    """Ignore views drop deselected manifests from the source state, and repeat apply is stable."""
    fixture = agent_source_fixture
    plugin = fixture.write_plugin("domain-brain", skills={"records": {"SKILL.md": "# Records\n"}})
    _write_config(fixture, hosts=("claude", "codex", "cursor"), environment="personal")
    first = fixture.run("apply")
    assert first.returncode == 0, first.stderr
    assert all((fixture.destination / path).is_file() for path in MANIFESTS.values())
    sibling = fixture.destination / MARKET / "notes.json"
    sibling.write_text('{"keep":true}\n', encoding="utf-8")

    if change == "host_removed":
        _write_config(fixture, hosts=("claude", "codex"), environment="personal")
    elif change == "environment_disabled":
        _write_config(fixture, hosts=("claude", "codex", "cursor"), environment="work")
    else:
        shutil.rmtree(plugin)

    managed = fixture.managed_files()
    assert {host for host, path in MANIFESTS.items() if path in managed} == expected_hosts
    second = fixture.run("apply")
    assert second.returncode == 0, second.stderr
    # The exact plugin root prunes unmanaged children while the plugin stays managed;
    # an unmanaged root keeps them until root ownership cleanup removes it.
    assert sibling.exists() is (change != "host_removed")
    after_transition = _snapshot(fixture)

    diff = fixture.run("--no-pager", "diff")
    assert diff.returncode == 0, diff.stderr
    assert diff.stdout == ""
    third = fixture.run("apply")
    assert third.returncode == 0, third.stderr
    assert _snapshot(fixture) == after_transition


def test_runtime_bytecode_cache_survives_repeat_apply_in_exact_plugin_root(agent_source_fixture):
    """Ignore views keep Python bytecode that skill scripts create inside an exact plugin root."""
    fixture = agent_source_fixture
    fixture.write_plugin(
        "domain-brain", skills={"records": {"SKILL.md": "# Records\n", "scripts/run.py": "print(1)\n"}}
    )
    _write_config(fixture, hosts=("claude", "codex", "cursor"), environment="personal")
    first = fixture.run("apply")
    assert first.returncode == 0, first.stderr
    cache = fixture.destination / MARKET / "claude/skills/records/scripts/__pycache__"
    cache.mkdir(parents=True)
    (cache / "x.pyc").write_bytes(b"bytecode")
    stray = fixture.destination / MARKET / "claude/skills/records/stray.txt"
    stray.write_text("unmanaged\n", encoding="utf-8")

    second = fixture.run("apply")
    assert second.returncode == 0, second.stderr
    assert (cache / "x.pyc").read_bytes() == b"bytecode"
    assert not stray.exists()
    diff = fixture.run("--no-pager", "diff")
    assert diff.returncode == 0, diff.stderr
    assert diff.stdout == ""


@pytest.mark.parametrize(
    ("interface", "expected"),
    [
        ({"displayName": "Fixture"}, ["email", "records"]),
        ({"displayName": "Fixture", "capabilities": ["Custom text"]}, ["Custom text"]),
    ],
)
def test_codex_capabilities_derive_from_selected_skills_unless_declared(agent_source_fixture, interface, expected):
    """An interface without capabilities lists the selected skills; declared capabilities stay as written."""
    fixture = agent_source_fixture
    fixture.write_plugin(
        "domain-brain",
        {"interface": interface},
        skills={"records": {"SKILL.md": "# Records\n"}, "email": {"SKILL.md": "# Email\n"}},
    )
    _write_config(fixture, hosts=("claude", "codex", "cursor"), environment="personal")
    result = fixture.run("apply")
    assert result.returncode == 0, result.stderr
    manifest = json.loads((fixture.destination / MANIFESTS["codex"]).read_text(encoding="utf-8"))
    assert manifest["interface"]["capabilities"] == expected
