from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

import skill_filter.materializer as materializer_module
from skill_filter.materializer import MaterializerError, materialize


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _payload(tmp_path: Path) -> dict[str, object]:
    working = tmp_path / "working"
    output = tmp_path / "assembled"
    wrapper = working / "src/plugins/demo/wrapper"
    _write(wrapper / "plugin.json.tmpl", "package")
    _write(
        wrapper / "cursor/dot_cursor-plugin/plugin.json.tmpl",
        "cursor manifest",
    )
    _write(working / "src/ai/skills/shared/SKILL.md", "shared")
    _write(working / "src/plugins/demo/skills/cursor-only/SKILL.md", "cursor")
    return {
        "plan_version": 1,
        "plugin_bridge": {
            "marketplaces": {"dotfiles": {"hosts": ["claude", "cursor"]}},
            "capabilities": {
                "demo": {
                    "marketplace": "dotfiles",
                    "hosts": ["claude", "cursor"],
                    "wrapper_source_dir": "src/plugins/demo/wrapper",
                    "authored_skill_source": "src/ai/skills",
                    "source_dir": "src/plugins/demo",
                    "skills": {"cursor-only": "cursor"},
                }
            },
            "plugins": {},
        },
        "skills": {"authored": {"shared": "present"}},
        "overlay_skills": {},
        "working_tree": str(working),
        "output_source_root": str(output),
        "environment": "local",
        "acquired_sources": {},
    }


def _file_snapshot(root: Path, relative: str) -> tuple[bytes, int]:
    path = root / relative
    return path.read_bytes(), stat.S_IMODE(path.stat().st_mode)


@pytest.mark.parametrize(
    ("name", "encoded"),
    [
        ("notes", "exact_notes"),
        ("exact_notes", "exact_literal_exact_notes"),
        ("dot_config", "exact_literal_dot_config"),
        ("private_data", "exact_literal_private_data"),
        ("literal_notes", "exact_literal_literal_notes"),
    ],
)
def test_source_name_encoder_preserves_literal_attribute_prefixes(name, encoded):
    assert materializer_module._encode_source_name(name) == encoded


def test_mark_exact_tree_avoids_encoded_name_collisions(tmp_path):
    root = tmp_path / "root"
    _write(root / "exact_notes/SKILL.md", "literal\n")
    _write(root / "notes/SKILL.md", "sibling\n")

    materializer_module._mark_exact_tree(root)

    assert (root / "exact_literal_exact_notes/SKILL.md").read_text() == "literal\n"
    assert (root / "exact_notes/SKILL.md").read_text() == "sibling\n"


def test_mark_exact_tree_encodes_nested_literal_attribute_names(tmp_path):
    root = tmp_path / "root"
    _write(root / "skills/child/marker", "child\n")
    _write(root / "skills/exact_child/marker", "literal\n")

    materializer_module._mark_exact_tree(root)

    assert (root / "exact_skills/exact_child/marker").read_text() == "child\n"
    assert (
        root / "exact_skills/exact_literal_exact_child/marker"
    ).read_text() == "literal\n"


def test_materialize_emits_exact_package_and_cursor_trees(tmp_path):
    payload = _payload(tmp_path)

    materialize(payload)

    output = Path(str(payload["output_source_root"]))
    package = (
        output / "dot_local/share/agent-plugins/marketplace/exact_plugins/exact_demo"
    )
    cursor = output / "dot_cursor/plugins/exact_local/exact_demo"
    assert (package / "plugin.json.tmpl").read_text() == "package"
    assert (package / "exact_skills/exact_shared/SKILL.md").read_text() == "shared"
    assert (
        package / "exact_cursor/exact_skills/exact_shared/SKILL.md"
    ).read_text() == "shared"
    assert (
        package / "exact_cursor/exact_skills/exact_cursor-only/SKILL.md"
    ).read_text() == "cursor"
    assert (cursor / "exact_dot_cursor-plugin/plugin.json.tmpl").read_text() == (
        "cursor manifest"
    )
    assert (cursor / "exact_skills/exact_shared/SKILL.md").read_text() == "shared"
    assert (cursor / "exact_skills/exact_cursor-only/SKILL.md").read_text() == "cursor"


def test_materialize_does_not_require_path_is_relative_to(tmp_path, monkeypatch):
    payload = _payload(tmp_path)
    _write(
        Path(str(payload["working_tree"]))
        / "src/plugins/demo/wrapper/cursor/exact_marker/marker",
        "marker",
    )
    monkeypatch.setattr(
        Path,
        "is_relative_to",
        lambda *args: (_ for _ in ()).throw(AssertionError("unsupported API")),
    )

    materialize(payload)

    assert any(
        path.read_text() == "marker"
        for path in Path(str(payload["output_source_root"]))
        .joinpath("dot_cursor/plugins/exact_local/exact_demo")
        .rglob("marker")
    )


