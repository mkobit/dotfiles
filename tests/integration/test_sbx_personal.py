import json
import os
import shutil
import subprocess
import tomllib
from copy import deepcopy
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHEZMOI_SOURCE = REPO_ROOT / "src" / "chezmoi"
PERSONAL_SCRIPT = CHEZMOI_SOURCE / ".chezmoiscripts" / "run_onchange_after_01_build-sbx-personal-learning-kit.sh.tmpl"
CATALOG_DATA = {
    "ai": {
        "skills": {
            "authored": {
                "authored-fixture": "present",
                "nested-skill": "present",
                "disabled-authored": "absent",
            },
            "external": {
                "fixture-plugin": {
                    "skills": {
                        "external-fixture": "present",
                        "disabled-external": "absent",
                    }
                }
            },
        },
        "guidelines": {
            "sections": [
                {"content": "## Fixture guidelines\nUse the project checks."},
                {"content": "## Fixture voice\nKeep the output concise."},
            ]
        },
    }
}


def _fixture_catalog_data() -> dict:
    data = deepcopy(CATALOG_DATA)
    skills = data["ai"]["skills"]
    for catalog_path in (CHEZMOI_SOURCE / ".chezmoidata/ai/skills").glob("*.toml"):
        with catalog_path.open("rb") as catalog_file:
            catalog = tomllib.load(catalog_file)["ai"]["skills"]
        for name in catalog.get("authored", {}):
            skills["authored"][name] = "absent"
        for source_name, source in catalog.get("external", {}).items():
            skills["external"].setdefault(source_name, {"skills": {}})
            skills["external"][source_name]["skills"] = dict.fromkeys(source.get("skills", {}), "absent")
    return data


def _render_personal_script(destination: Path, enabled: bool | None, extra_data: dict | None = None) -> str:
    data = {"sbx": {"personal": {}}}
    if enabled is not None:
        data["sbx"]["personal"]["enabled"] = enabled
    if extra_data:
        data.update(extra_data)
    result = subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPO_ROOT),
            "--destination",
            str(destination),
            "execute-template",
            "--file",
            "--override-data",
            json.dumps(data),
            str(PERSONAL_SCRIPT),
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _portable_skills(destination: Path) -> Path:
    return destination / ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills"


def _populate_selected_portable_skills(destination: Path) -> Path:
    source = _portable_skills(destination)
    selected = {"authored-fixture", "nested-skill", "external-fixture"}
    for skill_name in selected:
        skill = source / skill_name
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(f"# {skill_name}\n", encoding="utf-8")
    return source


def _run(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["sh"], input=script, capture_output=True, check=False, text=True)


def test_personal_layer_snapshots_portable_skills_and_preserves_nested_resources(tmp_path):
    destination = tmp_path / "alternate-destination"
    source = _populate_selected_portable_skills(destination)
    (source / "arbitrary-extra").mkdir(parents=True)
    (source / "arbitrary-extra" / "SKILL.md").write_text("# Extra\n", encoding="utf-8")
    (source / "nested-skill" / "references").mkdir(parents=True)
    (source / "nested-skill" / "SKILL.md").write_text("# Nested\n", encoding="utf-8")
    (source / "nested-skill" / "references" / "guide.md").write_text("guide\n", encoding="utf-8")
    (source / "nested-skill" / "references" / "guide.md").chmod(0o755)

    fixture_data = _fixture_catalog_data()
    result = _run(_render_personal_script(destination, enabled=True, extra_data=fixture_data))

    assert result.returncode == 0, result.stderr
    personal = destination / ".local/share/sbx/personal"
    overlay = yaml.safe_load((personal / "personal.sbxenv.yaml").read_text(encoding="utf-8"))
    assert overlay == {
        "schemaVersion": "1",
        "kits": ["./kit", "./skills-kit"],
        "sandboxOptions": {"shareSkills": False},
    }
    for relative_root in (
        ".agents/skills",
        ".claude/skills",
        ".gemini/antigravity-cli/skills",
    ):
        copied = personal / "skills-kit/files/home" / relative_root / "nested-skill"
        assert (copied / "SKILL.md").read_text(encoding="utf-8") == "# Nested\n"
        assert (copied / "references/guide.md").read_text(encoding="utf-8") == "guide\n"
        assert (copied / "references/guide.md").stat().st_mode & 0o111
        assert not (personal / "kit/files/home" / relative_root / "arbitrary-extra").exists()


