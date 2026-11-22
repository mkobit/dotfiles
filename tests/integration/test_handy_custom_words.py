import json
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

SOURCE = Path("src/chezmoi")
HANDY = Path("Library/Application Support/com.pais.handy")
PROCESS_FIXTURE = Path("tests/integration/fixtures/handy_process.py")
SCRIPT_PATHS = (
    Path(".chezmoiscripts/handy/run_before_stop.sh.tmpl"),
    Path(".chezmoiscripts/handy/run_after_start.sh.tmpl"),
)


def fixture(tmp_path, data, *, running=True, process_error=False, quit_fails=False):
    # Apply copied source files to a test destination, not to the home directory.
    source = tmp_path / "source"
    destination = tmp_path / "dest"
    source.mkdir()
    destination.mkdir()
    for relative in [
        HANDY / "modify_private_settings_store.json",
        HANDY / ".chezmoiignore.tmpl",
        *SCRIPT_PATHS,
        Path(".chezmoitemplates/handy/settings"),
    ]:
        original = SOURCE / relative
        assert original.is_file(), f"The Handy source is missing: {original}"
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        # Exercise the macOS templates on every CI runner.
        target.write_text(
            original.read_text().replace('eq .chezmoi.os "darwin"', "true").replace('ne .chezmoi.os "darwin"', "false")
        )
    settings = destination / HANDY / "settings_store.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"settings": {"custom_words": ["existing"], "paste_method": "direct"}}))
    # The helper records app state and command counts for the assertions.
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"running": running, "quit": 0, "start": 0}))
    # Copy the static process helper into the test directory before execution.
    mock = tmp_path / "handy_process.py"
    shutil.copyfile(PROCESS_FIXTURE, mock)
    mock.chmod(0o755)
    mock_command = [str(mock), "--state", str(state), "--settings", str(settings)]
    if process_error:
        mock_command.append("--process-error")
    if quit_fails:
        mock_command.append("--quit-fails")
    # Replace process commands only in the test copies to avoid controlling real apps.
    scripts = [*(source / relative for relative in SCRIPT_PATHS), source / HANDY / "modify_private_settings_store.json"]
    for script in scripts:
        text = script.read_text()
        for command in ("pgrep", "osascript", "open"):
            text = text.replace("/usr/bin/" + command, shlex.join([*mock_command, command]))
        text = text.replace("sleep 0.1", ":")
        script.write_text(text)
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"data": data}))
    command = [
        "chezmoi",
        "--source",
        str(source),
        "--destination",
        str(destination),
        "--config",
        str(config),
        "--no-tty",
    ]
    return command, settings, state, destination


def apply(command, *paths):
    return subprocess.run([*command, "apply", *map(str, paths)], capture_output=True, text=True, check=False)


def test_handy_custom_words_preserve_existing_settings(tmp_path):
    command, settings, state, _ = fixture(
        tmp_path,
        {
            "handy": {"enabled": True, "custom_words": {"egm": "EGM", "chezmoi": "chezmoi", "zellij": "Zellij"}},
            "text_replacements": {"chi": "Kai", "egm": False, "zellij": "Zellij editor"},
        },
    )
    result = apply(command)
    assert result.returncode == 0, result.stderr
    assert json.loads(settings.read_text()) == {
        "settings": {
            "custom_words": ["Kai", "Zellij editor", "chezmoi"],
            "paste_method": "direct",
            "flushed": True,
        }
    }
    assert settings.stat().st_mode & 0o777 == 0o600
    assert json.loads(state.read_text()) == {"running": True, "quit": 1, "start": 1}
    original = settings.read_bytes()
    assert apply(command).returncode == 0
    assert settings.read_bytes() == original
    assert json.loads(state.read_text()) == {"running": True, "quit": 1, "start": 1}