def test_materialize_encodes_generated_skill_attribute_and_template_files(tmp_path):
    payload = _payload(tmp_path)
    skill = Path(str(payload["working_tree"])) / "src/ai/skills/shared"
    (skill / "run_eval.py").write_bytes(b"#!/usr/bin/env python3\n{{ raw }}\n")
    (skill / "instructions.tmpl").write_bytes(b"{{ should stay literal }}\n")
    (skill / "run_eval.py").chmod(0o751)
    (skill / "instructions.tmpl").chmod(0o640)

    materialize(payload)

    package = (
        Path(str(payload["output_source_root"]))
        / "dot_local/share/agent-plugins/marketplace/exact_plugins/exact_demo"
        / "exact_skills/exact_shared"
    )
    for source_name, encoded_name, mode in (
        ("run_eval.py", "literal_run_eval.py", 0o751),
        (
            "instructions.tmpl",
            "literal_instructions.tmpl.literal",
            0o640,
        ),
    ):
        source = skill / source_name
        encoded = package / encoded_name
        assert encoded.read_bytes() == source.read_bytes()
        assert stat.S_IMODE(encoded.stat().st_mode) == mode
        assert not (package / source_name).exists()


def test_materialize_replaces_owned_boundaries_deterministically(tmp_path):
    payload = _payload(tmp_path)
    materialize(payload)
    output = Path(str(payload["output_source_root"]))
    package_parent = output / "dot_local/share/agent-plugins/marketplace/exact_plugins"
    _write(package_parent / "stale/marker", "stale")
    _write(
        output / "dot_local/share/agent-plugins/marketplace/plugins/unmanaged/marker",
        "keep",
    )
    _write(output / "dot_cursor/plugins/exact_local/stale/marker", "stale")

    payload["plugin_bridge"] = {
        "marketplaces": {},
        "capabilities": {},
        "plugins": {},
    }
    materialize(payload)

    assert not (package_parent / "demo").exists()
    assert not (package_parent / "stale").exists()
    assert (
        output / "dot_local/share/agent-plugins/marketplace/plugins/unmanaged/marker"
    ).read_text() == "keep"
    assert list((output / "dot_cursor/plugins/exact_local").iterdir()) == []


def test_materialize_filters_environment_specific_capabilities(tmp_path):
    payload = _payload(tmp_path)
    bridge = payload["plugin_bridge"]
    assert isinstance(bridge, dict)
    capabilities = bridge["capabilities"]
    assert isinstance(capabilities, dict)
    capabilities["demo"]["environments"] = ["remote"]

    materialize(payload)

    output = Path(str(payload["output_source_root"]))
    assert not (
        output / "dot_local/share/agent-plugins/marketplace/exact_plugins/exact_demo"
    ).exists()
    assert list((output / "dot_cursor/plugins/exact_local").iterdir()) == []


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("marketplace", "undeclared marketplace"),
        ("hosts", "host"),
        ("wrapper", "wrapper source"),
        ("source", "capability source"),
    ],
)
def test_materialize_validates_inactive_malformed_capabilities_before_publication(
    tmp_path, mutation, message
):
    payload = _payload(tmp_path)
    output = Path(str(payload["output_source_root"]))
    package_root = output / "dot_local/share/agent-plugins/marketplace/exact_plugins"
    cursor_root = output / "dot_cursor/plugins/exact_local"
    _write(package_root / "old/marker", "old package")
    _write(cursor_root / "old/marker", "old cursor")
    (package_root / "old/marker").chmod(0o751)
    (cursor_root / "old/marker").chmod(0o640)
    before_package = _file_snapshot(package_root, "old/marker")
    before_cursor = _file_snapshot(cursor_root, "old/marker")

    capability = payload["plugin_bridge"]["capabilities"]["demo"]
    capability["environments"] = ["remote"]
    if mutation == "marketplace":
        capability["marketplace"] = "missing"
    elif mutation == "hosts":
        capability["hosts"] = ["unsupported"]
    elif mutation == "wrapper":
        capability["wrapper_source_dir"] = "../outside"
    else:
        capability["source_dir"] = "src/plugins/missing"

    with pytest.raises(MaterializerError, match=message):
        materialize(payload)

    assert _file_snapshot(package_root, "old/marker") == before_package
    assert _file_snapshot(cursor_root, "old/marker") == before_cursor


