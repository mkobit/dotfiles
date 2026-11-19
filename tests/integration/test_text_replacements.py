import importlib.util
import json
import os
import sqlite3
import subprocess
import time
import tomllib
from pathlib import Path

import pytest


def load_sync():
    source = Path.cwd() / "src/chezmoi/.chezmoitemplates/text-replacements/sync.py"
    assert source.is_file()
    spec = importlib.util.spec_from_file_location("text_replacements_sync", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plan_preserves_unmanaged_entries_and_updates_managed_shortcuts():
    sync = load_sync()
    changes = sync.plan_changes(
        {"EGM": "Elephant-Goldfish Model", "chesmoir": "chezmoi"},
        [("EGM", "old phrase"), ("other", "keep"), ("chesmoir", "chezmoi")],
    )
    assert changes == [("add", "EGM", "Elephant-Goldfish Model"), ("remove", "EGM", "old phrase")]


def test_plan_adds_missing_entries_and_is_idempotent():
    sync = load_sync()
    desired = {"EGM": "Elephant-Goldfish Model"}
    assert sync.plan_changes(desired, []) == [("add", "EGM", "Elephant-Goldfish Model")]
    assert sync.plan_changes(desired, [("EGM", "Elephant-Goldfish Model")]) == []


def test_configured_zellij_replacements_are_added():
    data = tomllib.loads(Path("src/chezmoi/.chezmoidata/text_replacements.toml").read_text())
    changes = load_sync().plan_changes(data["text_replacement_pairs"], [])
    assert ("add", "Zealage", "Zellij") in changes
    assert ("add", "zelleedge", "Zellij") in changes


def test_read_current_ignores_deleted_entries(tmp_path):
    sync = load_sync()
    database = tmp_path / "replacements.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE ZTEXTREPLACEMENTENTRY (ZSHORTCUT TEXT, ZPHRASE TEXT, ZWASDELETED INTEGER)")
        connection.executemany(
            "INSERT INTO ZTEXTREPLACEMENTENTRY VALUES (?, ?, ?)",
            [("EGM", "Elephant-Goldfish Model", 0), ("old", "deleted", 1)],
        )
    assert sync.read_current(database) == [("EGM", "Elephant-Goldfish Model")]


def test_missing_database_is_empty(tmp_path):
    assert load_sync().read_current(tmp_path / "missing.db") == []


def test_handy_custom_words_include_base_and_overlay_without_removing_existing(tmp_path):
    template = Path.cwd() / "src/chezmoi/Library/Application Support/com.pais.handy/modify_settings_store.json"
    result = subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(tmp_path),
            "execute-template",
            "-f",
            "--with-stdin",
            "--override-data",
            json.dumps(
                {
                    "text_replacement_pairs": {"chesmoir": "chezmoi"},
                    "text_replacements": {"chi": "Kai"},
                    "handy": {"custom_words": {"zellij": "Zellij"}},
                }
            ),
            str(template),
        ],
        input=json.dumps({"settings": {"custom_words": ["existing"]}}),
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["settings"]["custom_words"] == ["Kai", "Zellij", "chezmoi", "existing"]


def test_handy_custom_words_can_be_configured_without_replacement_pairs(tmp_path):
    source = Path.cwd() / "src/chezmoi/Library/Application Support/com.pais.handy"
    target = tmp_path / "Library/Application Support/com.pais.handy/settings_store.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}")
    options = [
        "chezmoi",
        "--config",
        "/dev/null",
        "--config-format",
        "toml",
        "--source",
        str(tmp_path),
        "--destination",
        str(tmp_path),
        "execute-template",
        "-f",
        "--override-data",
        json.dumps({"handy": {"custom_words": {"zellij": "Zellij"}}}),
    ]
    ignored = subprocess.run(
        [*options, str(source / ".chezmoiignore.tmpl")], capture_output=True, text=True, check=True
    )
    assert "settings_store.json" not in ignored.stdout
    result = subprocess.run(
        [*options, "--with-stdin", str(source / "modify_settings_store.json")],
        input=json.dumps({"settings": {"custom_words": ["existing"]}}),
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["settings"]["custom_words"] == ["Zellij", "existing"]


@pytest.mark.parametrize("template_kind", ["base", "overlay"])
@pytest.mark.parametrize("enabled", [None, False, True])
@pytest.mark.parametrize("previous_path", [None, "/old/script"])
def test_handy_paste_script_is_opt_in_and_preserves_other_settings(tmp_path, template_kind, enabled, previous_path):
    if template_kind == "overlay":
        overlay_template = os.environ.get("HANDY_OVERLAY_TEMPLATE")
        if not overlay_template:
            pytest.skip("No overlay template supplied")
        template = Path(overlay_template)
    else:
        template = Path.cwd() / "src/chezmoi/Library/Application Support/com.pais.handy/modify_settings_store.json"

    settings = {"custom_words": ["existing"], "paste_method": "direct", "external_script_path": previous_path}
    store = {"settings": settings, "unrelated": "keep"}
    handy = {} if enabled is None else {"use_paste_script": enabled}
    result = subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(tmp_path),
            "--destination",
            str(tmp_path),
            "execute-template",
            "-f",
            "--with-stdin",
            "--override-data",
            json.dumps({"handy": handy}),
            str(template),
        ],
        input=json.dumps(store),
        capture_output=True,
        text=True,
        check=True,
    )
    expected = {"settings": dict(settings), "unrelated": "keep"}
    if enabled:
        expected["settings"]["paste_method"] = "external_script"
        expected["settings"]["external_script_path"] = str(tmp_path / ".local/bin/handy-paste")
    assert json.loads(result.stdout) == expected
    repeated = subprocess.run(result.args, input=result.stdout, capture_output=True, text=True, check=True)
    assert repeated.stdout == result.stdout


