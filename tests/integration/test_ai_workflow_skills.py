import json
import re
import shutil
from pathlib import Path

import pytest
from test_ai_plugin_folders import (
    DEFAULT_HOSTS,
    MARKETPLACE,
    PLUGINS,
    SOURCE_ROOT,
    _chezmoi,
    _config,
    _fixture,
    _sources,
)

PLUGIN = PLUGINS / "exact_mkobit-dotfiles"
SKILLS_ROOT = SOURCE_ROOT / PLUGIN / "exact_skills"
WORKFLOW_SKILLS = ("sbx-sandboxes", "sbx-orchestrator", "worker-handoff")
DEPLOYED_PLUGIN = MARKETPLACE / "plugins/mkobit-dotfiles"
CURSOR_PLUGIN = Path(".cursor/plugins/local/mkobit-dotfiles")


def _tree_bytes(root: Path) -> dict[Path, bytes]:
    return {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def _assert_local_links(root: Path) -> None:
    for document in root.rglob("*.md"):
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text()):
            if "://" in target:
                continue
            filename, _, fragment = target.partition("#")
            resolved = (document.parent / filename).resolve() if filename else document.resolve()
            assert resolved.is_relative_to(root.resolve()), f"Link leaves deployed skills: {document}: {target}"
            assert resolved.is_file(), f"Broken link in {document}: {target}"
            if fragment:
                headings = re.findall(r"^#{1,6}\s+(.+)$", resolved.read_text(), re.MULTILINE)
                slugs = {re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-") for title in headings}
                assert fragment in slugs, f"Broken heading link in {document}: {target}"


def _workflow_fixture(tmp_path, skill_names=WORKFLOW_SKILLS):
    source, destination, config = _fixture(tmp_path)
    for name in ("alpha", "beta"):
        shutil.rmtree(source / PLUGINS / f"exact_{name}")
    for host in DEFAULT_HOSTS:
        relative = PLUGIN / f"exact_dot_{host}-plugin/plugin.json.tmpl"
        (source / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE_ROOT / relative, source / relative)
    relative = ".chezmoidata/ai/plugins/mkobit-dotfiles.toml"
    shutil.copy2(SOURCE_ROOT / relative, source / relative)
    for name in skill_names:
        shutil.copytree(SKILLS_ROOT / f"exact_{name}", source / PLUGIN / "exact_skills" / f"exact_{name}")

    def apply(states=None, *, hosts=DEFAULT_HOSTS, enabled=True):
        _config(
            config,
            extra="[data.ai.plugin_bridge.capabilities.mkobit-dotfiles]\n"
            f"hosts = {json.dumps(hosts)}\nenabled = {str(enabled).lower()}\n"
            "[data.ai.plugin_bridge.capabilities.mkobit-dotfiles.skills]\n"
            + "".join(f'{name} = "{state}"\n' for name, state in (states or {}).items()),
        )
        _chezmoi(source, destination, config, "diff")
        _chezmoi(source, destination, config, "apply")

    return source, destination, config, apply


def _assert_selection(source, destination, config, skill_names, states, hosts):
    """Use chezmoi's rendered bytes and native manifests to check both package copies."""
    shared = destination / DEPLOYED_PLUGIN
    for host, manifest in (
        ("claude", ".claude-plugin/marketplace.json"),
        ("codex", ".agents/plugins/marketplace.json"),
        ("cursor", ".cursor-plugin/marketplace.json"),
    ):
        assert ("mkobit-dotfiles" in _sources(destination, manifest)) == (host in hosts)
        assert (shared / f".{host}-plugin/plugin.json").is_file() == (host in hosts)
    rendered = {}
    for relative in (DEPLOYED_PLUGIN, CURSOR_PLUGIN):
        root = destination / relative / "skills"
        if relative == CURSOR_PLUGIN and "cursor" not in hosts:
            assert not root.parent.exists()
            continue
        for name in skill_names:
            deployed = root / name
            if states.get(name, "present") == "absent":
                assert not deployed.exists()
                continue
            if name not in rendered:
                managed = _chezmoi(
                    source, destination, config, "managed", "--path-style=absolute", str(shared / "skills" / name)
                )
                files = [Path(path) for path in managed.splitlines() if Path(path).is_file()]
                assert files
                rendered[name] = {
                    path.relative_to(shared / "skills" / name): _chezmoi(
                        source, destination, config, "cat", str(path)
                    ).encode()
                    for path in files
                }
            assert _tree_bytes(deployed) == rendered[name]
            assert not deployed.is_symlink()
            assert not any(path.is_symlink() for path in deployed.rglob("*"))
        _assert_local_links(root)


@pytest.mark.parametrize(
    "skill_names",
    [
        WORKFLOW_SKILLS,
        ("architect-scoping",),
        (*WORKFLOW_SKILLS, "architect-scoping"),
        ("repo-bootstrap",),
        (*WORKFLOW_SKILLS, "architect-scoping", "repo-bootstrap"),
    ],
    ids=["workflow", "architect", "combined", "bootstrap", "bootstrap-combined"],
)
@pytest.mark.parametrize("hosts", [DEFAULT_HOSTS, ("claude",), ("codex",), ("cursor",)])
def test_workflow_skills_deploy_select_repeat_and_remove(tmp_path, hosts, skill_names):
    """Apply real skill trees, narrow plugin hosts, then disable and restore the plugin."""
    source, destination, config, apply = _workflow_fixture(tmp_path, skill_names)
    apply()
    apply(hosts=hosts)
    _assert_selection(source, destination, config, skill_names, {}, hosts)
    installed = _tree_bytes(destination / DEPLOYED_PLUGIN)
    apply(hosts=hosts)
    assert _tree_bytes(destination / DEPLOYED_PLUGIN) == installed
    unrelated = destination / ".local/share/unmanaged/SKILL.md"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("Keep this local skill.\n")
    for _ in range(2):
        apply(hosts=hosts, enabled=False)
        assert not (destination / DEPLOYED_PLUGIN).exists()
        assert not (destination / CURSOR_PLUGIN).exists()
        assert unrelated.read_text() == "Keep this local skill.\n"
    apply(hosts=hosts)
    _assert_selection(source, destination, config, skill_names, {}, hosts)


@pytest.mark.parametrize(
    "absent",
    [("worker-handoff",), ("sbx-sandboxes", "sbx-orchestrator")],
    ids=["worker-absent", "worker-only"],
)
def test_workflow_skills_mixed_selection_preserves_links_and_partial_removal(tmp_path, absent):
    """Keep independently selected skills complete through partial cleanup and repeat apply."""
    source, destination, config, apply = _workflow_fixture(tmp_path)
    apply()
    unmanaged = destination / "unmanaged-state.json"
    unmanaged.write_bytes(b'{"keep": true}\n')
    states = dict.fromkeys(absent, "absent")
    apply(states)
    _assert_selection(source, destination, config, WORKFLOW_SKILLS, states, DEFAULT_HOSTS)
    installed = _tree_bytes(destination / DEPLOYED_PLUGIN)
    apply(states)
    assert _tree_bytes(destination / DEPLOYED_PLUGIN) == installed
    assert unmanaged.read_bytes() == b'{"keep": true}\n'
    # Restore selection, then let native exact_ cleanup remove deleted source skills.
    apply()
    _assert_selection(source, destination, config, WORKFLOW_SKILLS, {}, DEFAULT_HOSTS)
    for name in absent:
        shutil.rmtree(source / PLUGIN / "exact_skills" / f"exact_{name}")
    apply()
    _assert_selection(source, destination, config, WORKFLOW_SKILLS, states, DEFAULT_HOSTS)


@pytest.mark.parametrize("independent_skill", ["architect-scoping", "repo-bootstrap"], ids=["architect", "bootstrap"])
@pytest.mark.parametrize("absent", ["independent", "worker"])
def test_independent_selection_preserves_skills_and_state(tmp_path, independent_skill, absent):
    """Per-skill present/absent decisions preserve unrelated skills and state."""
    skill_names = (*WORKFLOW_SKILLS, independent_skill)
    source, destination, config, apply = _workflow_fixture(tmp_path, skill_names)
    apply()
    baseline = _tree_bytes(destination / DEPLOYED_PLUGIN / "skills")
    unmanaged = destination / "unmanaged-state.json"
    unmanaged.write_bytes(b'{"keep": true}\n')
    absent_name = independent_skill if absent == "independent" else "worker-handoff"
    states = {name: "absent" if name == absent_name else "present" for name in skill_names}
    for _ in range(2):
        apply(states)
        _assert_selection(source, destination, config, skill_names, states, DEFAULT_HOSTS)
        for name in set(skill_names) - {absent_name}:
            expected = {path.relative_to(name): content for path, content in baseline.items() if path.parts[0] == name}
            assert _tree_bytes(destination / DEPLOYED_PLUGIN / "skills" / name) == expected
        assert unmanaged.read_bytes() == b'{"keep": true}\n'