def test_materialize_rolls_back_both_collections_when_second_publication_fails(
    tmp_path, monkeypatch
):
    payload = _payload(tmp_path)
    materialize(payload)
    output = Path(str(payload["output_source_root"]))
    package_root = output / "dot_local/share/agent-plugins/marketplace/exact_plugins"
    cursor_root = output / "dot_cursor/plugins/exact_local"
    before_package = _file_snapshot(package_root / "exact_demo", "plugin.json.tmpl")
    before_cursor = _file_snapshot(
        cursor_root / "exact_demo", "exact_dot_cursor-plugin/plugin.json.tmpl"
    )
    _write(
        Path(str(payload["working_tree"]))
        / "src/plugins/demo/wrapper/plugin.json.tmpl",
        "new package",
    )

    original_replace = materializer_module._replace_directory
    calls = 0

    def fail_second(staged, destination, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected second publication failure")
        return original_replace(staged, destination, *args, **kwargs)

    monkeypatch.setattr(materializer_module, "_replace_directory", fail_second)
    with pytest.raises(OSError, match="second publication"):
        materialize(payload)

    assert (
        _file_snapshot(package_root / "exact_demo", "plugin.json.tmpl")
        == before_package
    )
    assert (
        _file_snapshot(
            cursor_root / "exact_demo", "exact_dot_cursor-plugin/plugin.json.tmpl"
        )
        == before_cursor
    )


def test_materialize_preserves_preexisting_backup_sibling(tmp_path):
    payload = _payload(tmp_path)
    output = Path(str(payload["output_source_root"]))
    backup = (
        output / "dot_local/share/agent-plugins/marketplace/.exact_plugins.previous"
    )
    _write(backup / "do-not-delete", "preserve me")

    materialize(payload)

    assert (backup / "do-not-delete").read_text() == "preserve me"


def test_materialize_copies_declared_cursor_plugin_source(tmp_path):
    payload = _payload(tmp_path)
    working = Path(str(payload["working_tree"]))
    _write(working / "vendor/public-plugin/dot_cursor-plugin/plugin.json", "public")
    payload["plugin_bridge"] = {
        "marketplaces": {"public": {"hosts": ["claude", "cursor"]}},
        "capabilities": {},
        "plugins": {
            "public-plugin": {
                "marketplace": "public",
                "hosts": ["claude", "cursor"],
                "cursor_source_dir": "vendor/public-plugin",
                "environments": ["local"],
            }
        },
    }

    materialize(payload)

    output = Path(str(payload["output_source_root"]))
    installed = output / "dot_cursor/plugins/exact_local/exact_public-plugin"
    assert (installed / "exact_dot_cursor-plugin/plugin.json").read_text() == "public"


def test_materialize_rejects_symlinks_without_touching_output(tmp_path):
    payload = _payload(tmp_path)
    working = Path(str(payload["working_tree"]))
    skill = working / "src/ai/skills/shared"
    (skill / "link").symlink_to(tmp_path / "outside")
    output = Path(str(payload["output_source_root"]))
    _write(output / "marker", "keep")

    with pytest.raises(MaterializerError, match="symlink"):
        materialize(payload)

    assert (output / "marker").read_text() == "keep"
    assert not (output / "dot_cursor").exists()


def test_materialize_rejects_symlinked_package_source(tmp_path):
    payload = _payload(tmp_path)
    working = Path(str(payload["working_tree"]))
    wrapper = working / "src/plugins/demo/wrapper"
    shutil.rmtree(wrapper)
    real_wrapper = Path(str(payload["working_tree"])) / "real-wrapper"
    _write(real_wrapper / "plugin.json.tmpl", "package")
    wrapper.symlink_to(real_wrapper, target_is_directory=True)

    with pytest.raises(MaterializerError, match="symlink"):
        materialize(payload)


def test_materialize_rejects_symlinked_output_boundary(tmp_path):
    payload = _payload(tmp_path)
    output = Path(str(payload["output_source_root"]))
    redirected = tmp_path / "redirected"
    redirected.mkdir()
    (output / "dot_cursor").parent.mkdir(parents=True)
    (output / "dot_cursor").symlink_to(redirected, target_is_directory=True)

    with pytest.raises(MaterializerError, match=r"output boundary.*symlink"):
        materialize(payload)

    assert list(redirected.iterdir()) == []


def test_materialize_rejects_symlinked_output_root_ancestor(tmp_path):
    payload = _payload(tmp_path)
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    payload["output_source_root"] = str(linked_parent / "assembled")

    with pytest.raises(MaterializerError, match=r"output source.*ancestor.*symlink"):
        materialize(payload)

    assert list(real_parent.iterdir()) == []


@pytest.mark.parametrize("field", ["output_source_root", "working_tree"])
def test_materialize_rejects_non_normalized_absolute_contract_path(tmp_path, field):
    payload = _payload(tmp_path)
    output = Path(str(payload["output_source_root"]))
    original = Path(str(payload[field]))
    payload[field] = f"{original.parent}/unused/../{original.name}"

    with pytest.raises(MaterializerError, match=f"{field}.*normalized absolute"):
        materialize(payload)

    assert not output.exists()


@pytest.mark.parametrize(
    ("state", "hosts"),
    [("unexpected", ["cursor"]), ("codex", ["cursor"])],
)
def test_materialize_rejects_invalid_skill_state(tmp_path, state, hosts):
    payload = _payload(tmp_path)
    bridge = payload["plugin_bridge"]
    assert isinstance(bridge, dict)
    capability = bridge["capabilities"]["demo"]
    capability["hosts"] = hosts
    skills = payload["skills"]
    assert isinstance(skills, dict)
    skills["authored"]["shared"] = state

    with pytest.raises(MaterializerError, match=r"skill.*state"):
        materialize(payload)


@pytest.mark.parametrize(
    ("environment", "present"), [("local", True), ("remote", False)]
)
def test_materialize_overlay_local_skill_depends_on_environment(
    tmp_path, environment, present
):
    payload = _payload(tmp_path)
    working = Path(str(payload["working_tree"]))
    _write(working / "src/overlay-skills/local-only/SKILL.md", "local")
    bridge = payload["plugin_bridge"]
    assert isinstance(bridge, dict)
    capability = bridge["capabilities"]["demo"]
    capability["overlay_skill_source"] = "src/overlay-skills"
    payload["overlay_skills"] = {"authored": {"local-only": "local"}}
    payload["environment"] = environment

    materialize(payload)

    output = Path(str(payload["output_source_root"]))
    skill = (
        output
        / "dot_local/share/agent-plugins/marketplace/exact_plugins/exact_demo"
        / "exact_skills/exact_local-only/SKILL.md"
    )
    assert skill.exists() is present


def test_materializer_cli_reads_json_from_stdin(tmp_path):
    payload = _payload(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parents[1] / "skill_filter/materializer.py"),
        ],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    output = Path(str(payload["output_source_root"]))
    assert (output / "dot_cursor/plugins/exact_local/exact_demo").is_dir()