def test_personal_layer_prunes_stale_snapshot_and_missing_input(tmp_path):
    destination = tmp_path / "destination"
    source = _populate_selected_portable_skills(destination)
    fixture_data = _fixture_catalog_data()
    script = _render_personal_script(destination, enabled=True, extra_data=fixture_data)
    assert _run(script).returncode == 0

    skills = destination / ".local/share/sbx/personal/skills-kit/files/home/.agents/skills"
    assert (skills / "authored-fixture/SKILL.md").is_file()

    (source / "authored-fixture").rename(source / "replacement")
    replacement_data = deepcopy(fixture_data)
    replacement_data["ai"]["skills"]["authored"]["authored-fixture"] = "absent"
    replacement_data["ai"]["skills"]["authored"]["replacement"] = "present"
    replacement_script = _render_personal_script(destination, enabled=True, extra_data=replacement_data)
    assert _run(replacement_script).returncode == 0
    assert not (skills / "authored-fixture").exists()
    assert (skills / "replacement/SKILL.md").is_file()

    (source / "replacement").rename(source / "missing")
    missing_selected = _run(replacement_script)
    assert missing_selected.returncode != 0
    assert (skills / "replacement/SKILL.md").is_file()

    source.rename(source.with_name("withheld-portable-skills"))
    missing = _run(script)
    assert missing.returncode != 0
    assert (skills / "replacement/SKILL.md").is_file()
    assert "portable skills are unavailable" in missing.stderr


def test_personal_layer_disabled_is_a_noop(tmp_path):
    destination = tmp_path / "destination"
    _populate_selected_portable_skills(destination)
    fixture_data = _fixture_catalog_data()
    assert _run(_render_personal_script(destination, enabled=True, extra_data=fixture_data)).returncode == 0
    personal = destination / ".local/share/sbx/personal"
    assert personal.is_dir()

    result = _run(_render_personal_script(destination, enabled=False, extra_data=fixture_data))

    assert result.returncode == 0, result.stderr
    assert not personal.exists()


def test_personal_layer_missing_setting_is_a_noop(tmp_path):
    destination = tmp_path / "destination"
    sentinel = destination / ".local/share/sbx/personal/sentinel"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("keep\n", encoding="utf-8")

    result = _run(_render_personal_script(destination, enabled=None))

    assert result.returncode == 0, result.stderr
    assert sentinel.read_text(encoding="utf-8") == "keep\n"