def test_handy_nested_settings_and_api_keys(tmp_path, monkeypatch):
    command, settings, _, _ = fixture(
        tmp_path,
        {
            "handy": {
                "enabled": True,
                "settings": {
                    "selected_model": "new",
                    "bindings": {"transcribe": {"current_binding": "new"}},
                    "post_process_prompts": [{"id": "prompt", "prompt": "new"}],
                    "post_process_providers": [{"id": "provider", "base_url": "new"}],
                    "post_process_api_keys": {"ignored": "literal-key"},
                },
                "api_key_env": {"provider": "TEST_HANDY_KEY"},
            }
        },
    )
    settings.write_text(
        json.dumps(
            {
                "settings": {
                    "custom_words": [],
                    "bindings": {"transcribe": {"description": "keep"}},
                    "post_process_prompts": [{"id": "prompt", "name": "keep"}, {"id": "other"}],
                    "post_process_providers": [{"id": "provider", "name": "keep"}],
                    "post_process_api_keys": {"other": "keep"},
                }
            }
        )
    )
    monkeypatch.setenv("TEST_HANDY_KEY", "secret-value")
    result = apply(command)
    assert result.returncode == 0, result.stderr
    store = json.loads(settings.read_text())["settings"]
    assert store["bindings"]["transcribe"] == {"current_binding": "new", "description": "keep"}
    assert store["post_process_prompts"] == [{"id": "prompt", "name": "keep", "prompt": "new"}, {"id": "other"}]
    assert store["post_process_providers"] == [{"id": "provider", "name": "keep", "base_url": "new"}]
    assert store["post_process_api_keys"] == {"provider": "secret-value", "other": "keep"}
    monkeypatch.delenv("TEST_HANDY_KEY")
    result = apply(command)
    assert result.returncode == 0, result.stderr
    assert json.loads(settings.read_text())["settings"]["post_process_api_keys"] == store["post_process_api_keys"]


@pytest.mark.parametrize("process_error,quit_fails", [(True, False), (False, True)])
def test_handy_stop_errors_prevent_writes(tmp_path, process_error, quit_fails):
    command, settings, _, _ = fixture(
        tmp_path, {"handy": {"enabled": True}}, process_error=process_error, quit_fails=quit_fails
    )
    original = settings.read_bytes()
    assert apply(command).returncode != 0
    assert settings.read_bytes() == original


@pytest.mark.parametrize(
    "lifecycle,running,quit,start",
    [
        ({"stop_before_update": False}, True, 0, 0),
        ({"restart_after_update": False}, True, 1, 0),
        ({}, False, 0, 1),
    ],
)
def test_handy_lifecycle_options(tmp_path, lifecycle, running, quit, start):
    command, settings, state, destination = fixture(
        tmp_path, {"handy": {"enabled": True, "lifecycle": lifecycle}}, running=running
    )
    result = apply(command)
    assert result.returncode == 0, result.stderr
    assert json.loads(settings.read_text())["settings"]["custom_words"] == []
    status = json.loads(state.read_text())
    assert status["quit"] == quit
    assert status["start"] == start
    assert not (destination / ".cache/chezmoi/handy").exists()


def test_handy_changed_scoped_apply_requires_stop(tmp_path):
    command, settings, _, _ = fixture(tmp_path, {"handy": {"enabled": True}})
    original = settings.read_bytes()
    result = apply(command, settings)
    assert result.returncode != 0
    assert settings.read_bytes() == original


@pytest.mark.parametrize("enabled,missing", [(False, False), (True, True)])
def test_handy_disabled_or_missing_is_a_noop(tmp_path, enabled, missing):
    command, settings, state, _ = fixture(tmp_path, {"handy": {"enabled": enabled}})
    original = settings.read_bytes()
    original_mode = settings.stat().st_mode
    if missing:
        settings.unlink()
    result = apply(command)
    assert result.returncode == 0, result.stderr
    if missing:
        assert not settings.exists()
    else:
        assert settings.read_bytes() == original
        assert settings.stat().st_mode == original_mode
    assert json.loads(state.read_text()) == {"running": True, "quit": 0, "start": 0}


def test_handy_lifecycle_scripts_do_not_contain_api_keys(tmp_path, monkeypatch):
    command, _, _, _ = fixture(
        tmp_path,
        {
            "handy": {
                "enabled": True,
                "api_key_env": {"provider": "TEST_HANDY_KEY"},
            }
        },
    )
    monkeypatch.setenv("TEST_HANDY_KEY", "secret-value")
    source = tmp_path / "source"
    for relative in SCRIPT_PATHS:
        path = source / relative
        rendered = subprocess.run(
            [*command, "execute-template", "-f", str(path)],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert "secret-value" not in rendered


def test_handy_starts_when_settings_are_already_current(tmp_path):
    command, settings, state, _ = fixture(tmp_path, {"handy": {"enabled": True}}, running=False)
    settings.write_text(json.dumps({"settings": {"custom_words": [], "paste_method": "direct"}}))
    original = settings.read_bytes()
    result = apply(command)
    assert result.returncode == 0, result.stderr
    assert settings.read_bytes() == original
    assert json.loads(state.read_text()) == {"running": True, "quit": 0, "start": 1}


def test_handy_scoped_apply_is_safe_when_app_is_stopped(tmp_path):
    command, settings, state, _ = fixture(tmp_path, {"handy": {"enabled": True}}, running=False)
    result = apply(command, settings)
    assert result.returncode == 0, result.stderr
    assert json.loads(settings.read_text())["settings"]["custom_words"] == []
    assert json.loads(state.read_text()) == {"running": False, "quit": 0, "start": 0}