def test_materializer_cli_reports_invalid_json():
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).parents[1] / "skill_filter/materializer.py"),
        ],
        input="not-json",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith("plugin-materializer: invalid JSON:")


@pytest.mark.parametrize("name", ["../escape", "nested/plugin", ".", ""])
def test_materialize_rejects_unsafe_declaration_names(tmp_path, name):
    payload = _payload(tmp_path)
    payload["plugin_bridge"] = {
        "marketplaces": {"dotfiles": {"hosts": ["cursor"]}},
        "capabilities": {name: {"marketplace": "dotfiles", "hosts": ["cursor"]}},
        "plugins": {},
    }

    with pytest.raises(MaterializerError, match="name"):
        materialize(payload)


def test_materialize_rejects_unsupported_plan_version_before_mutation(tmp_path):
    payload = _payload(tmp_path)
    payload["plan_version"] = 2
    output = Path(str(payload["output_source_root"]))
    _write(output / "marker", "keep")

    with pytest.raises(MaterializerError, match="plan version"):
        materialize(payload)

    assert (output / "marker").read_text() == "keep"
    assert not (output / "dot_cursor").exists()


def test_materialize_rejects_undeclared_marketplace_before_mutation(tmp_path):
    payload = _payload(tmp_path)
    payload["plugin_bridge"]["capabilities"]["demo"]["marketplace"] = "missing"
    output = Path(str(payload["output_source_root"]))
    _write(output / "marker", "keep")

    with pytest.raises(MaterializerError, match="undeclared marketplace"):
        materialize(payload)

    assert (output / "marker").read_text() == "keep"
    assert not (output / "dot_cursor").exists()


@pytest.mark.parametrize("hosts", [None, "cursor", ["bogus"], ["cursor", 1]])
def test_materialize_rejects_malformed_hosts(tmp_path, hosts):
    payload = _payload(tmp_path)
    payload["plugin_bridge"]["capabilities"]["demo"]["hosts"] = hosts

    with pytest.raises(MaterializerError, match="host"):
        materialize(payload)