def test_failed_helper_reports_its_error(monkeypatch, tmp_path):
    sync = load_sync()

    def fail(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, stderr="keyboard service rejected request")

    monkeypatch.setattr(sync.subprocess, "run", fail)
    with pytest.raises(RuntimeError, match="keyboard service rejected request"):
        sync.apply_changes(Path("helper"), tmp_path / "database", [("add", "EGM", "elephant-goldfish model")])


def test_update_waits_for_macos_database_changes(monkeypatch, tmp_path):
    sync = load_sync()
    database = tmp_path / "replacements.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE ZTEXTREPLACEMENTENTRY (ZSHORTCUT TEXT, ZPHRASE TEXT, ZWASDELETED INTEGER)")
        connection.executemany(
            "INSERT INTO ZTEXTREPLACEMENTENTRY VALUES (?, ?, 0)", [("EGM", "old phrase"), ("other", "keep")]
        )

    pending = []
    monkeypatch.setattr(sync.subprocess, "run", lambda command, **kwargs: pending.append(command[1:]))

    def publish_changes(_seconds):
        with sqlite3.connect(database) as connection:
            while pending:
                action, shortcut, phrase = pending.pop(0)
                if action == "add":
                    connection.execute("INSERT INTO ZTEXTREPLACEMENTENTRY VALUES (?, ?, 0)", (shortcut, phrase))
                else:
                    connection.execute(
                        "UPDATE ZTEXTREPLACEMENTENTRY SET ZWASDELETED = 1 WHERE ZSHORTCUT = ? AND ZPHRASE = ?",
                        (shortcut, phrase),
                    )

    monkeypatch.setattr(time, "sleep", publish_changes)
    desired = {"EGM": "elephant-goldfish model"}
    sync.apply_changes(Path("helper"), database, sync.plan_changes(desired, sync.read_current(database)))
    assert sorted(sync.read_current(database)) == [("EGM", "elephant-goldfish model"), ("other", "keep")]


def test_failed_add_does_not_remove_previous_phrase(monkeypatch, tmp_path):
    sync = load_sync()
    calls = []

    def fail_add(command, **kwargs):
        calls.append(command[1])
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(sync.subprocess, "run", fail_add)
    changes = sync.plan_changes({"EGM": "Elephant-Goldfish Model"}, [("EGM", "old phrase")])
    try:
        sync.apply_changes(Path("helper"), tmp_path / "database", changes)
    except RuntimeError:
        pass
    else:
        raise AssertionError("The failed add must be reported")
    assert calls == ["add"]


def test_unsaved_add_does_not_remove_previous_phrase(monkeypatch, tmp_path):
    sync = load_sync()
    calls = []
    monkeypatch.setattr(sync, "CHANGE_TIMEOUT_SECONDS", 0)
    monkeypatch.setattr(sync.subprocess, "run", lambda command, **kwargs: calls.append(command[1]))
    changes = sync.plan_changes({"EGM": "Elephant-Goldfish Model"}, [("EGM", "old phrase")])
    try:
        sync.apply_changes(Path("helper"), tmp_path / "database", changes)
    except RuntimeError:
        pass
    else:
        raise AssertionError("An unsaved add must be reported")
    assert calls == ["add"]
