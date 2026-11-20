import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

TEMPLATE = Path("src/chezmoi/.chezmoiscripts/run_after_manage-handy.py.tmpl")


def render(tmp_path, data):
    assert TEMPLATE.is_file(), "The Handy management script is missing"
    return subprocess.run(
        [
            "chezmoi", "--source", str(tmp_path), "--destination", str(tmp_path),
            "--config", "/dev/null", "--config-format", "toml", "execute-template",
            "-f", "--override-data", json.dumps(data), str(TEMPLATE),
        ],
        capture_output=True, text=True, check=True,
    ).stdout


def load(tmp_path, data):
    namespace = {"__name__": "handy_test"}
    exec(render(tmp_path, data), namespace)
    return namespace


def store_path(tmp_path, initial):
    path = tmp_path / "Library/Application Support/com.pais.handy/settings_store.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(initial))
    return path


def test_handy_custom_words_preserve_existing_settings(tmp_path):
    data = {
        "handy": {
            "enabled": True,
            "lifecycle": {"stop_before_update": False},
            "custom_words": {"egm": "EGM", "chezmoi": "chezmoi", "zellij": "Zellij"},
        },
        "text_replacements": {"chi": "Kai", "egm": False, "zellij": "Zellij editor"},
    }
    path = store_path(tmp_path, {"settings": {"custom_words": ["existing", "chezmoi"], "paste_method": "direct"}})
    script = load(tmp_path, data)
    script["main"]()
    assert json.loads(path.read_text()) == {
        "settings": {"custom_words": ["Kai", "Zellij editor", "chezmoi"], "paste_method": "direct"}
    }
    result = path.read_bytes()
    script["main"]()
    assert path.read_bytes() == result


@pytest.mark.parametrize("data", [{}, {"handy": {"enabled": False}}])
def test_handy_disabled_renders_no_script(tmp_path, data):
    assert render(tmp_path, data).strip() == ""


def test_handy_missing_settings_is_a_noop(tmp_path):
    script = load(tmp_path, {"handy": {"enabled": True}})
    script["main"]()
    assert not (tmp_path / "Library").exists()


def test_handy_settings_merge_after_quit_and_keep_api_keys(tmp_path, monkeypatch):
    data = {
        "handy": {
            "enabled": True,
            "settings": {
                "selected_model": "new-model",
                "bindings": {"transcribe": {"current_binding": "new"}},
                "post_process_prompts": [{"id": "prompt", "prompt": "new prompt"}],
                "post_process_providers": [{"id": "provider", "base_url": "new-url"}],
                "post_process_api_keys": {"ignored": "not-an-env-key"},
            },
            "api_key_env": {"provider": "TEST_HANDY_KEY"},
        },
    }
    initial = {"settings": {
        "selected_model": "old", "custom_words": [],
        "bindings": {"transcribe": {"current_binding": "old", "description": "keep"}},
        "post_process_prompts": [{"id": "prompt", "prompt": "old", "name": "keep"}, {"id": "other"}],
        "post_process_providers": [{"id": "provider", "base_url": "old", "name": "keep"}],
        "post_process_api_keys": {"other": "keep"},
    }}
    path = store_path(tmp_path, initial)
    monkeypatch.setenv("TEST_HANDY_KEY", "secret-value")
    assert "secret-value" not in render(tmp_path, data)
    script = load(tmp_path, data)
    state = {"running": True, "quit": 0, "start": 0}

    def run(command, **kwargs):
        if command[0] == "/usr/bin/pgrep":
            return SimpleNamespace(returncode=0 if state["running"] else 1)
        if command[0] == "/usr/bin/osascript":
            initial["settings"]["flushed"] = True
            path.write_text(json.dumps(initial))
            state["running"] = False
            state["quit"] += 1
        elif command[0] == "/usr/bin/open":
            state["running"] = True
            state["start"] += 1
        else:
            raise AssertionError(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(script["subprocess"], "run", run)
    script["main"]()
    settings = json.loads(path.read_text())["settings"]
    assert settings["flushed"] is True
    assert settings["selected_model"] == "new-model"
    assert settings["bindings"]["transcribe"] == {"current_binding": "new", "description": "keep"}
    assert settings["post_process_prompts"] == [{"id": "prompt", "prompt": "new prompt", "name": "keep"}, {"id": "other"}]
    assert settings["post_process_providers"] == [{"id": "provider", "base_url": "new-url", "name": "keep"}]
    assert settings["post_process_api_keys"] == {"provider": "secret-value", "other": "keep"}
    assert path.stat().st_mode & 0o777 == 0o600
    assert state == {"running": True, "quit": 1, "start": 1}
    script["main"]()
    assert state == {"running": True, "quit": 1, "start": 1}
    monkeypatch.delenv("TEST_HANDY_KEY")
    script["main"]()
    assert json.loads(path.read_text())["settings"]["post_process_api_keys"]["provider"] == "secret-value"


@pytest.mark.parametrize("was_running,restart,expected_start", [(False, True, 0), (True, False, 0)])
def test_handy_restart_can_be_disabled(tmp_path, monkeypatch, was_running, restart, expected_start):
    path = store_path(tmp_path, {"settings": {"selected_model": "old"}})
    script = load(tmp_path, {"handy": {
        "enabled": True, "settings": {"selected_model": "new"},
        "lifecycle": {"restart_after_update": restart},
    }})
    state = {"running": was_running, "start": 0}

    def run(command, **kwargs):
        if command[0] == "/usr/bin/pgrep":
            return SimpleNamespace(returncode=0 if state["running"] else 1)
        if command[0] == "/usr/bin/osascript":
            state["running"] = False
        elif command[0] == "/usr/bin/open":
            state["start"] += 1
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(script["subprocess"], "run", run)
    script["main"]()
    assert json.loads(path.read_text())["settings"]["selected_model"] == "new"
    assert state["start"] == expected_start


def test_handy_does_not_write_when_quit_fails(tmp_path, monkeypatch):
    path = store_path(tmp_path, {"settings": {"selected_model": "old"}})
    original = path.read_bytes()
    script = load(tmp_path, {"handy": {"enabled": True, "settings": {"selected_model": "new"}}})
    monkeypatch.setattr(script["subprocess"], "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    monkeypatch.setattr(script["time"], "sleep", lambda _: None)
    with pytest.raises(RuntimeError):
        script["main"]()
    assert path.read_bytes() == original


def test_handy_does_not_write_when_process_check_fails(tmp_path, monkeypatch):
    path = store_path(tmp_path, {"settings": {"selected_model": "old"}})
    original = path.read_bytes()
    script = load(tmp_path, {"handy": {"enabled": True, "settings": {"selected_model": "new"}}})
    monkeypatch.setattr(script["subprocess"], "run", lambda *args, **kwargs: SimpleNamespace(returncode=2))
    with pytest.raises(RuntimeError):
        script["main"]()
    assert path.read_bytes() == original
