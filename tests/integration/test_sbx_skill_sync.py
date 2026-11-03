"""Exercise receipt ownership, portable copies, and native import retry behavior."""

import hashlib
import json
import os
import subprocess

import pytest
from test_sbx_workflow_setup import SETUP, SYNC, HookHarness, decisions

PORTABLE = ".local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills"
RECEIPT = ".local/state/dotfiles/sbx-skills-ownership.json"
IMPORT = ["skills", "import", "--force"]


def sync_data(**sandbox):
    data = decisions(sync_skills=True, **sandbox)
    data["ai"]["skills"] = {"authored": {"alpha": "present", "tool-only": "claude", "old": "absent"}}
    return data


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def harness(tmp_path):
    h = HookHarness(tmp_path, SYNC)
    write(h.destination / PORTABLE, "alpha/SKILL.md", "already rendered destination and decisions\n")
    write(h.destination / PORTABLE, "alpha/references/note.txt", "reference\n")
    write(h.destination / PORTABLE, "tool-only/SKILL.md", "tool specific\n")
    return h


def receipt(h):
    return json.loads((h.destination / RECEIPT).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "data",
    [
        {},
        decisions(sync_skills=False),
        decisions(sync_skills=True, provider="none"),
        {**sync_data(), "local": {}},
        {**sync_data(), "ai": {"workflow": {"enabled": False}}},
    ],
)
def test_no_receipt_and_disabled_setup_does_not_touch_files(tmp_path, data):
    h = harness(tmp_path)
    h.run(data, apply=True)
    assert not (h.destination / RECEIPT).exists()
    assert not (h.destination / ".agents").exists()
    assert not h.calls()


@pytest.mark.parametrize("workflow_enabled", [False, None], ids=["global-disabled", "global-missing"])
def test_explicit_sync_applies_without_global_workflow(tmp_path, workflow_enabled):
    h = harness(tmp_path)
    data = sync_data()
    if workflow_enabled is None:
        del data["ai"]["workflow"]
    else:
        data["ai"]["workflow"]["enabled"] = workflow_enabled
    h.run(data, apply=True)
    target = h.destination / ".agents/skills/alpha/SKILL.md"
    assert target.read_bytes() == (h.destination / PORTABLE / "alpha/SKILL.md").read_bytes()
    assert receipt(h)["imports"]["alpha"]
    assert h.calls() == [IMPORT]
    h.run(data, apply=True)
    assert target.is_file()
    assert h.calls() == [IMPORT]


def test_real_portable_files_are_copied_with_digests_and_imported_once(tmp_path):
    h = harness(tmp_path)
    h.run(sync_data(), apply=True)
    target = h.destination / ".agents/skills/alpha"
    assert (target / "SKILL.md").read_text() == "already rendered destination and decisions\n"
    assert (target / "references/note.txt").is_file()
    assert all(not p.is_symlink() for p in target.rglob("*"))
    assert not (target.parent / "tool-only").exists()
    state = receipt(h)
    assert (
        state["skills"]["alpha"]["files"]["SKILL.md"]["sha256"]
        == hashlib.sha256((target / "SKILL.md").read_bytes()).hexdigest()
    )
    assert state["imports"]["alpha"]
    before = (h.destination / RECEIPT).read_bytes()
    h.run(sync_data(), apply=True)
    assert h.calls() == [IMPORT]
    assert (h.destination / RECEIPT).read_bytes() == before
    assert not list((h.destination / RECEIPT).parent.glob("*.tmp*"))


def test_native_import_keeps_all_root_precedence_and_replaces_obsolete_payload(tmp_path):
    h = harness(tmp_path)
    write(h.destination, ".claude/skills/alpha/SKILL.md", "lower precedence")
    write(h.destination, ".cursor/skills/other/SKILL.md", "other root")
    write(tmp_path, "fake-store/alpha/obsolete", "old native entry")
    h.run(sync_data())
    assert (tmp_path / "fake-store/alpha/SKILL.md").read_text().startswith("already rendered")
    assert not (tmp_path / "fake-store/alpha/obsolete").exists()
    assert (tmp_path / "fake-store/other/SKILL.md").read_text() == "other root"
    assert h.calls() == [IMPORT]


