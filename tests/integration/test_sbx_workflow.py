"""Check the workflow schema through chezmoi data loading and init rendering."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "src/chezmoi"
INIT_TEMPLATE = SOURCE / ".chezmoi.toml.tmpl"
DECISIONS = {
    "ai.workflow.enabled": False,
    "ai.sandbox.provider": "none",
    "ai.sandbox.default_clone_mode": False,
    "ai.sandbox.network_policy": "",
    "ai.sandbox.proxy_gh_secret": False,
    "ai.sandbox.sync_skills": False,
    "sbx.settings.skills_default_mode": "",
    "ai.signing.mode": "host-default",
    "ai.signing.ssh_public_key": "",
    "ai.signing.gpg_subkey_id": "",
    "ai.ollama.enabled": False,
    "ai.ollama.host_url": "",
    "ai.ollama.sandbox_url": "",
    "ai.ollama.default_coder_model": "",
}


@pytest.fixture
def workflow_source(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(SOURCE / ".chezmoidata", source / ".chezmoidata")
    return source


def _chezmoi(tmp_path, source, *args, config_text=None, override=None):
    config = tmp_path / "chezmoi.toml"
    if config_text is not None or not config.exists():
        config.write_text(config_text or "", encoding="utf-8")
    destination = tmp_path / "destination"
    destination.mkdir(exist_ok=True)
    result = subprocess.run(
        [
            "chezmoi",
            "--config",
            str(config),
            "--source",
            str(source),
            "--destination",
            str(destination),
            "--cache",
            str(tmp_path / "cache"),
            "--persistent-state",
            str(tmp_path / "state.boltdb"),
            "--no-tty",
            "--override-data",
            json.dumps(override or {}),
            *args,
        ],
        env={**os.environ, "CI": "true"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _data(tmp_path, source, config_text=None):
    return json.loads(_chezmoi(tmp_path, source, "data", "--format=json", config_text=config_text))


def _init(tmp_path, source, os_name="linux"):
    return _chezmoi(
        tmp_path,
        source,
        "execute-template",
        "--init",
        "--file",
        str(INIT_TEMPLATE),
        override={"chezmoi": {"os": os_name}},
    )


def _decisions(tmp_path, source):
    # Resolve the published interface without adding a setup consumer in this checkpoint.
    template = "{{ dict "
    for path, default in DECISIONS.items():
        keys = " ".join(json.dumps(key) for key in path.split("."))
        template += f"{json.dumps(path)} (dig {keys} {json.dumps(default)} .) "
    template += "| toJson }}"
    return json.loads(_chezmoi(tmp_path, source, "execute-template", template))


def test_catalog_declares_extensible_capability_maps(tmp_path, workflow_source):
    ai = _data(tmp_path, workflow_source)["ai"]
    assert ai["sandbox"]["providers"]["sbx"]["description"]
    assert set(ai["signing"]["modes"]) == {"host-default", "ssh-forwarded", "gpg-subkey"}
    assert all(mode["description"] for mode in ai["signing"]["modes"].values())
    assert ai["workflow"]["description"]
    assert ai["ollama"]["description"]
    assert isinstance(ai["skills"]["authored"], dict)
    assert isinstance(ai["command_policy"]["commands"], dict)
    assert "permissions" not in ai
    assert "skills_mode" not in ai["sandbox"]
    assert "enabled_list" not in ai["skills"]
    assert "disabled_list" not in ai["skills"]


@pytest.mark.parametrize("with_catalog", [False, True], ids=["no-ai-data", "catalog-only"])
def test_missing_decisions_resolve_to_safe_defaults(tmp_path, workflow_source, with_catalog):
    source = workflow_source if with_catalog else tmp_path / "empty-source"
    source.mkdir(exist_ok=True)
    data = _data(tmp_path, source)
    for path in DECISIONS:
        value = data
        for key in path.split(".")[:-1]:
            value = value.get(key, {})
        assert path.split(".")[-1] not in value, f"Catalog selected {path}"
    assert _decisions(tmp_path, source) == DECISIONS


@pytest.mark.parametrize("os_name", ["linux", "darwin"])
def test_personal_init_selects_workflow_without_selecting_a_signing_key(tmp_path, workflow_source, os_name):
    config = _init(tmp_path, workflow_source, os_name)
    data = _data(tmp_path, workflow_source, config_text=config)
    ai = data["ai"]
    enabled = os_name == "linux"
    assert ai["workflow"]["enabled"] is enabled
    assert ai["sandbox"]["provider"] == ("sbx" if enabled else "none")
    assert ai["sandbox"]["default_clone_mode"] is False
    assert ai["sandbox"]["network_policy"] == "balanced"
    assert ai["sandbox"]["proxy_gh_secret"] is True
    assert ai["sandbox"]["sync_skills"] is True
    assert data["sbx"]["settings"]["skills_default_mode"] == "readonly"
    assert ai["signing"]["mode"] == "ssh-forwarded"
    assert ai["signing"]["ssh_public_key"] == ""
    assert ai["signing"]["gpg_subkey_id"] == ""
    assert ai["ollama"]["enabled"] is enabled
    assert ai["ollama"]["host_url"] == "http://localhost:11434"
    assert ai["ollama"]["sandbox_url"] == "http://host.docker.internal:11434"
    assert ai["ollama"]["default_coder_model"] == "qwen3-coder:30b"
    # Rendering must use the isolated deployment target.
    assert f'MISE_CONFIG_DIR = "{tmp_path}/destination/.config/mise"' in config


def test_explicit_disabled_overlay_decisions_survive_data_merge(tmp_path, workflow_source):
    _data(
        tmp_path,
        workflow_source,
        config_text="""[data.ai.workflow]