@pytest.mark.parametrize("path", ["", "./wrapper", "nested/../wrapper", "../wrapper"])
def test_materialize_rejects_malformed_declared_wrapper_path(tmp_path, path):
    payload = _payload(tmp_path)
    payload["plugin_bridge"]["capabilities"]["demo"]["wrapper_source_dir"] = path

    with pytest.raises(MaterializerError, match="wrapper source"):
        materialize(payload)


def test_materialize_uses_acquired_source_mapping_and_deduplicates_fanout(tmp_path):
    payload = _payload(tmp_path)
    acquired = tmp_path / "acquired"
    _write(acquired / "skills/from-acquired/SKILL.md", "acquired")
    capabilities = payload["plugin_bridge"]["capabilities"]
    capabilities["demo"]["source_id"] = "shared-pin"
    capabilities["demo"]["source_root"] = "skills"
    capabilities["demo"]["skills"] = {"from-acquired": "present"}
    capabilities["demo"].pop("source_dir")
    capabilities["other"] = {
        "marketplace": "dotfiles",
        "hosts": ["claude"],
        "wrapper_source_dir": "src/plugins/demo/wrapper",
        "source_id": "shared-pin",
        "source_root": "skills",
        "skills": {"from-acquired": "present"},
    }
    payload["acquired_sources"] = {"shared-pin": str(acquired)}
    payload["skills"] = {"authored": {}}

    materialize(payload)

    output = Path(str(payload["output_source_root"]))
    package = (
        output / "dot_local/share/agent-plugins/marketplace/exact_plugins/exact_demo"
    )
    assert (
        package / "exact_skills/exact_from-acquired/SKILL.md"
    ).read_text() == "acquired"
    other = (
        output / "dot_local/share/agent-plugins/marketplace/exact_plugins/exact_other"
    )
    assert (
        other / "exact_skills/exact_from-acquired/SKILL.md"
    ).read_text() == "acquired"


@pytest.mark.parametrize("entry_kind", ["symlink", "special"])
def test_materialize_rejects_bad_acquired_source_entries_before_mutation(
    tmp_path, entry_kind
):
    payload = _payload(tmp_path)
    acquired = tmp_path / "acquired"
    acquired.mkdir()
    if entry_kind == "symlink":
        (acquired / "link").symlink_to(tmp_path / "outside")
    else:
        os.mkfifo(acquired / "pipe")
    payload["plugin_bridge"]["capabilities"]["demo"]["source_id"] = "shared-pin"
    payload["acquired_sources"] = {"shared-pin": str(acquired)}
    output = Path(str(payload["output_source_root"]))
    _write(output / "marker", "keep")

    with pytest.raises(MaterializerError, match=entry_kind):
        materialize(payload)

    assert (output / "marker").read_text() == "keep"
    assert not (output / "dot_cursor").exists()


@pytest.mark.parametrize(
    "relative",
    [
        "exact_plugins",
        "exact_plugins/exact_demo",
        "exact_local",
        "exact_local/exact_demo",
    ],
)
def test_materialize_rejects_desired_output_symlink_before_replacement(
    tmp_path, relative
):
    payload = _payload(tmp_path)
    output = Path(str(payload["output_source_root"]))
    if relative.startswith("exact_plugins"):
        path = output / "dot_local/share/agent-plugins/marketplace" / relative
    else:
        path = output / "dot_cursor/plugins" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    redirected = tmp_path / "redirected"
    redirected.mkdir()
    path.symlink_to(redirected, target_is_directory=True)

    with pytest.raises(MaterializerError, match=r"output.*symlink"):
        materialize(payload)

    assert not (redirected / "demo").exists()


def test_materialize_preserves_modes_and_bytes_across_repeated_runs(tmp_path):
    payload = _payload(tmp_path)
    wrapper_file = (
        Path(str(payload["working_tree"])) / "src/plugins/demo/wrapper/plugin.json.tmpl"
    )
    wrapper_file.chmod(0o751)

    materialize(payload)
    output = Path(str(payload["output_source_root"]))
    package = (
        output
        / "dot_local/share/agent-plugins/marketplace/exact_plugins/exact_demo/plugin.json.tmpl"
    )
    first = (package.read_bytes(), stat.S_IMODE(package.stat().st_mode))
    materialize(payload)
    second = (package.read_bytes(), stat.S_IMODE(package.stat().st_mode))

    assert first == second == (b"package", 0o751)
