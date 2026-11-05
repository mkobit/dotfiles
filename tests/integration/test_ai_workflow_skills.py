import re
import shutil
import tomllib
from pathlib import Path

import pytest
from test_ai_skills import (
    AUTHORED_SKILL_ROOTS,
    _apply_authored_cleanup,
    _initialize_authored_cleanup_source,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / "src/ai/skills"
WORKFLOW_SKILLS = ("sbx-sandboxes", "sbx-orchestrator", "worker-handoff")


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
    source, destination = tmp_path / "source", tmp_path / "destination"
    destination.mkdir()
    _initialize_authored_cleanup_source(source, include_external=True)
    gemini = source / "src/chezmoi/dot_gemini"
    gemini.mkdir()
    shutil.copy2(REPO_ROOT / "src/chezmoi/dot_gemini/.chezmoiremove.tmpl", gemini / ".chezmoiremove.tmpl")
    for name in skill_names:
        shutil.copytree(SKILLS_ROOT / name, source / "src/ai/skills" / name)
    config = tmp_path / "chezmoi.toml"

    def apply(states):
        config.write_text(
            "[data.ai.skills.authored]\n"
            + "".join(f'{name} = "{state}"\n' for name, state in states.items())
            + "[data.ai.skills.external]\n[data.ai.agents.external]\n"
            + '[data.local.bin.agy]\ninstallation_method = "preinstalled"\n'
        )
        result = _apply_authored_cleanup(source, destination, config)
        assert result.returncode == 0, result.stderr

    return source, destination, apply


@pytest.mark.parametrize(
    "skill_names",
    [WORKFLOW_SKILLS, ("architect-scoping",), (*WORKFLOW_SKILLS, "architect-scoping")],
    ids=["workflow", "architect", "combined"],
)
@pytest.mark.parametrize(
    ("selection", "expected_hosts"),
    [
        ("present", frozenset(AUTHORED_SKILL_ROOTS)),
        ("claude", frozenset({"claude"})),
        ("codex", frozenset({"codex"})),
        ("cursor", frozenset({"cursor", "cursor-local"})),
        ("antigravity", frozenset({"antigravity"})),
    ],
)
def test_workflow_skills_deploy_select_repeat_and_remove(tmp_path, selection, expected_hosts, skill_names):
    """Apply the real named trees, follow deployed links, and converge host selection and cleanup."""
    catalog = tomllib.loads((REPO_ROOT / "src/chezmoi/.chezmoidata/ai/skills/authored.toml").read_text())
    assert catalog["ai"]["skills"]["authored"]["worker-handoff"] == "present"
    assert (SKILLS_ROOT / "worker-handoff/SKILL.md").is_file()
    assert (SKILLS_ROOT / "worker-handoff/references/delivery.md").is_file()
    for name in skill_names:
        assert catalog["ai"]["skills"]["authored"][name] == "present"
        assert (SKILLS_ROOT / name / "SKILL.md").is_file()
        if name == "architect-scoping":
            _assert_local_links(SKILLS_ROOT / name)
    _, destination, apply_states = _workflow_fixture(tmp_path, skill_names)

    def apply(state):
        apply_states(dict.fromkeys(skill_names, state))

    # Install everywhere before narrowing so selection must also remove old copies.
    apply("present")
    apply(selection)
    installed = {}
    for host, relative in AUTHORED_SKILL_ROOTS.items():
        root = destination / relative
        for name in skill_names:
            deployed = root / name
            if host in expected_hosts:
                assert _tree_bytes(deployed) == _tree_bytes(SKILLS_ROOT / name)
                assert not deployed.is_symlink()
                assert not any(path.is_symlink() for path in deployed.rglob("*"))
            else:
                assert not deployed.exists()
        if host in expected_hosts:
            _assert_local_links(root)
            installed[host] = _tree_bytes(root)
    manifest = destination / ".cursor/plugins/local/mkobit-dotfiles/.cursor-plugin/plugin.json"
    manifest_bytes = manifest.read_bytes()
    apply(selection)
    for host in expected_hosts:
        assert _tree_bytes(destination / AUTHORED_SKILL_ROOTS[host]) == installed[host]
    assert manifest.read_bytes() == manifest_bytes

    sibling = destination / AUTHORED_SKILL_ROOTS["codex"] / "unmanaged/SKILL.md"
    sibling.parent.mkdir(parents=True)
    sibling.write_text("Keep this local skill.\n")
    for _ in range(2):
        apply("absent")
        for relative in AUTHORED_SKILL_ROOTS.values():
            for name in skill_names:
                assert not (destination / relative / name).exists()
        assert sibling.read_text() == "Keep this local skill.\n"


@pytest.mark.parametrize(
    ("worker_selection", "sbx_selected"),
    [
        ("absent", True),
        ("claude", True),
        ("codex", True),
        ("cursor", True),
        ("antigravity", True),
        ("present", False),
    ],
    ids=["worker-absent", "worker-claude", "worker-codex", "worker-cursor", "worker-antigravity", "worker-only"],
)
def test_workflow_skills_mixed_selection_preserves_links_and_partial_removal(tmp_path, worker_selection, sbx_selected):
    """Keep independent selections complete through partial cleanup and repeat apply."""
    source, destination, apply = _workflow_fixture(tmp_path)
    apply(dict.fromkeys(WORKFLOW_SKILLS, "present"))
    for relative in AUTHORED_SKILL_ROOTS.values():
        _assert_local_links(destination / relative)
        sibling = destination / relative / "unmanaged/SKILL.md"
        sibling.parent.mkdir()
        sibling.write_bytes(b"Keep this local skill.\n")
    unmanaged = destination / "unmanaged-state.json"
    unmanaged.write_bytes(b'{"keep": true}\n')
    states = {
        "sbx-sandboxes": "present" if sbx_selected else "absent",
        "sbx-orchestrator": "present" if sbx_selected else "absent",
        "worker-handoff": worker_selection,
    }
    apply(states)
    if not sbx_selected:
        # Remove installed copies with tombstones before testing an omitted SBX catalog.
        for relative in AUTHORED_SKILL_ROOTS.values():
            for name in WORKFLOW_SKILLS[:2]:
                assert not (destination / relative / name).exists()
        states = {"worker-handoff": worker_selection}
        for name in WORKFLOW_SKILLS[:2]:
            shutil.rmtree(source / "src/ai/skills" / name)
        apply(states)
    installed = {}
    for host, relative in AUTHORED_SKILL_ROOTS.items():
        root = destination / relative
        worker_selected = worker_selection == "present" or worker_selection == host.removesuffix("-local")
        for name in WORKFLOW_SKILLS:
            deployed = root / name
            if worker_selected if name == "worker-handoff" else sbx_selected:
                assert _tree_bytes(deployed) == _tree_bytes(SKILLS_ROOT / name)
                assert not any(path.is_symlink() for path in deployed.rglob("*"))
            else:
                assert not deployed.exists()
        _assert_local_links(root)
        assert (root / "unmanaged/SKILL.md").read_bytes() == b"Keep this local skill.\n"
        installed[host] = _tree_bytes(root)
    manifest = destination / ".cursor/plugins/local/mkobit-dotfiles/.cursor-plugin/plugin.json"
    manifest_bytes = manifest.read_bytes()
    apply(states)
    for host, relative in AUTHORED_SKILL_ROOTS.items():
        assert _tree_bytes(destination / relative) == installed[host]
        _assert_local_links(destination / relative)
    assert manifest.read_bytes() == manifest_bytes
    assert unmanaged.read_bytes() == b'{"keep": true}\n'


@pytest.mark.parametrize(
    ("architect_selection", "worker_selection"),
    [("present", "absent"), ("absent", "present"), ("claude", "codex"), ("codex", "claude")],
)
def test_architect_selection_preserves_independent_skills_and_state(tmp_path, architect_selection, worker_selection):
    """Converge independent architect and worker selections without changing unrelated copies."""
    skill_names = (*WORKFLOW_SKILLS, "architect-scoping")
    _, destination, apply = _workflow_fixture(tmp_path, skill_names)
    apply(dict.fromkeys(skill_names, "present"))
    for relative in AUTHORED_SKILL_ROOTS.values():
        sibling = destination / relative / "unmanaged/SKILL.md"
        sibling.parent.mkdir()
        sibling.write_bytes(b"Keep this local skill.\n")
    unmanaged = destination / "unmanaged-state.json"
    unmanaged.write_bytes(b'{"keep": true}\n')
    states = dict.fromkeys(WORKFLOW_SKILLS[:2], "present")
    states.update({"worker-handoff": worker_selection, "architect-scoping": architect_selection})
    apply(states)
    installed = {}
    for host, relative in AUTHORED_SKILL_ROOTS.items():
        root = destination / relative
        for name, selection in states.items():
            deployed = root / name
            if selection == "present" or selection == host.removesuffix("-local"):
                assert _tree_bytes(deployed) == _tree_bytes(SKILLS_ROOT / name)
                assert not deployed.is_symlink()
                assert not any(path.is_symlink() for path in deployed.rglob("*"))
            else:
                assert not deployed.exists()
        _assert_local_links(root)
        assert (root / "unmanaged/SKILL.md").read_bytes() == b"Keep this local skill.\n"
        installed[host] = _tree_bytes(root)
    manifest = destination / ".cursor/plugins/local/mkobit-dotfiles/.cursor-plugin/plugin.json"
    manifest_bytes = manifest.read_bytes()
    apply(states)
    for host, relative in AUTHORED_SKILL_ROOTS.items():
        assert _tree_bytes(destination / relative) == installed[host]
        _assert_local_links(destination / relative)
    assert manifest.read_bytes() == manifest_bytes
    assert unmanaged.read_bytes() == b'{"keep": true}\n'