enabled = false
[data.ai.sandbox]
provider = "none"
default_clone_mode = false
network_policy = ""
proxy_gh_secret = false
sync_skills = false
[data.sbx.settings]
skills_default_mode = "off"
[data.ai.signing]
mode = "host-default"
[data.ai.ollama]
enabled = false
""",
    )
    assert _decisions(tmp_path, workflow_source) == {**DECISIONS, "sbx.settings.skills_default_mode": "off"}


def test_overlay_maps_extend_capabilities_and_existing_catalogs(tmp_path, workflow_source):
    baseline = _data(tmp_path, workflow_source)
    (workflow_source / ".chezmoidata/zz-workflow-overlay.toml").write_text(
        """[ai.sandbox.providers.sbx]
description = "Overlay SBX capability."
[ai.sandbox.providers.example]
description = "Overlay sandbox capability."
[ai.signing.modes.example]
description = "Overlay signing capability."
[ai.skills.authored]
example = "present"
[ai.command_policy.commands]
"example inspect" = "allow"
""",
        encoding="utf-8",
    )
    data = _data(tmp_path, workflow_source)
    ai = data["ai"]
    assert ai["sandbox"]["providers"]["sbx"]["description"] == "Overlay SBX capability."
    assert ai["sandbox"]["providers"]["example"]["description"] == "Overlay sandbox capability."
    assert set(ai["signing"]["modes"]) == {*baseline["ai"]["signing"]["modes"], "example"}
    assert ai["skills"]["authored"] == {**baseline["ai"]["skills"]["authored"], "example": "present"}
    assert ai["command_policy"]["commands"] == {
        **baseline["ai"]["command_policy"]["commands"],
        "example inspect": "allow",
    }
    assert data["sbx"]["settings"]["kit_allowed_sources"] == baseline["sbx"]["settings"]["kit_allowed_sources"]
    assert _decisions(tmp_path, workflow_source) == DECISIONS


def test_overlay_control_plane_selects_values_and_overrides_catalog(tmp_path, workflow_source):
    (workflow_source / ".chezmoidata/zz-workflow-overlay.toml").write_text(
        '[ai.sandbox]\nprovider = "catalog-provider"\n[ai.ollama]\nhost_url = "http://catalog.invalid"\n',
        encoding="utf-8",
    )
    data = _data(
        tmp_path,
        workflow_source,
        config_text="""[data.ai.workflow]
enabled = true
[data.ai.sandbox]
provider = "overlay-provider"
default_clone_mode = true
network_policy = "custom"
proxy_gh_secret = false
sync_skills = false
[data.sbx.settings]
skills_default_mode = "readwrite"
[data.ai.signing]
mode = "gpg-subkey"
gpg_subkey_id = "EXPLICIT-SUBKEY-FIXTURE"
[data.ai.ollama]
enabled = true
host_url = "http://model-host.invalid:11434"
sandbox_url = "http://model-guest.invalid:11434"
default_coder_model = "overlay-model"
""",
    )
    assert _decisions(tmp_path, workflow_source) == {
        **DECISIONS,
        "ai.workflow.enabled": True,
        "ai.sandbox.provider": "overlay-provider",
        "ai.sandbox.default_clone_mode": True,
        "ai.sandbox.network_policy": "custom",
        "sbx.settings.skills_default_mode": "readwrite",
        "ai.signing.mode": "gpg-subkey",
        "ai.signing.gpg_subkey_id": "EXPLICIT-SUBKEY-FIXTURE",
        "ai.ollama.enabled": True,
        "ai.ollama.host_url": "http://model-host.invalid:11434",
        "ai.ollama.sandbox_url": "http://model-guest.invalid:11434",
        "ai.ollama.default_coder_model": "overlay-model",
    }
    assert "sbx" in data["ai"]["sandbox"]["providers"]
    assert "ssh-forwarded" in data["ai"]["signing"]["modes"]