def test_source_updates_remove_only_unchanged_obsolete_copies(tmp_path):
    h = harness(tmp_path)
    h.run(sync_data())
    source = h.destination / PORTABLE / "alpha"
    (source / "references/note.txt").unlink()
    (source / "SKILL.md").write_text("new rendered payload\n")
    write(source, "new/note", "new file")
    h.run(sync_data())
    target = h.destination / ".agents/skills/alpha"
    assert not (target / "references").exists()
    assert (target / "SKILL.md").read_text() == "new rendered payload\n"
    assert (target / "new/note").read_text() == "new file"
    assert h.calls() == [IMPORT, IMPORT]
    assert not (tmp_path / "fake-store/alpha/references/note.txt").exists()


@pytest.mark.parametrize("collision", ["directory", "file", "nested-file", "nested-directory"])
def test_unowned_sources_are_never_overwritten(tmp_path, collision):
    h = harness(tmp_path)
    target = h.destination / ".agents/skills/alpha"
    if collision == "directory":
        target.mkdir(parents=True)
    elif collision == "file":
        write(h.destination, ".agents/skills/alpha", "unowned root")
    else:
        h.run(sync_data())
        source = h.destination / PORTABLE / "alpha/new"
        source.mkdir()
        write(source, "file", "desired")
        if collision == "nested-file":
            write(target, "new/file", "unowned")
        else:
            (target / "new/file").mkdir(parents=True)
    before = len(h.calls())
    output = h.run(sync_data())
    assert "collision" in output.lower()
    assert len(h.calls()) == before
    if collision == "file":
        assert target.read_text() == "unowned root"
    elif collision == "directory":
        assert list(target.iterdir()) == []
    elif collision == "nested-file":
        assert (target / "new/file").read_text() == "unowned"
    else:
        assert (target / "new/file").is_dir()


def test_modified_owned_file_is_preserved_and_retry_works_when_restored(tmp_path):
    h = harness(tmp_path)
    h.run(sync_data())
    target = h.destination / ".agents/skills/alpha/SKILL.md"
    old = target.read_text()
    target.write_text("local changes")
    (h.destination / PORTABLE / "alpha/SKILL.md").write_text("upstream changes")
    assert "collision" in h.run(sync_data()).lower()
    assert target.read_text() == "local changes"
    assert h.calls() == [IMPORT]
    target.write_text(old)
    h.run(sync_data())
    assert target.read_text() == "upstream changes"
    assert h.calls() == [IMPORT, IMPORT]


@pytest.mark.parametrize("disabled", ["selection", "provider", "sync", "method"])
def test_removed_or_disabled_skill_cleans_only_owned_files_and_keeps_store(tmp_path, disabled):
    h = harness(tmp_path)
    h.run(sync_data())
    data = sync_data()
    if disabled == "selection":
        data["ai"]["skills"]["authored"]["alpha"] = "absent"
    elif disabled == "provider":
        data["ai"]["sandbox"]["provider"] = "none"
    elif disabled == "sync":
        data["ai"]["sandbox"]["sync_skills"] = False
    else:
        data["local"] = {}
    output = h.run(data, apply=True)
    assert not (h.destination / ".agents/skills/alpha").exists()
    assert (tmp_path / "fake-store/alpha/SKILL.md").is_file()
    assert "alpha" in output and "identity" in output.lower()
    assert h.calls() == [IMPORT]
    assert receipt(h)["imports"]["alpha"]


def test_cleanup_preserves_changed_and_added_content(tmp_path):
    h = harness(tmp_path)
    h.run(sync_data())
    target = h.destination / ".agents/skills/alpha"
    (target / "SKILL.md").write_text("local modification")
    write(target, "unowned", "user file")
    output = h.run(decisions(sync_skills=False))
    assert "collision" in output.lower()
    assert (target / "SKILL.md").read_text() == "local modification"
    assert (target / "unowned").read_text() == "user file"
    assert not (target / "references/note.txt").exists()
    assert h.calls() == [IMPORT]