def test_personal_layer_contains_only_portable_learning_content(tmp_path):
    destination = tmp_path / "destination"
    source = _populate_selected_portable_skills(destination)
    (source / "skill").mkdir(parents=True)
    (source / "skill" / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    assert (
        _run(
            _render_personal_script(
                destination,
                enabled=True,
                extra_data={
                    "ai": {
                        **_fixture_catalog_data()["ai"],
                        "agent_context": {"environment": "host-only-secret"},
                    }
                },
            )
        ).returncode
        == 0
    )

    personal = destination / ".local/share/sbx/personal"
    paths = {path.relative_to(personal).as_posix() for path in personal.rglob("*")}
    assert not any(path.startswith("kit/files/home/.codex") for path in paths)
    instructions = yaml.safe_load((personal / "kit/spec.yaml").read_text(encoding="utf-8"))["agentInstructions"][
        "content"
    ]
    assert instructions == (
        "## Fixture guidelines\nUse the project checks.\n\n"
        "## Fixture voice\nKeep the output concise.\n\n"
        "You are already inside an isolated sandbox.\n"
        "Run project build and verification commands here.\n"
        "Host orchestration belongs to the host coordinator."
    )
    assert "host-only-secret" not in instructions


def _codex_fixture(destination: Path) -> None:
    marketplace = destination / ".local/share/agent-plugins/marketplace"
    (marketplace / ".agents/plugins").mkdir(parents=True)
    (marketplace / ".agents/plugins/marketplace.json").write_text("{}\n", encoding="utf-8")
    plugin = marketplace / "plugins/mkobit-dotfiles/codex/.codex-plugin"
    plugin.mkdir(parents=True)
    (plugin / "plugin.json").write_text("{}\n", encoding="utf-8")
    codex_skills = marketplace / "plugins/mkobit-dotfiles/codex/skills"
    portable = marketplace / "plugins/mkobit-dotfiles/skills"
    for skill_name in ("authored-fixture", "nested-skill", "external-fixture"):
        source = portable / skill_name
        source.mkdir(parents=True, exist_ok=True)
        (source / "SKILL.md").write_text(f"# {skill_name}\n", encoding="utf-8")
        shutil.copytree(source, codex_skills / skill_name)


def test_personal_layer_copies_cached_tools_and_codex_package_separately(tmp_path):
    destination = tmp_path / "destination"
    _populate_selected_portable_skills(destination)
    _codex_fixture(destination)
    cache = destination / ".local/share/sbx/tool-cache/linux_amd64"
    cache.mkdir(parents=True)
    binary = cache / "ripgrep"
    binary.write_bytes(b"fixture-rg")
    binary.chmod(0o755)
    data = _fixture_catalog_data()
    data["sbx"] = {"personal": {"enabled": True, "tools": {"ripgrep": True}, "plugins": {"codex": True}}}
    data["bin"] = {"ripgrep": {"github_releases": {"bin_name": "rg", "path_format": "x/rg"}}}

    assert _run(_render_personal_script(destination, True, data)).returncode == 0
    personal = destination / ".local/share/sbx/personal"
    assert (personal / "kit/files/home/.local/share/sbx/bin/rg").read_bytes() == b"fixture-rg"
    guest_tool = personal / "kit/files/home/.local/share/sbx/bin/rg"
    guest_tool.chmod(0o644)
    setup = yaml.safe_load((personal / "kit/spec.yaml").read_text())["setup"]["install"]
    guest_bin = tmp_path / "guest-bin"
    guest_bin.mkdir()
    guest_copy = guest_bin / "rg"
    guest_copy.write_bytes(guest_tool.read_bytes())
    guest_copy.chmod(0o644)
    persistent = tmp_path / "persistent.sh"
    persistent.write_text("export PATH=/project/bin\n", encoding="utf-8")
    setup_commands = [
        item["command"]
        .replace("/home/agent/.local/share/sbx/bin", str(guest_bin))
        .replace("/etc/sandbox-persistent.sh", str(persistent))
        for item in setup
    ]
    for command in setup_commands:
        result = subprocess.run(["sh", "-c", command], capture_output=True, check=False, text=True)
        assert result.returncode == 0, result.stderr
    assert guest_copy.stat().st_mode & 0o111
    assert (
        personal
        / "codex-kit/files/home/.local/share/sbx/marketplace/plugins/mkobit-dotfiles/codex/.codex-plugin/plugin.json"
    ).is_file()
    assert "./skills-kit" not in yaml.safe_load((personal / "personal.codex.sbxenv.yaml").read_text())["kits"]


def test_personal_layer_missing_new_input_preserves_previous_output_and_disable_prunes(tmp_path):
    destination = tmp_path / "destination"
    _populate_selected_portable_skills(destination)
    _codex_fixture(destination)
    data = _fixture_catalog_data()
    data["sbx"] = {"personal": {"enabled": True, "plugins": {"codex": True}}}
    assert _run(_render_personal_script(destination, True, data)).returncode == 0
    personal = destination / ".local/share/sbx/personal"
    sentinel = personal / "sentinel"
    sentinel.write_text("keep\n", encoding="utf-8")
    (destination / ".local/share/agent-plugins/marketplace/.agents/plugins/marketplace.json").unlink()
    assert _run(_render_personal_script(destination, True, data)).returncode != 0
    assert sentinel.read_text() == "keep\n"
    disabled = {"sbx": {"personal": {"enabled": False}}}
    assert _run(_render_personal_script(destination, False, disabled)).returncode == 0
    assert not personal.exists()


def test_personal_layer_missing_codex_skill_preserves_previous_output(tmp_path):
    destination = tmp_path / "destination"
    _populate_selected_portable_skills(destination)
    _codex_fixture(destination)
    data = _fixture_catalog_data()
    data["sbx"] = {"personal": {"enabled": True, "plugins": {"codex": True}}}
    assert _run(_render_personal_script(destination, True, data)).returncode == 0
    personal = destination / ".local/share/sbx/personal"
    sentinel = personal / "sentinel"
    sentinel.write_text("keep\n", encoding="utf-8")
    (
        destination
        / ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/codex/skills/nested-skill/SKILL.md"
    ).unlink()
    result = _run(_render_personal_script(destination, True, data))
    assert result.returncode != 0
    assert sentinel.read_text() == "keep\n"


def test_personal_layer_setup_install_schema_and_path_architecture_gate(tmp_path):
    destination = tmp_path / "destination"
    _populate_selected_portable_skills(destination)
    cache = destination / ".local/share/sbx/tool-cache/linux_amd64"
    cache.mkdir(parents=True)
    binary = cache / "ripgrep"
    binary.write_bytes(b"rg")
    binary.chmod(0o755)
    data = _fixture_catalog_data()
    data["sbx"] = {"personal": {"enabled": True, "tools": {"ripgrep": True}}}
    data["bin"] = {"ripgrep": {"github_releases": {"bin_name": "rg", "path_format": "x/rg"}}}
    assert _run(_render_personal_script(destination, True, data)).returncode == 0
    spec = yaml.safe_load((destination / ".local/share/sbx/personal/kit/spec.yaml").read_text())
    installs = spec["setup"]["install"]
    assert all(isinstance(item, dict) for item in installs)
    assert all(item["user"] == "1000" for item in installs)

    persistent = tmp_path / "persistent.sh"
    persistent.write_text("export PATH=/project/bin\n", encoding="utf-8")
    guest_bin = tmp_path / "guest-bin"
    guest_bin.mkdir()
    guest_tool = guest_bin / "rg"
    guest_tool.write_bytes(b"rg")
    guest_tool.chmod(0o644)
    commands = [
        item["command"]
        .replace("/home/agent/.local/share/sbx/bin", str(guest_bin))
        .replace("/etc/sandbox-persistent.sh", str(persistent))
        for item in installs
    ]
    matching = subprocess.run(["sh", "-c", "; ".join(commands)], capture_output=True, check=False, text=True)
    assert matching.returncode == 0, matching.stderr
    assert guest_tool.stat().st_mode & 0o111
    shell = subprocess.run(
        ["/bin/sh", "-c", f'. "{persistent}"; printf "%s" "$PATH"'],
        env={"PATH": "/project/bin"},
        capture_output=True,
        check=False,
        text=True,
    )
    assert shell.stdout == f"/project/bin:{guest_bin}"
    persistent_after_match = persistent.read_text()

    fake_uname = tmp_path / "uname"
    fake_uname.write_text("#!/bin/sh\necho aarch64\n", encoding="utf-8")
    fake_uname.chmod(0o755)
    mismatch = subprocess.run(
        ["sh", "-c", commands[0]],
        env={"PATH": f"{tmp_path}:{os.environ['PATH']}"},
        capture_output=True,
        check=False,
        text=True,
    )
    assert mismatch.returncode != 0
    assert "architecture" in mismatch.stderr
    assert persistent.read_text() == persistent_after_match


def test_personal_layer_missing_cached_tool_preserves_previous_output(tmp_path):
    destination = tmp_path / "destination"
    _populate_selected_portable_skills(destination)
    cache = destination / ".local/share/sbx/tool-cache/linux_amd64"
    cache.mkdir(parents=True)
    binary = cache / "ripgrep"
    binary.write_bytes(b"rg")
    binary.chmod(0o755)
    data = _fixture_catalog_data()
    data["sbx"] = {"personal": {"enabled": True, "tools": {"ripgrep": True}}}
    data["bin"] = {"ripgrep": {"github_releases": {"bin_name": "rg", "path_format": "x/rg"}}}
    assert _run(_render_personal_script(destination, True, data)).returncode == 0
    previous = destination / ".local/share/sbx/personal/kit/files/home/.local/share/sbx/bin/rg"
    binary.unlink()
    assert _run(_render_personal_script(destination, True, data)).returncode != 0
    assert previous.read_bytes() == b"rg"


def test_personal_layer_false_selections_prune_optional_outputs_and_keep_skills(tmp_path):
    destination = tmp_path / "destination"
    _populate_selected_portable_skills(destination)
    _codex_fixture(destination)
    cache = destination / ".local/share/sbx/tool-cache/linux_amd64"
    cache.mkdir(parents=True)
    binary = cache / "ripgrep"
    binary.write_bytes(b"rg")
    binary.chmod(0o755)
    data = _fixture_catalog_data()
    data["sbx"] = {"personal": {"enabled": True, "tools": {"ripgrep": True}, "plugins": {"codex": True}}}
    data["bin"] = {"ripgrep": {"github_releases": {"bin_name": "rg", "path_format": "x/rg"}}}
    assert _run(_render_personal_script(destination, True, data)).returncode == 0
    data["sbx"]["personal"]["tools"]["ripgrep"] = False
    data["sbx"]["personal"]["plugins"]["codex"] = False
    assert _run(_render_personal_script(destination, True, data)).returncode == 0
    personal = destination / ".local/share/sbx/personal"
    assert not (personal / "codex-kit").exists()
    assert not (personal / "personal.codex.sbxenv.yaml").exists()
    assert not (personal / "kit/files/home/.local/share/sbx/bin/rg").exists()
    assert (personal / "skills-kit/files/home/.agents/skills/authored-fixture/SKILL.md").exists()


def test_personal_layer_fingerprint_tracks_catalog_and_marketplace_inputs(tmp_path):
    destination = tmp_path / "destination"
    _populate_selected_portable_skills(destination)
    data = _fixture_catalog_data()
    data["sbx"] = {"personal": {"enabled": True}}
    first = _render_personal_script(destination, True, data)
    data["bin"] = {"ripgrep": {"version": "changed"}}
    second = _render_personal_script(destination, True, data)
    assert first.splitlines()[2] != second.splitlines()[2]
    data["ai"] = {**data["ai"], "plugin_bridge": {"marketplace": {"name": "dotfiles"}}}
    third = _render_personal_script(destination, True, data)
    data["ai"]["plugin_bridge"]["marketplace"]["name"] = "changed"
    fourth = _render_personal_script(destination, True, data)
    assert third.splitlines()[2] != fourth.splitlines()[2]
