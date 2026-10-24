"""Integration coverage for authored overlay capability skill projection."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AUTHORED_CAPABILITIES_EXTERNAL = REPOSITORY_ROOT / "src/chezmoi/.chezmoiexternals/ai-authored-capabilities.toml.tmpl"
CAPABILITIES_CLEANUP = (
    REPOSITORY_ROOT
    / "src/chezmoi/.chezmoiscripts/run_onchange_after_00-agent-plugin-authored-capabilities-cleanup.sh.tmpl"
)
FILTER_INTERPRETER_TEMPLATE = REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/python/filter-interpreter"
FILTER_INTERPRETER_RESOLVER = REPOSITORY_ROOT / "src/python/skill_filter/resolve-interpreter.sh"
AUTHORED_TEMPLATE_ROOT = REPOSITORY_ROOT / "src/chezmoi/.chezmoitemplates/ai"


def _add_plugin_wrappers(source: Path) -> None:
    """Add the thin package manifests that accompany external-projected skills."""
    manifest_template = source / ".chezmoitemplates/ai/authored-plugin-manifest"
    manifest_template.parent.mkdir(parents=True, exist_ok=True)
    manifest_template.write_text(
        '{{- define "ai/authored-plugin-manifest" -}}'
        '{"name":"{{ .name }}","version":"1.0.0","skills":"./skills"}'
        "{{- end -}}\n",
        encoding="utf-8",
    )
    wrappers = {
        "dot_local/share/agent-plugins/marketplace/plugins/domain-brain/exact_claude/"
        "exact_dot_claude-plugin/plugin.json.tmpl": '{{ includeTemplate "ai/authored-plugin-manifest" (dict "root" . "name" "domain-brain") }}\n',
        "dot_local/share/agent-plugins/marketplace/plugins/domain-brain/exact_codex/"
        "exact_dot_codex-plugin/plugin.json.tmpl": (
            '{{- $manifest := includeTemplate "ai/authored-plugin-manifest" '
            '(dict "root" . "name" "domain-brain") | fromJson -}}\n'
            '{{- $_ := set $manifest "author" (dict "name" "Local developer") -}}\n'
            "{{- $manifest | toPrettyJson -}}\n"
        ),
        "dot_local/share/agent-plugins/marketplace/plugins/domain-brain/exact_cursor/"
        "exact_dot_cursor-plugin/plugin.json.tmpl": '{{ includeTemplate "ai/authored-plugin-manifest" (dict "root" . "name" "domain-brain") }}\n',
        "dot_cursor/plugins/local/domain-brain/exact_dot_cursor-plugin/plugin.json.tmpl": '{{ includeTemplate "ai/authored-plugin-manifest" (dict "root" . "name" "domain-brain") }}\n',
    }
    for relative_path, contents in wrappers.items():
        wrapper = source / relative_path
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        wrapper.write_text(contents, encoding="utf-8")


def _add_stripe_dotfiles_wrappers(source: Path) -> None:
    """Add thin Stripe manifests without adding skill payloads to wrapper trees."""
    manifest_template = source / ".chezmoitemplates/ai/authored-plugin-manifest"
    manifest_template.parent.mkdir(parents=True, exist_ok=True)
    manifest_template.write_text(
        '{{- define "ai/authored-plugin-manifest" -}}'
        '{"name":"{{ .name }}","version":"1.0.0","skills":"./skills"}'
        "{{- end -}}\n",
        encoding="utf-8",
    )
    wrappers = {
        "dot_local/share/agent-plugins/marketplace/plugins/stripe-dotfiles/exact_claude/"
        "exact_dot_claude-plugin/plugin.json.tmpl": '{{ includeTemplate "ai/authored-plugin-manifest" (dict "root" . "name" "stripe-dotfiles") }}\n',
        "dot_local/share/agent-plugins/marketplace/plugins/stripe-dotfiles/exact_codex/"
        "exact_dot_codex-plugin/plugin.json.tmpl": (
            '{{- $manifest := includeTemplate "ai/authored-plugin-manifest" '
            '(dict "root" . "name" "stripe-dotfiles") | fromJson -}}\n'
            '{{- $_ := set $manifest "author" (dict "name" "Local developer") -}}\n'
            "{{- $manifest | toPrettyJson -}}\n"
        ),
        "dot_local/share/agent-plugins/marketplace/plugins/stripe-dotfiles/exact_cursor/"
        "exact_dot_cursor-plugin/plugin.json.tmpl": '{{ includeTemplate "ai/authored-plugin-manifest" (dict "root" . "name" "stripe-dotfiles") }}\n',
        "dot_cursor/plugins/local/stripe-dotfiles/exact_dot_cursor-plugin/plugin.json.tmpl": '{{ includeTemplate "ai/authored-plugin-manifest" (dict "root" . "name" "stripe-dotfiles") }}\n',
    }
    for relative_path, contents in wrappers.items():
        wrapper = source / relative_path
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        wrapper.write_text(contents, encoding="utf-8")


def _add_cleanup_script(source: Path) -> None:
    """Install the shared cleanup runner and its interpreter resolver into a fixture source."""
    files = {
        CAPABILITIES_CLEANUP: Path(".chezmoiscripts") / CAPABILITIES_CLEANUP.name,
        FILTER_INTERPRETER_TEMPLATE: Path(".chezmoitemplates/python/filter-interpreter"),
        FILTER_INTERPRETER_RESOLVER: Path("../python/skill_filter/resolve-interpreter.sh"),
    }
    for origin, relative_path in files.items():
        assert origin.is_file(), f"cleanup fixture dependency is missing: {origin}"
        target = source / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, target)


def _apply(source: Path, destination: Path, config: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "chezmoi",
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--config",
            str(config),
            "--persistent-state",
            str(config.with_suffix(".boltdb")),
            "--refresh-externals=always",
            "apply",
        ],
        capture_output=True,
        check=False,
        cwd=destination.parent,
        env={
            **os.environ,
            "XDG_CACHE_HOME": str(config.parent / "cache"),
            "XDG_CONFIG_HOME": str(config.parent / "config"),
            "XDG_DATA_HOME": str(config.parent / "data"),
            "XDG_STATE_HOME": str(config.parent / "state"),
        },
        text=True,
    )


def _write_capability_config(
    config: Path,
    *,
    hosts: tuple[str, ...] = ("claude", "codex", "cursor"),
    state: str = "present",
    declared: bool = True,
) -> None:
    if not declared:
        config.write_text("[data.ai.skills]\n", encoding="utf-8")
        return
    config.write_text(
        "\n".join(
            [
                "[data.ai.skills]",
                "",
                "[data.ai.plugin_bridge.capabilities.domain-brain]",
                'source_dir = "src/overlay-plugins/domain-brain"',
                f"hosts = {json.dumps(hosts)}",
                "",
                "[data.ai.plugin_bridge.capabilities.domain-brain.skills]",
                f'records = "{state}"',
                "",
            ]
        ),
        encoding="utf-8",
    )


def _capability_skill_roots(destination: Path) -> tuple[Path, ...]:
    package_root = destination / ".local/share/agent-plugins/marketplace/plugins/domain-brain"
    return (
        *(package_root / host / "skills/records" for host in ("claude", "codex", "cursor")),
        destination / ".cursor/plugins/local/domain-brain/skills/records",
    )


def _initialize_capability_lifecycle_source(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    overlay_root = tmp_path / "overlay"
    source = overlay_root / ".chezmoiroot.assembled/chezmoi"
    destination = tmp_path / "destination"
    destination.mkdir()
    external_dir = source / ".chezmoiexternals"
    external_dir.mkdir(parents=True)
    shutil.copy2(AUTHORED_CAPABILITIES_EXTERNAL, external_dir / AUTHORED_CAPABILITIES_EXTERNAL.name)
    for name in ("authored-render-context", "authored-file-entry", "authored-file-digest"):
        target = source / ".chezmoitemplates/ai" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(AUTHORED_TEMPLATE_ROOT / name, target)
    _add_cleanup_script(source)
    subprocess.run(["git", "init", "--quiet", str(source)], check=True)

    skill_source = source.parent / "overlay-plugins/domain-brain/skills/records"
    (skill_source / "references").mkdir(parents=True)
    (skill_source / "SKILL.md").write_text("# Records\n", encoding="utf-8")
    (skill_source / "references/record-contract.md").write_text("contract\n", encoding="utf-8")
    config = tmp_path / "chezmoi.toml"
    return source, destination, config, skill_source


@pytest.mark.parametrize(
    ("state", "source_dir", "expected_hosts"),
    [
        ("present", "src/overlay-plugins/domain-brain", frozenset({"claude", "codex", "cursor"})),
        ("codex", "src/overlay-plugins/domain-brain", frozenset({"codex"})),
        ("present", "src/custom-support/domain-brain", frozenset({"claude", "codex", "cursor"})),
    ],
)
def test_capability_projects_canonical_domain_brain_skill_tree_to_selected_hosts(
    tmp_path, state, source_dir, expected_hosts
):
    """An overlay capability projects one canonical skill tree to every selected host package."""
    overlay_root = tmp_path / "overlay"
    source = overlay_root / ".chezmoiroot.assembled/chezmoi"
    destination = tmp_path / "destination"
    destination.mkdir()
    external_dir = source / ".chezmoiexternals"
    external_dir.mkdir(parents=True)
    assert AUTHORED_CAPABILITIES_EXTERNAL.is_file(), "authored capability external is missing"
    shutil.copy2(AUTHORED_CAPABILITIES_EXTERNAL, external_dir / AUTHORED_CAPABILITIES_EXTERNAL.name)
    for name in ("authored-render-context", "authored-file-entry", "authored-file-digest"):
        target = source / ".chezmoitemplates/ai" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(AUTHORED_TEMPLATE_ROOT / name, target)
    _add_plugin_wrappers(source)
    subprocess.run(["git", "init", "--quiet", str(source)], check=True)

    records = source.parent / source_dir.removeprefix("src/") / "skills/records"
    (records / "references").mkdir(parents=True)
    (records / "SKILL.md").write_text("# Records\n", encoding="utf-8")
    (records / "references/record-contract.md").write_text("contract\n", encoding="utf-8")

    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.plugin_bridge.capabilities.domain-brain]",
                f"source_dir = {json.dumps(source_dir)}",
                'hosts = ["claude", "codex", "cursor"]',
                "",
                "[data.ai.plugin_bridge.capabilities.domain-brain.skills]",
                f'records = "{state}"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = _apply(source, destination, config)

    assert result.returncode == 0, result.stderr
    package_roots = {
        host: (destination / ".local/share/agent-plugins/marketplace/plugins/domain-brain" / host / "skills/records")
        for host in ("claude", "codex", "cursor")
    }
    package_roots["cursor-local"] = destination / ".cursor/plugins/local/domain-brain/skills/records"
    expected_roots = {host: host in expected_hosts for host in package_roots}
    expected_roots["cursor-local"] = "cursor" in expected_hosts
    for host, skill_root in package_roots.items():
        skill_file = skill_root / "SKILL.md"
        assert skill_file.exists() is expected_roots[host]
        if expected_roots[host]:
            assert skill_file.read_text(encoding="utf-8") == "# Records\n"
            assert (skill_root / "references/record-contract.md").read_text(encoding="utf-8") == "contract\n"

    for manifest in (
        destination / ".local/share/agent-plugins/marketplace/plugins/domain-brain/claude/.claude-plugin/plugin.json",
        destination / ".local/share/agent-plugins/marketplace/plugins/domain-brain/codex/.codex-plugin/plugin.json",
        destination / ".local/share/agent-plugins/marketplace/plugins/domain-brain/cursor/.cursor-plugin/plugin.json",
        destination / ".cursor/plugins/local/domain-brain/.cursor-plugin/plugin.json",
    ):
        assert json.loads(manifest.read_text(encoding="utf-8"))["skills"] == "./skills"


def test_capability_projects_stripe_direct_skill_root_and_removes_remote_only_skill(tmp_path):
    """A direct canonical root projects selected Stripe skills and removes remote-only content."""
    overlay_root = tmp_path / "overlay"
    source = overlay_root / ".chezmoiroot.assembled/chezmoi"
    destination = tmp_path / "destination"
    destination.mkdir()
    external_dir = source / ".chezmoiexternals"
    external_dir.mkdir(parents=True)
    shutil.copy2(AUTHORED_CAPABILITIES_EXTERNAL, external_dir / AUTHORED_CAPABILITIES_EXTERNAL.name)
    for name in ("authored-render-context", "authored-file-entry", "authored-file-digest"):
        target = source / ".chezmoitemplates/ai" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(AUTHORED_TEMPLATE_ROOT / name, target)
    _add_cleanup_script(source)
    _add_stripe_dotfiles_wrappers(source)
    subprocess.run(["git", "init", "--quiet", str(source)], check=True)

    skill_names = ("domain-projects", "jira-format-content", "jira-slack-to-jira", "writing")
    for skill_name in skill_names:
        skill_source = source.parent / "overlay-skills" / skill_name
        skill_source.mkdir(parents=True)
        (skill_source / "SKILL.md").write_text(f"# {skill_name}\n", encoding="utf-8")

    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.plugin_bridge.capabilities.stripe-dotfiles]",
                'source_dir = "src/overlay-plugins/stripe-dotfiles"',
                'skills_source_dir = "src/overlay-skills"',
                'hosts = ["claude", "codex", "cursor"]',
                "",
                "[data.ai.plugin_bridge.capabilities.stripe-dotfiles.skills]",
                *[f'{skill_name} = "present"' for skill_name in skill_names],
                "",
            ]
        ),
        encoding="utf-8",
    )

    local_apply = _apply(source, destination, config)

    assert local_apply.returncode == 0, local_apply.stderr
    roots = (
        *(
            destination / ".local/share/agent-plugins/marketplace/plugins/stripe-dotfiles" / host / "skills"
            for host in ("claude", "codex", "cursor")
        ),
        destination / ".cursor/plugins/local/stripe-dotfiles/skills",
    )
    for root in roots:
        for skill_name in skill_names:
            assert (root / skill_name / "SKILL.md").read_text(encoding="utf-8") == f"# {skill_name}\n"

    config.write_text(
        config.read_text(encoding="utf-8").replace('jira-slack-to-jira = "present"', 'jira-slack-to-jira = "absent"'),
        encoding="utf-8",
    )
    remote_apply = _apply(source, destination, config)

    assert remote_apply.returncode == 0, remote_apply.stderr
    for root in roots:
        assert not (root / "jira-slack-to-jira").exists()
        for skill_name in ("domain-projects", "jira-format-content", "writing"):
            assert (root / skill_name / "SKILL.md").is_file()


def test_authored_plugin_manifest_supports_direct_skill_root_and_default_skill_layout(tmp_path):
    """Explicit skill roots render alongside capabilities that use the default skills directory."""
    overlay_root = tmp_path / "overlay"
    source = overlay_root / ".chezmoiroot.assembled/chezmoi"
    destination = tmp_path / "destination"
    destination.mkdir()
    template_root = source / ".chezmoitemplates/ai"
    template_root.mkdir(parents=True)
    for template_name in (
        "authored-plugin-manifest",
        "authored-plugins",
        "authored-file-digest",
        "authored-render-context",
    ):
        shutil.copy2(AUTHORED_TEMPLATE_ROOT / template_name, template_root / template_name)
    (source / "dot_local/share/stripe-plugin.json.tmpl").parent.mkdir(parents=True)
    (source / "dot_local/share/stripe-plugin.json.tmpl").write_text(
        '{{ includeTemplate "ai/authored-plugin-manifest" (dict "root" . "name" "stripe-dotfiles") }}\n',
        encoding="utf-8",
    )
    (source / "dot_local/share/domain-plugin.json.tmpl").write_text(
        '{{ includeTemplate "ai/authored-plugin-manifest" (dict "root" . "name" "domain-brain") }}\n',
        encoding="utf-8",
    )
    assembled_root = source.parent
    (assembled_root / "overlay-plugins/stripe-dotfiles/wrappers").mkdir(parents=True)
    (assembled_root / "overlay-plugins/stripe-dotfiles/wrappers/plugin.json.tmpl").write_text(
        "wrapper\n", encoding="utf-8"
    )
    (assembled_root / "overlay-skills/writing").mkdir(parents=True)
    (assembled_root / "overlay-skills/writing/SKILL.md").write_text("# Writing\n", encoding="utf-8")
    (assembled_root / "overlay-plugins/domain-brain/skills/records").mkdir(parents=True)
    (assembled_root / "overlay-plugins/domain-brain/skills/records/SKILL.md").write_text(
        "# Records\n", encoding="utf-8"
    )
    subprocess.run(["git", "init", "--quiet", str(overlay_root)], check=True)

    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.plugin_bridge.capabilities.stripe-dotfiles]",
                'description = "Stripe dotfiles capability bundle."',
                'source_dir = "src/overlay-plugins/stripe-dotfiles"',
                'skills_source_dir = "src/overlay-skills"',
                'hosts = ["claude"]',
                "",
                "[data.ai.plugin_bridge.capabilities.stripe-dotfiles.skills]",
                'writing = "present"',
                "",
                "[data.ai.plugin_bridge.capabilities.domain-brain]",
                'description = "Domain Intelligence workflows."',
                'source_dir = "src/overlay-plugins/domain-brain"',
                'hosts = ["claude"]',
                "",
                "[data.ai.plugin_bridge.capabilities.domain-brain.skills]",
                'records = "present"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = _apply(source, destination, config)

    assert result.returncode == 0, result.stderr
    assert (
        json.loads((destination / ".local/share/stripe-plugin.json").read_text(encoding="utf-8"))["name"]
        == "stripe-dotfiles"
    )
    assert (
        json.loads((destination / ".local/share/domain-plugin.json").read_text(encoding="utf-8"))["name"]
        == "domain-brain"
    )


def test_capability_cleanup_removes_deleted_canonical_source_files_and_preserves_siblings(tmp_path):
    """A deleted canonical file is removed from every owned projection without pruning sibling content."""
    source, destination, config, skill_source = _initialize_capability_lifecycle_source(tmp_path)
    _write_capability_config(config)

    first_apply = _apply(source, destination, config)
    assert first_apply.returncode == 0, first_apply.stderr
    sibling = _capability_skill_roots(destination)[0] / "local-notes.md"
    sibling.write_text("keep\n", encoding="utf-8")

    (skill_source / "references/record-contract.md").unlink()
    second_apply = _apply(source, destination, config)

    assert second_apply.returncode == 0, second_apply.stderr
    for skill_root in _capability_skill_roots(destination):
        assert not (skill_root / "references/record-contract.md").exists()
    assert sibling.read_text(encoding="utf-8") == "keep\n"


def test_capability_cleanup_removes_deselected_cursor_hosts_and_preserves_siblings(tmp_path):
    """Removing Cursor from capability hosts clears both Cursor projections and preserves unrelated files."""
    source, destination, config, _ = _initialize_capability_lifecycle_source(tmp_path)
    _write_capability_config(config)

    first_apply = _apply(source, destination, config)
    assert first_apply.returncode == 0, first_apply.stderr
    cursor_package, cursor_local = _capability_skill_roots(destination)[2:]
    sibling = cursor_package / "local-notes.md"
    sibling.write_text("keep\n", encoding="utf-8")

    _write_capability_config(config, hosts=("claude", "codex"))
    second_apply = _apply(source, destination, config)

    assert second_apply.returncode == 0, second_apply.stderr
    assert not (cursor_package / "SKILL.md").exists()
    assert not (cursor_local / "SKILL.md").exists()
    assert sibling.read_text(encoding="utf-8") == "keep\n"
    for skill_root in _capability_skill_roots(destination)[:2]:
        assert (skill_root / "SKILL.md").is_file()


def test_capability_cleanup_removes_disabled_skill_and_preserves_siblings(tmp_path):
    """Changing a capability skill from present to absent removes only its owned files."""
    source, destination, config, _ = _initialize_capability_lifecycle_source(tmp_path)
    _write_capability_config(config)

    first_apply = _apply(source, destination, config)
    assert first_apply.returncode == 0, first_apply.stderr
    sibling = _capability_skill_roots(destination)[0] / "local-notes.md"
    sibling.write_text("keep\n", encoding="utf-8")

    _write_capability_config(config, state="absent")
    second_apply = _apply(source, destination, config)

    assert second_apply.returncode == 0, second_apply.stderr
    for skill_root in _capability_skill_roots(destination):
        assert not (skill_root / "SKILL.md").exists()
    assert sibling.read_text(encoding="utf-8") == "keep\n"


def test_capability_cleanup_removes_deleted_capability_and_preserves_siblings(tmp_path):
    """Deleting a capability declaration removes files recorded as capability-owned only."""
    source, destination, config, _ = _initialize_capability_lifecycle_source(tmp_path)
    _write_capability_config(config)

    first_apply = _apply(source, destination, config)
    assert first_apply.returncode == 0, first_apply.stderr
    sibling = _capability_skill_roots(destination)[0] / "local-notes.md"
    sibling.write_text("keep\n", encoding="utf-8")

    _write_capability_config(config, declared=False)
    second_apply = _apply(source, destination, config)

    assert second_apply.returncode == 0, second_apply.stderr
    for skill_root in _capability_skill_roots(destination):
        assert not (skill_root / "SKILL.md").exists()
    assert sibling.read_text(encoding="utf-8") == "keep\n"


@pytest.mark.parametrize(
    ("capability_name", "source_dir", "skills_source_dir", "skill_name", "expected_error"),
    [
        ("../domain-brain", "src/overlay-plugins/domain-brain", None, "records", "invalid capability name"),
        ("domain-brain", "src/overlay-plugins/domain-brain", None, "../records", "invalid skill name"),
        ("domain-brain", "src/custom-support/../outside", None, "records", "invalid source_dir"),
        (
            "domain-brain",
            "src/overlay-plugins/domain-brain",
            "src/overlay-skills/../outside",
            "records",
            "invalid skills_source_dir",
        ),
    ],
)
def test_capability_rejects_paths_outside_the_declared_overlay_schema(
    tmp_path, capability_name, source_dir, skills_source_dir, skill_name, expected_error
):
    """Capability identifiers and source directories cannot become path traversal inputs."""
    overlay_root = tmp_path / "overlay"
    source = overlay_root / ".chezmoiroot.assembled/chezmoi"
    destination = tmp_path / "destination"
    destination.mkdir()
    external_dir = source / ".chezmoiexternals"
    external_dir.mkdir(parents=True)
    shutil.copy2(AUTHORED_CAPABILITIES_EXTERNAL, external_dir / AUTHORED_CAPABILITIES_EXTERNAL.name)
    for name in ("authored-render-context", "authored-file-entry", "authored-file-digest"):
        target = source / ".chezmoitemplates/ai" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(AUTHORED_TEMPLATE_ROOT / name, target)
    subprocess.run(["git", "init", "--quiet", str(source)], check=True)

    capability_key = json.dumps(capability_name)
    config = tmp_path / "chezmoi.toml"
    capability_lines = [
        f"[data.ai.plugin_bridge.capabilities.{capability_key}]",
        f"source_dir = {json.dumps(source_dir)}",
    ]
    if skills_source_dir is not None:
        capability_lines.append(f"skills_source_dir = {json.dumps(skills_source_dir)}")
    config.write_text(
        "\n".join(
            [
                *capability_lines,
                'hosts = ["claude"]',
                "",
                f"[data.ai.plugin_bridge.capabilities.{capability_key}.skills]",
                f'{json.dumps(skill_name)} = "present"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = _apply(source, destination, config)

    assert result.returncode != 0
    assert expected_error in result.stderr


def test_capability_rejects_a_selected_skill_without_skill_markdown(tmp_path):
    """A source folder with references but no SKILL.md cannot become a deployed skill."""
    overlay_root = tmp_path / "overlay"
    source = overlay_root / ".chezmoiroot.assembled/chezmoi"
    destination = tmp_path / "destination"
    destination.mkdir()
    external_dir = source / ".chezmoiexternals"
    external_dir.mkdir(parents=True)
    shutil.copy2(AUTHORED_CAPABILITIES_EXTERNAL, external_dir / AUTHORED_CAPABILITIES_EXTERNAL.name)
    for name in ("authored-render-context", "authored-file-entry", "authored-file-digest"):
        target = source / ".chezmoitemplates/ai" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(AUTHORED_TEMPLATE_ROOT / name, target)
    subprocess.run(["git", "init", "--quiet", str(source)], check=True)

    references = source.parent / "custom-support/domain-brain/skills/records/references"
    references.mkdir(parents=True)
    (references / "record-contract.md").write_text("contract\n", encoding="utf-8")

    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.plugin_bridge.capabilities.domain-brain]",
                'source_dir = "src/custom-support/domain-brain"',
                'hosts = ["codex"]',
                "",
                "[data.ai.plugin_bridge.capabilities.domain-brain.skills]",
                'records = "codex"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = _apply(source, destination, config)

    assert result.returncode != 0
    assert "missing SKILL.md" in result.stderr


@pytest.mark.parametrize(
    ("hosts", "expected_error"),
    [
        ([], "must declare at least one host"),
        (["claude", "opencode"], 'unknown host "opencode"'),
    ],
)
def test_capability_rejects_empty_or_unknown_hosts(tmp_path, hosts, expected_error):
    """Capability host declarations must select at least one supported package host."""
    overlay_root = tmp_path / "overlay"
    source = overlay_root / ".chezmoiroot.assembled/chezmoi"
    destination = tmp_path / "destination"
    destination.mkdir()
    external_dir = source / ".chezmoiexternals"
    external_dir.mkdir(parents=True)
    shutil.copy2(AUTHORED_CAPABILITIES_EXTERNAL, external_dir / AUTHORED_CAPABILITIES_EXTERNAL.name)
    for name in ("authored-render-context", "authored-file-entry", "authored-file-digest"):
        target = source / ".chezmoitemplates/ai" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(AUTHORED_TEMPLATE_ROOT / name, target)
    subprocess.run(["git", "init", "--quiet", str(source)], check=True)

    config = tmp_path / "chezmoi.toml"
    config.write_text(
        "\n".join(
            [
                "[data.ai.plugin_bridge.capabilities.domain-brain]",
                'source_dir = "src/overlay-plugins/domain-brain"',
                f"hosts = {json.dumps(hosts)}",
                "",
                "[data.ai.plugin_bridge.capabilities.domain-brain.skills]",
                'records = "absent"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = _apply(source, destination, config)

    assert result.returncode != 0
    assert expected_error in result.stderr


def _initialize_wrapper_source(tmp_path: Path, *, with_skills: bool = True):
    """Build complete packages through real externals, template filters, and cleanup."""
    source, destination, config, skill_source = _initialize_capability_lifecycle_source(tmp_path)
    for origin in AUTHORED_TEMPLATE_ROOT.glob("authored-*"):
        shutil.copy2(origin, source / ".chezmoitemplates/ai" / origin.name)
    for origin in AUTHORED_CAPABILITIES_EXTERNAL.parent.glob("ai-authored-wrappers*"):
        shutil.copy2(origin, source / ".chezmoiexternals" / origin.name)
    wrappers = skill_source.parents[1] / "wrappers"
    for host in ("claude", "codex", "cursor"):
        manifest = wrappers / host / f".{host}-plugin/plugin.json.tmpl"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            '{{ includeTemplate "ai/authored-plugin-manifest" (dict "root" . "name" "domain-brain") }}\n',
            encoding="utf-8",
        )
        support = wrappers / host / ".support.json.tmpl"
        support.write_text('{"label":{{ .fixture.label | toJson }}}\n', encoding="utf-8")
        executable = wrappers / host / "scripts/check.sh.tmpl"
        executable.parent.mkdir()
        executable.write_text('#!/bin/sh\nprintf "%s\\n" {{ .fixture.label | shellQuote }}\n', encoding="utf-8")
        executable.chmod(0o755)
        (wrappers / host / "payload.bin").write_bytes(b"\x00\xff\xfe\x80\n")
        (wrappers / host / "dot_literal.tmpl.tmpl").write_text("literal\n", encoding="utf-8")
    (wrappers.parent / "README.md").write_text("source only\n", encoding="utf-8")
    _write_wrapper_config(config, with_skills=with_skills)
    return source, destination, config, wrappers


def _write_wrapper_config(
    config, *, hosts=("claude", "codex", "cursor"), label="first", environment="enabled", with_skills=True
):
    lines = [
        "[data.fixture]",
        f"label = {json.dumps(label)}",
        "[data.ai.plugin_bridge]",
        f"environment = {json.dumps(environment)}",
        "[data.ai.plugin_bridge.capabilities.domain-brain]",
        'description = "Fixture capability"',
        'wrapper_source_dir = "src/overlay-plugins/domain-brain/wrappers"',
        f"hosts = {json.dumps(hosts)}",
        'environments = ["enabled"]',
    ]
    if with_skills:
        lines.extend(
            [
                'source_dir = "src/overlay-plugins/domain-brain"',
                "[data.ai.plugin_bridge.capabilities.domain-brain.skills]",
                'records = "present"',
            ]
        )
    config.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _wrapper_roots(destination):
    return (
        *(
            destination / ".local/share/agent-plugins/marketplace/plugins/domain-brain" / host
            for host in ("claude", "codex", "cursor")
        ),
        destination / ".cursor/plugins/local/domain-brain",
    )


@pytest.mark.parametrize("with_skills", [True, False])
def test_canonical_wrappers_render_complete_literal_packages(tmp_path, with_skills):
    """Missing wrapper delivery must fail before a native manifest or its support can be consumed."""
    source, destination, config, _ = _initialize_wrapper_source(tmp_path, with_skills=with_skills)
    result = _apply(source, destination, config)
    assert result.returncode == 0, result.stderr
    for host, root in zip(("claude", "codex", "cursor", "cursor"), _wrapper_roots(destination), strict=True):
        manifest = root / f".{host}-plugin/plugin.json"
        assert manifest.is_file(), f"canonical manifest was not delivered: {manifest}"
        decoded = json.loads(manifest.read_text())
        assert decoded["name"] == "domain-brain"
        assert ("skills" in decoded) is with_skills
        assert (root / ".support.json").read_text() == '{"label":"first"}\n'
        assert (root / "payload.bin").read_bytes() == b"\x00\xff\xfe\x80\n"
        script = root / "scripts/check.sh"
        assert script.stat().st_mode & 0o777 == 0o755
        assert subprocess.check_output([str(script)], text=True) == "first\n"
        assert (root / "dot_literal.tmpl").read_text() == "literal\n"
        assert not (root / "README.md").exists()
        assert (root / "skills/records/SKILL.md").exists() is with_skills


def test_canonical_wrapper_versions_follow_rendered_data_modes_and_manifest_sources(tmp_path):
    """Unchanged inputs must be stable while changed output content, modes, and manifest code invalidate versions."""
    source, destination, config, wrappers = _initialize_wrapper_source(tmp_path)
    manifest = _wrapper_roots(destination)[0] / ".claude-plugin/plugin.json"

    def version():
        result = _apply(source, destination, config)
        assert result.returncode == 0, result.stderr
        assert manifest.is_file(), "canonical manifest was not delivered"
        return json.loads(manifest.read_text())["version"]

    first = version()
    assert version() == first
    _write_wrapper_config(config, label="second")
    second = version()
    assert second != first
    assert (_wrapper_roots(destination)[0] / ".support.json").read_text() == '{"label":"second"}\n'
    (wrappers / "claude/payload.bin").chmod(0o755)
    mode_changed = version()
    assert mode_changed != second
    generated = wrappers / "claude/.claude-plugin/plugin.json.tmpl"
    generated.write_text(generated.read_text() + "\n")
    manifest_changed = version()
    assert manifest_changed != mode_changed
    relocated = tmp_path / "relocated"
    shutil.copytree(source.parent, relocated)
    result = _apply(relocated / "chezmoi", destination, config)
    assert result.returncode == 0, result.stderr
    assert json.loads(manifest.read_text())["version"] == manifest_changed


@pytest.mark.parametrize("change", ["support_removed", "host_removed", "environment_disabled", "declaration_removed"])
def test_canonical_wrapper_cleanup_removes_only_owned_files(tmp_path, change):
    """Stale support and disabled wrappers must disappear without removing unknown package files."""
    source, destination, config, wrappers = _initialize_wrapper_source(tmp_path)
    result = _apply(source, destination, config)
    assert result.returncode == 0, result.stderr
    roots = _wrapper_roots(destination)
    assert (roots[2] / ".support.json").is_file(), "canonical support was not delivered"
    unknown = roots[2] / "scripts/unknown.txt"
    unknown.write_text("keep\n")
    if change == "support_removed":
        for host in ("claude", "codex", "cursor"):
            (wrappers / host / ".support.json.tmpl").unlink()
    elif change == "host_removed":
        _write_wrapper_config(config, hosts=("claude", "codex"))
    elif change == "environment_disabled":
        _write_wrapper_config(config, environment="disabled")
    else:
        config.write_text("[data.ai.skills]\n")
    result = _apply(source, destination, config)
    assert result.returncode == 0, result.stderr
    assert unknown.read_text() == "keep\n"
    for index, root in enumerate(roots):
        assert (root / ".support.json").exists() is (change == "host_removed" and index < 2)
        if change != "support_removed" and (change != "host_removed" or index >= 2):
            assert not (root / "payload.bin").exists()
    repeated = _apply(source, destination, config)
    assert repeated.returncode == 0, repeated.stderr
    assert unknown.read_text() == "keep\n"


@pytest.mark.parametrize("inactive", ["host", "environment"])
def test_canonical_wrappers_gate_inactive_templates_before_rendering(tmp_path, inactive):
    """An inactive wrapper that requires missing data must not enter the renderer."""
    source, destination, config, wrappers = _initialize_wrapper_source(tmp_path)
    host = "cursor" if inactive == "host" else "claude"
    (wrappers / host / "invalid.json.tmpl").write_text("{{ .missing.inactive.value }}")
    _write_wrapper_config(
        config, hosts=("claude", "codex"), environment="enabled" if inactive == "host" else "disabled"
    )
    result = _apply(source, destination, config)
    assert result.returncode == 0, result.stderr
    if inactive == "host":
        assert (_wrapper_roots(destination)[0] / ".support.json").is_file(), "active wrapper was not delivered"
    assert not (_wrapper_roots(destination)[2] / "invalid.json").exists()


@pytest.mark.parametrize(
    "invalid",
    [
        "escape",
        "symlink_root",
        "symlink_parent",
        "symlink_file",
        "symlink_directory",
        "collision",
        "parent_collision",
        "native_collision",
        "empty_target",
        "backslash_target",
        "skills_overlap",
    ],
)
def test_canonical_wrappers_reject_unsafe_sources_and_output_collisions(tmp_path, invalid):
    """Unsafe source resolution and competing package output must fail before apply."""
    source, destination, config, wrappers = _initialize_wrapper_source(tmp_path)
    if invalid == "escape":
        config.write_text(config.read_text().replace("domain-brain/wrappers", "domain-brain/../wrappers"))
    elif invalid == "symlink_root":
        moved = wrappers.with_name("real-wrappers")
        wrappers.rename(moved)
        wrappers.symlink_to(moved, target_is_directory=True)
    elif invalid == "symlink_parent":
        plugin = wrappers.parent
        moved = plugin.with_name("real-plugin")
        plugin.rename(moved)
        plugin.symlink_to(moved, target_is_directory=True)
    elif invalid == "symlink_file":
        (wrappers / "claude/link.txt").symlink_to(wrappers / "codex/payload.bin")
    elif invalid == "symlink_directory":
        (wrappers / "claude/linked").symlink_to(wrappers / "codex/scripts", target_is_directory=True)
    elif invalid == "native_collision":
        native = source / "dot_local/share/agent-plugins/marketplace/plugins/domain-brain/claude/dot_support.json"
        native.parent.mkdir(parents=True)
        native.write_text("collision\n")
    elif invalid == "empty_target":
        (wrappers / "claude/.tmpl").write_text("collision\n")
    elif invalid == "backslash_target":
        (wrappers / "claude/back\\slash").write_text("collision\n")
    elif invalid == "collision":
        (wrappers / "claude/.support.json").write_text("collision\n")
    elif invalid == "parent_collision":
        (wrappers / "claude/scripts.tmpl").write_text("collision\n")
    else:
        overlap = wrappers / "claude/skills/records/SKILL.md"
        overlap.parent.mkdir(parents=True)
        overlap.write_text("collision\n")
    result = _apply(source, destination, config)
    assert result.returncode != 0, f"accepted unsafe wrapper case {invalid}"