@pytest.mark.parametrize(
    "where",
    [
        "portable-parent",
        "portable-skill",
        "portable-file",
        "portable-directory",
        "destination-parent",
        "destination-skill",
        "destination-file",
        "state-parent",
        "receipt",
    ],
)
def test_symlink_components_are_rejected_without_touching_referents(tmp_path, where):
    h = harness(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    write(outside, "sentinel", "untouched")
    paths = {
        "portable-parent": PORTABLE,
        "portable-skill": PORTABLE + "/alpha",
        "portable-file": PORTABLE + "/alpha/SKILL.md",
        "portable-directory": PORTABLE + "/alpha/references",
        "destination-parent": ".agents",
        "destination-skill": ".agents/skills/alpha",
        "destination-file": ".agents/skills/alpha/SKILL.md",
        "state-parent": ".local/state",
        "receipt": RECEIPT,
    }
    if where == "destination-file":
        h.run(sync_data())
    path = h.destination / paths[where]
    if path.is_dir():
        path.rename(path.with_name(path.name + "-saved"))
    elif path.exists():
        path.unlink()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(outside, target_is_directory=True)
    result = subprocess.run(
        ["/bin/bash"],
        input=h.render(sync_data()),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PATH": str(h.bin)},
    )
    assert "symlink" in (result.stdout + result.stderr).lower()
    assert result.returncode in (0, 1)
    assert (outside / "sentinel").read_text() == "untouched"
    assert list(outside.iterdir()) == [outside / "sentinel"]
    assert h.calls() == ([IMPORT] if where == "destination-file" else [])


@pytest.mark.parametrize("name", ["../escape", "..", "/absolute", "a/b", "bad\\name"])
def test_unsafe_skill_names_are_rejected(tmp_path, name):
    h = harness(tmp_path)
    data = sync_data()
    data["ai"]["skills"]["authored"] = {name: "present"}
    result = subprocess.run(["/bin/bash"], input=h.render(data), capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "unsafe" in result.stderr.lower()
    assert not h.calls()


@pytest.mark.parametrize(
    "bad_files",
    [
        {"../outside": {"sha256": "0" * 64, "mode": 0o644}},
        {"/absolute": {"sha256": "0" * 64, "mode": 0o644}},
        {"SKILL.md": {"sha256": "bad", "mode": 0o644}},
    ],
)
def test_invalid_receipt_is_rejected_before_mutation(tmp_path, bad_files):
    h = harness(tmp_path)
    write(
        h.destination,
        RECEIPT,
        json.dumps({"version": 2, "skills": {"alpha": {"files": bad_files, "directories": []}}, "imports": {}}),
    )
    result = subprocess.run(["/bin/bash"], input=h.render(sync_data()), capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert not (h.destination / ".agents").exists()
    assert not h.calls()


def test_failed_native_import_stays_pending_and_retries(tmp_path):
    h = harness(tmp_path)
    h.configure(fail=[IMPORT])
    assert "skip" in h.run(sync_data()).lower()
    assert receipt(h)["skills"]["alpha"]["files"]
    assert not receipt(h)["imports"]
    h.configure(fail=[])
    h.run(sync_data(), apply=True)
    assert h.calls() == [IMPORT, IMPORT]
    assert receipt(h)["imports"]["alpha"]


def test_unavailable_cli_leaves_pending_copies(tmp_path):
    h = harness(tmp_path)
    assert "unavailable" in h.run(sync_data(), missing_cli=True).lower()
    assert receipt(h)["skills"]["alpha"]["files"]
    assert not receipt(h)["imports"]
    assert not h.calls()
    h._fake_cli()
    h.run(sync_data())
    assert h.calls() == [IMPORT]


def test_missing_portable_source_does_not_import_stale_payload(tmp_path):
    h = harness(tmp_path)
    h.run(sync_data())
    source = h.destination / PORTABLE / "alpha"
    source.rename(source.with_name("saved"))
    assert "skip" in h.run(sync_data()).lower()
    assert (h.destination / ".agents/skills/alpha/SKILL.md").is_file()
    assert h.calls() == [IMPORT]


def test_failed_import_does_not_claim_store_ownership_for_removal(tmp_path):
    h = harness(tmp_path)
    h.configure(fail=[IMPORT])
    h.run(sync_data())
    write(tmp_path, "fake-store/alpha/SKILL.md", "unowned native store")
    h.run(decisions(sync_skills=False))
    assert not receipt(h)["imports"]
    assert (tmp_path / "fake-store/alpha/SKILL.md").read_text() == "unowned native store"
    assert h.calls() == [IMPORT]


def test_prior_success_does_not_prove_current_store_identity(tmp_path):
    h = harness(tmp_path)
    h.run(sync_data())
    write(tmp_path, "fake-store/alpha/SKILL.md", "new native owner")
    output = h.run(decisions(sync_skills=False))
    assert "alpha" in output and "identity" in output.lower()
    assert (tmp_path / "fake-store/alpha/SKILL.md").read_text() == "new native owner"
    assert h.calls() == [IMPORT]


@pytest.mark.parametrize("hook", [SETUP, SYNC])
def test_enabled_hooks_render_as_valid_bash(tmp_path, hook):
    h = HookHarness(tmp_path, hook)
    rendered = h.render(sync_data())
    assert rendered.startswith("#!/usr/bin/env bash\n")
    result = subprocess.run(["bash", "-n"], input=rendered, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_added_nonowned_content_blocks_import_and_is_reported(tmp_path):
    h = harness(tmp_path)
    h.run(sync_data())
    target = h.destination / ".agents/skills/alpha"
    write(target, "user-note", "unowned")
    (h.destination / PORTABLE / "alpha/SKILL.md").write_text("new source")
    output = h.run(sync_data())
    assert "collision" in output.lower()
    assert (target / "user-note").read_text() == "unowned"
    assert h.calls() == [IMPORT]


def test_nested_destination_symlink_blocks_import_and_cleanup(tmp_path):
    h = harness(tmp_path)
    h.run(sync_data())
    target = h.destination / ".agents/skills/alpha"
    outside = tmp_path / "outside-file"
    outside.write_text("preserved")
    (target / "user-link").symlink_to(outside)
    assert "symlink" in h.run(sync_data()).lower()
    assert "symlink" in h.run(decisions(sync_skills=False)).lower()
    assert outside.read_text() == "preserved"
    assert h.calls() == [IMPORT]


def test_modified_obsolete_copy_is_preserved_without_import(tmp_path):
    h = harness(tmp_path)
    h.run(sync_data())
    target = h.destination / ".agents/skills/alpha/references/note.txt"
    target.write_text("local change")
    (h.destination / PORTABLE / "alpha/references/note.txt").unlink()
    assert "collision" in h.run(sync_data()).lower()
    assert target.read_text() == "local change"
    assert h.calls() == [IMPORT]


def test_removed_catalog_entry_and_missing_authored_map_clean_owned_copy(tmp_path):
    h = harness(tmp_path)
    h.run(sync_data())
    h.run(decisions(sync_skills=True))
    assert not (h.destination / ".agents/skills/alpha").exists()
    assert h.calls() == [IMPORT]


def test_portable_executable_bit_survives_materialization(tmp_path):
    h = harness(tmp_path)
    source = write(h.destination / PORTABLE, "alpha/scripts/tool.sh", "#!/bin/sh\nexit 0\n")
    source.chmod(0o755)
    h.run(sync_data())
    target = h.destination / ".agents/skills/alpha/scripts/tool.sh"
    assert target.stat().st_mode & 0o777 == 0o755
    assert target.read_bytes() == source.read_bytes()


def test_unreadable_portable_directory_preserves_prior_copy_and_import(tmp_path):
    h = harness(tmp_path)
    h.run(sync_data())
    directory = h.destination / PORTABLE / "alpha/references"
    directory.chmod(0)
    try:
        if os.access(directory, os.R_OK):
            pytest.skip("Test requires an unprivileged process for directory read denial")
        output = h.run(sync_data())
        assert "denied" in output.lower()
        assert (h.destination / ".agents/skills/alpha/references/note.txt").read_text() == "reference\n"
        assert h.calls() == [IMPORT]
    finally:
        directory.chmod(0o755)


def interrupt_copy(h, target, *, after_replace=True):
    """Inject a local failure at the real rendered program's replacement boundary."""
    rendered = h.render(sync_data())
    replacement = "        os.replace(temporary, path)\n"
    assert rendered.count(replacement) == 1
    failure = f"        if path == Path({str(target)!r}):\n            raise OSError('injected copy interruption')\n"
    rendered = rendered.replace(
        replacement,
        replacement + failure if after_replace else failure + replacement,
        1,
    )
    result = subprocess.run(
        ["/bin/bash"],
        input=rendered,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PATH": str(h.bin) + os.pathsep + os.environ["PATH"]},
    )
    assert result.returncode == 0, result.stderr
    assert "injected copy interruption" in result.stderr


@pytest.mark.parametrize("existing", [False, True], ids=["new-copy", "existing-copy"])
@pytest.mark.parametrize("after_replace", [True, False], ids=["after-replacement", "before-replacement"])
def test_interrupted_copy_recovers_on_next_normal_apply(tmp_path, existing, after_replace):
    h = harness(tmp_path)
    if existing:
        h.run(sync_data(), apply=True)
    source = h.destination / PORTABLE / "alpha/SKILL.md"
    source.write_text("version two\n")
    target = h.destination / ".agents/skills/alpha/SKILL.md"
    interrupt_copy(h, target, after_replace=after_replace)
    assert h.calls() == ([IMPORT] if existing else [])
    if after_replace:
        assert target.read_bytes() == source.read_bytes()
    h.run(sync_data(), apply=True)
    assert target.read_bytes() == source.read_bytes()
    assert (tmp_path / "fake-store/alpha/SKILL.md").read_bytes() == source.read_bytes()
    assert h.calls() == ([IMPORT, IMPORT] if existing else [IMPORT])
    assert not receipt(h)["skills"]["alpha"].get("pending")
    h.run(sync_data(), apply=True)
    assert h.calls() == ([IMPORT, IMPORT] if existing else [IMPORT])


@pytest.mark.parametrize("existing", [False, True], ids=["new-copy", "existing-copy"])
@pytest.mark.parametrize("user_change", ["content", "mode"])
def test_interrupted_copy_preserves_intervening_user_identity(tmp_path, existing, user_change):
    h = harness(tmp_path)
    if existing:
        h.run(sync_data(), apply=True)
    (h.destination / PORTABLE / "alpha/SKILL.md").write_text("version two\n")
    target = h.destination / ".agents/skills/alpha/SKILL.md"
    interrupt_copy(h, target)
    if user_change == "content":
        target.write_text("third-party edit\n")
    else:
        target.chmod(0o600)
    before = (target.read_bytes(), target.stat().st_mode)
    assert "collision" in h.run(sync_data(), apply=True).lower()
    assert (target.read_bytes(), target.stat().st_mode) == before
    assert h.calls() == ([IMPORT] if existing else [])


def test_mode_only_source_changes_reach_copy_and_store_without_repeat_import(tmp_path):
    h = harness(tmp_path)
    source = write(h.destination / PORTABLE, "alpha/scripts/tool.sh", "#!/bin/sh\nexit 0\n")
    source.chmod(0o644)
    target = h.destination / ".agents/skills/alpha/scripts/tool.sh"
    store = tmp_path / "fake-store/alpha/scripts/tool.sh"
    for imports, mode in enumerate((0o644, 0o755, 0o644), start=1):
        source.chmod(mode)
        h.run(sync_data(), apply=True)
        assert target.read_bytes() == source.read_bytes() == store.read_bytes()
        assert target.stat().st_mode & 0o7777 == mode
        assert store.stat().st_mode & 0o7777 == mode
        assert h.calls() == [IMPORT] * imports
        before = (h.destination / RECEIPT).read_bytes()
        h.run(sync_data(), apply=True)
        assert h.calls() == [IMPORT] * imports
        assert (h.destination / RECEIPT).read_bytes() == before


@pytest.mark.parametrize("operation", ["content-update", "mode-update", "cleanup"])
def test_user_target_mode_change_is_preserved(tmp_path, operation):
    h = harness(tmp_path)
    source = h.destination / PORTABLE / "alpha/SKILL.md"
    source.chmod(0o644)
    h.run(sync_data(), apply=True)
    target = h.destination / ".agents/skills/alpha/SKILL.md"
    target.chmod(0o600)
    before = target.read_bytes()
    if operation == "content-update":
        source.write_text("new source bytes\n")
    elif operation == "mode-update":
        source.chmod(0o755)
    data = decisions(sync_skills=False) if operation == "cleanup" else sync_data()
    assert "collision" in h.run(data, apply=True).lower()
    assert target.read_bytes() == before
    assert target.stat().st_mode & 0o7777 == 0o600
    assert h.calls() == [IMPORT]


def test_source_special_mode_bits_are_not_copied(tmp_path):
    h = harness(tmp_path)
    source = write(h.destination / PORTABLE, "alpha/scripts/tool.sh", "#!/bin/sh\nexit 0\n")
    source.chmod(0o4755)
    h.run(sync_data(), apply=True)
    target = h.destination / ".agents/skills/alpha/scripts/tool.sh"
    assert target.stat().st_mode & 0o7777 == 0o755
    assert (tmp_path / "fake-store/alpha/scripts/tool.sh").stat().st_mode & 0o7777 == 0o755


@pytest.mark.parametrize(
    "pending",
    [
        {"path": "../outside", "identity": {"sha256": "0" * 64, "mode": 0o644}},
        {"path": "/outside", "identity": {"sha256": "0" * 64, "mode": 0o644}},
        {"path": "SKILL.md", "identity": {"sha256": "bad", "mode": 0o644}},
        {"path": "SKILL.md", "identity": {"sha256": "0" * 64, "mode": 0o4755}},
        {"path": "SKILL.md", "identity": {"sha256": "0" * 64, "mode": True}},
        [],
    ],
)
def test_invalid_pending_receipt_is_rejected_without_mutation(tmp_path, pending):
    h = harness(tmp_path)
    saved = json.dumps(
        {
            "version": 2,
            "skills": {"alpha": {"files": {}, "directories": [], "pending": pending}},
            "imports": {},
        }
    )
    write(h.destination, RECEIPT, saved)
    h.install()
    result = subprocess.run(
        h.command("apply", data=sync_data()),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PATH": str(h.bin) + os.pathsep + os.environ["PATH"]},
    )
    assert result.returncode != 0
    assert (h.destination / RECEIPT).read_text() == saved
    assert not (h.destination / ".agents").exists()
    assert not h.calls()


@pytest.mark.parametrize("enabled", [True, False], ids=["sync-enabled", "cleanup-disabled"])
def test_legacy_digest_only_receipt_is_preserved_without_mode_claim(tmp_path, enabled):
    h = harness(tmp_path)
    h.run(sync_data(), apply=True)
    entry = receipt(h)["skills"]["alpha"]
    root = h.destination / ".agents/skills/alpha"
    legacy = {
        "version": 1,
        "skills": {
            "alpha": {
                "files": {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in entry["files"]},
                "directories": entry["directories"],
            }
        },
        "imports": receipt(h)["imports"],
    }
    saved = json.dumps(legacy)
    (h.destination / RECEIPT).write_text(saved)
    target = root / "SKILL.md"
    target.chmod(0o600)
    before = (target.read_bytes(), target.stat().st_mode)
    data = sync_data() if enabled else decisions(sync_skills=False)
    result = subprocess.run(
        h.command("apply", data=data),
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PATH": str(h.bin) + os.pathsep + os.environ["PATH"]},
    )
    assert result.returncode != 0
    assert (h.destination / RECEIPT).read_text() == saved
    assert (target.read_bytes(), target.stat().st_mode) == before
    assert h.calls() == [IMPORT]
