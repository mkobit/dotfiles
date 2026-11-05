"""Check local model routing with disposable Chezmoi targets and a fake SBX CLI."""

import copy
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "src/chezmoi"
HOOK = ".chezmoiscripts/run_after_08_configure-local-models.sh.tmpl"
OPEN_CODE = ".config/opencode/opencode.json"
PI_MODELS = ".pi/agent/models.json"
PI_SETTINGS = ".pi/agent/settings.json"
MODEL = "qwen3-coder:30b"
ROOT = "http://model.invalid:11434"
ENABLED = {
    "mise": {},
    "local": {
        "bin": {"opencode": {"installation_method": "preinstalled"}, "sbx": {"installation_method": "preinstalled"}}
    },
    "ai": {
        "workflow": {"enabled": False},
        "sandbox": {"provider": "sbx"},
        "ollama": {
            "enabled": True,
            "host_url": ROOT + "///",
            "sandbox_url": "http://guest.invalid:11434//",
            "default_coder_model": MODEL,
        },
    },
}
KEYS = ("platform.allowExperimentalFeatures", "feature.model", "model.providers")


def native_records():
    return {
        KEYS[0]: {"key": KEYS[0], "type": "bool", "value": False},
        KEYS[1]: {
            "key": KEYS[1],
            "type": "json",
            "feature_flag": True,
            "value": {"enabled": False, "variant": "custom", "variantPayload": {"private": "fake-private"}, "extra": 7},
        },
        KEYS[2]: {
            "key": KEYS[2],
            "type": "json",
            "value": {
                "foreign": {"url": "http://foreign.invalid", "private": "fake-private"},
                "ollama-configured": {"url": "http://old.invalid", "wire": "old", "custom": {"keep": True}},
            },
        },
    }


class RoutingHarness:
    """Keep all configuration and command state in a disposable directory."""

    def __init__(self, root, *, hook=False):
        self.root = root
        self.source = root / "src/chezmoi"
        self.destination = root / "destination"
        self.bin = root / "bin"
        self.source.mkdir(parents=True)
        self.destination.mkdir()
        self.bin.mkdir()
        self.config = root / "config.json"
        self.config.write_text("{}")
        paths = (
            (HOOK, ".chezmoitemplates/python/filter-interpreter", "../python/skill_filter/resolve-interpreter.sh")
            if hook
            else (
                ".chezmoiignore.tmpl",
                "dot_config/opencode/modify_opencode.json",
                "dot_pi/agent/modify_private_models.json",
                "dot_pi/agent/modify_private_settings.json",
            )
        )
        for relative in paths:
            origin = SOURCE / relative
            assert origin.is_file(), f"routing source is absent: {relative}"
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin, target)
        self.state_file = root / "fake-sbx.json"
        self.save({"records": native_records(), "calls": []})
        self._fake_cli()

    def _fake_cli(self):
        script = (
            f"#!{sys.executable}\nSTATE = {str(self.state_file)!r}\n"
            r"""
import json
import sys
from pathlib import Path
p = Path(STATE)
s = json.loads(p.read_text())
a = sys.argv[1:]
s['calls'].append(a)
p.write_text(json.dumps(s))
if a in s.get('fail', []):
    print('fake-private-stdout')
    print('fake-private-stderr', file=sys.stderr)
    sys.exit(1)
if len(a) == 4 and a[:2] == ['settings', 'get'] and a[2] in s['records'] and a[3] == '--json':
    print(s.get('raw', {}).get(a[2], json.dumps(s['records'][a[2]])))
elif len(a) == 4 and a[:2] == ['settings', 'set'] and a[2] in s['records']:
    s['records'][a[2]]['value'] = json.loads(a[3])
else:
    s['unexpected'] = a
    p.write_text(json.dumps(s))
    sys.exit(93)
p.write_text(json.dumps(s))
"""
        )
        fake = self.bin / "sbx"
        fake.write_text(script)
        fake.chmod(0o755)

    def save(self, state):
        self.state_file.write_text(json.dumps(state))

    def state(self):
        return json.loads(self.state_file.read_text())

    def calls(self):
        state = self.state()
        assert "unexpected" not in state, state
        return state["calls"]

    def seed(self, relative, value):
        target = self.destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value if isinstance(value, str) else json.dumps(value))
        return target

    def run(self, *args, data=None):
        env = {**os.environ, "PATH": str(self.bin) + os.pathsep + os.environ["PATH"]}
        return subprocess.run(
            [
                "chezmoi",
                "--config",
                str(self.config),
                "--source",
                str(self.source),
                "--destination",
                str(self.destination),
                "--cache",
                str(self.root / "cache"),
                "--persistent-state",
                str(self.root / "chezmoi.boltdb"),
                "--no-tty",
                "--override-data",
                json.dumps(ENABLED if data is None else data),
                *args,
            ],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def apply(self, data=None):
        preview = self.run("diff", data=data)
        assert preview.returncode == 0, preview.stderr
        result = self.run("apply", data=data)
        assert result.returncode == 0, result.stderr
        assert "fake-private" not in result.stdout + result.stderr
        return result

    def read(self, relative):
        return json.loads((self.destination / relative).read_text())


def test_host_apply_preserves_fields_and_is_stable(tmp_path):
    h = RoutingHarness(tmp_path)
    opencode = {
        "plugin": ["custom-plugin"],
        "model": "foreign/model",
        "extra": {"keep": True},
        "provider": {
            "foreign": {"options": {"apiKey": "fake-key"}},
            "ollama": {
                "extra": 1,
                "options": {"headers": {"keep": "yes"}, "baseURL": "old"},
                "models": {MODEL: {"name": "old", "limit": {"context": 123}}, "other:tag": {"name": "Other"}},
            },
        },
    }
    models = {
        "extra": True,
        "providers": {
            "foreign": {"apiKey": "fake-key"},
            "ollama": {
                "extra": 1,
                "models": [{"id": "other:tag", "name": "Other"}, {"id": MODEL, "name": "Keep", "contextWindow": 123}],
            },
        },
    }
    settings = {"defaultProvider": "foreign", "defaultModel": "old", "theme": "custom"}
    h.seed(OPEN_CODE, opencode)
    h.seed(PI_MODELS, models)
    h.seed(PI_SETTINGS, settings)
    h.apply()
    expected = copy.deepcopy(opencode)
    expected["model"] = "ollama/" + MODEL
    expected["provider"]["ollama"].update({"npm": "@ai-sdk/openai-compatible", "name": "Ollama (configured)"})
    expected["provider"]["ollama"]["options"]["baseURL"] = ROOT + "/v1"
    expected["provider"]["ollama"]["models"][MODEL]["name"] = MODEL
    assert h.read(OPEN_CODE) == expected
    expected_models = copy.deepcopy(models)
    expected_models["providers"]["ollama"].update(
        {"baseUrl": ROOT + "/v1", "api": "openai-completions", "apiKey": "ollama"}
    )
    assert h.read(PI_MODELS) == expected_models
    assert h.read(PI_SETTINGS) == {**settings, "defaultProvider": "ollama", "defaultModel": MODEL}
    paths = [h.destination / p for p in (OPEN_CODE, PI_MODELS, PI_SETTINGS)]
    before = [p.read_bytes() for p in paths]
    assert all(stat.S_IMODE(p.stat().st_mode) == 0o600 for p in paths[1:])
    h.apply()
    assert [p.read_bytes() for p in paths] == before
    disabled = copy.deepcopy(ENABLED)
    disabled["ai"]["ollama"]["enabled"] = False
    h.apply(disabled)
    assert [p.read_bytes() for p in paths] == before


def test_host_apply_creates_minimal_models_without_capability_guesses(tmp_path):
    h = RoutingHarness(tmp_path)
    h.apply()
    assert h.read(PI_MODELS) == {
        "providers": {
            "ollama": {
                "baseUrl": ROOT + "/v1",
                "api": "openai-completions",
                "apiKey": "ollama",
                "models": [{"id": MODEL}],
            }
        }
    }
    assert h.read(PI_SETTINGS) == {"defaultProvider": "ollama", "defaultModel": MODEL}
    models = h.read(PI_MODELS)
    models["providers"]["ollama"]["models"] = [{"id": "foreign:tag", "name": "Keep"}]
    h.seed(PI_MODELS, models)
    h.apply()
    assert h.read(PI_MODELS)["providers"]["ollama"]["models"] == [{"id": "foreign:tag", "name": "Keep"}, {"id": MODEL}]


@pytest.mark.parametrize("ai", [None, {}, {"ollama": {}}, {"ollama": {"enabled": False}}])
@pytest.mark.parametrize("existing", [False, True])
def test_disabled_routing_preserves_bytes_and_does_not_create_pi(tmp_path, ai, existing):
    h = RoutingHarness(tmp_path)
    data = {"mise": {}, "local": {"bin": {"opencode": {"installation_method": "preinstalled"}}}}
    if ai is not None:
        data["ai"] = ai
    original = '{ "model" : "custom", "plugin" : ["custom"] }\n'
    h.seed(OPEN_CODE, original)
    if existing:
        for relative in (PI_MODELS, PI_SETTINGS):
            h.seed(relative, original)
    h.apply(data)
    assert (h.destination / OPEN_CODE).read_text() == original
    for relative in (PI_MODELS, PI_SETTINGS):
        path = h.destination / relative
        assert path.read_text() == original if existing else not path.exists()


@pytest.mark.parametrize("gate", ["provider", "sbx", "local", "ai", "ollama", "enabled"])
def test_native_gates_do_not_call_sbx(tmp_path, gate):
    h = RoutingHarness(tmp_path, hook=True)
    data = copy.deepcopy(ENABLED)
    if gate == "provider":
        data["ai"]["sandbox"] = {}
    elif gate == "sbx":
        data["local"]["bin"]["sbx"] = {}
    elif gate in ("local", "ai"):
        data.pop(gate)
    elif gate == "ollama":
        data["ai"].pop("ollama")
    else:
        data["ai"]["ollama"]["enabled"] = False
    h.apply(data)
    assert h.calls() == []


@pytest.mark.parametrize("field", ["host_url", "sandbox_url", "default_coder_model"])
@pytest.mark.parametrize("omitted", [False, True])
def test_enabled_missing_fields_prevent_native_writes(tmp_path, field, omitted):
    h = RoutingHarness(tmp_path, hook=True)
    data = copy.deepcopy(ENABLED)
    if omitted:
        data["ai"]["ollama"].pop(field)
    else:
        data["ai"]["ollama"][field] = ""
    result = h.apply(data)
    assert not any(a[:2] == ["settings", "set"] for a in h.calls())
    assert "prerequisite" in result.stderr.lower()


def test_native_converges_on_ordinary_apply_and_repairs_drift(tmp_path):
    h = RoutingHarness(tmp_path, hook=True)
    original = native_records()
    h.apply()
    calls = h.calls()
    assert calls[:3] == [["settings", "get", key, "--json"] for key in KEYS]
    assert [a[2] for a in calls[3:]] == list(KEYS)
    assert all(a[:2] == ["settings", "set"] and len(a) == 4 for a in calls[3:])
    records = h.state()["records"]
    assert records[KEYS[0]]["value"] is True
    assert records[KEYS[1]] == {**original[KEYS[1]], "value": {**original[KEYS[1]]["value"], "enabled": True}}
    assert records[KEYS[2]]["value"] == {
        **original[KEYS[2]]["value"],
        "ollama-configured": {
            "custom": {"keep": True},
            "url": ROOT + "/v1",
            "wire": "openai",
            "name": "Ollama (configured)",
        },
    }
    h.apply()
    assert h.calls()[len(calls) :] == [["settings", "get", key, "--json"] for key in KEYS]
    state = h.state()
    state["records"][KEYS[2]]["value"]["ollama-configured"]["url"] = "http://drift.invalid"
    state["calls"] = []
    h.save(state)
    h.apply()
    assert len(h.calls()) == 4
    assert h.calls()[-1][2] == KEYS[2]
    assert h.state()["records"][KEYS[2]]["value"]["ollama-configured"]["url"] == ROOT + "/v1"


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("fault", ["read", "json", "record", "value", "type"])
def test_failed_or_malformed_reads_prevent_all_writes(tmp_path, key, fault):
    h = RoutingHarness(tmp_path, hook=True)
    state = h.state()
    if fault == "read":
        state["fail"] = [["settings", "get", key, "--json"]]
    elif fault == "json":
        state["raw"] = {key: "fake-private-invalid-json"}
    elif fault == "record":
        state["records"][key] = {"fake-private": "missing value"}
    elif fault == "value":
        state["records"][key]["value"] = []
    else:
        state["records"][key]["type"] = "string"
    h.save(state)
    result = h.apply()
    assert not any(a[:2] == ["settings", "set"] for a in h.calls())
    assert "prerequisite" in result.stderr.lower()


@pytest.mark.parametrize(
    "fault", ["feature-flag", "feature-enabled", "managed-provider", "foreign-provider", "bool-as-int"]
)
def test_invalid_effective_shapes_prevent_all_writes(tmp_path, fault):
    h = RoutingHarness(tmp_path, hook=True)
    state = h.state()
    records = state["records"]
    if fault == "feature-flag":
        records[KEYS[1]].pop("feature_flag")
    elif fault == "feature-enabled":
        records[KEYS[1]]["value"]["enabled"] = "false"
    elif fault == "bool-as-int":
        records[KEYS[0]]["value"] = 0
    else:
        records[KEYS[2]]["value"]["ollama-configured" if fault == "managed-provider" else "foreign"] = []
    h.save(state)
    result = h.apply()
    assert not any(a[:2] == ["settings", "set"] for a in h.calls())
    assert "prerequisite" in result.stderr.lower()


def test_failed_write_retries_without_private_output(tmp_path):
    h = RoutingHarness(tmp_path, hook=True)
    value = {**native_records()[KEYS[2]]["value"]}
    value["ollama-configured"] = {
        **value["ollama-configured"],
        "url": ROOT + "/v1",
        "wire": "openai",
        "name": "Ollama (configured)",
    }
    state = h.state()
    state["fail"] = [["settings", "set", KEYS[2], json.dumps(value)]]
    h.save(state)
    result = h.apply()
    assert "prerequisite" in result.stderr.lower()
    assert h.state()["records"][KEYS[2]]["value"] != value
    state = h.state()
    state["fail"] = []
    state["calls"] = []
    h.save(state)
    h.apply()
    assert len(h.calls()) == 4
    assert h.state()["records"][KEYS[2]]["value"] == value


def test_missing_cli_reports_prerequisite(tmp_path):
    h = RoutingHarness(tmp_path, hook=True)
    (h.bin / "sbx").unlink()
    # Render with the existing resolver before restricting the runtime search path.
    result = h.run("execute-template", "--file", str(h.source / HOOK))
    assert result.returncode == 0, result.stderr
    script = tmp_path / "hook.sh"
    script.write_text(result.stdout)
    result = subprocess.run(
        ["/bin/bash", str(script)], env={**os.environ, "PATH": str(h.bin)}, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0
    assert "prerequisite" in result.stderr.lower()
    assert "fake-private" not in result.stdout + result.stderr
    assert h.calls() == []


@pytest.mark.parametrize("method", [None, "none"])
def test_enabled_routing_retains_opencode_install_gate(tmp_path, method):
    h = RoutingHarness(tmp_path)
    data = copy.deepcopy(ENABLED)
    data["local"]["bin"]["opencode"] = {} if method is None else {"installation_method": method}
    original = '{ "model" : "foreign/model" }\n'
    target = h.seed(OPEN_CODE, original)
    h.apply(data)
    assert target.read_text() == original
    target.unlink()
    h.apply(data)
    assert not target.exists()
    assert h.read(PI_SETTINGS)["defaultModel"] == MODEL


def test_enabled_routing_retains_plugin_migration(tmp_path):
    h = RoutingHarness(tmp_path)
    data = copy.deepcopy(ENABLED)
    data["ai"]["plugins"] = {"superpowers": {"installation_method": "chezmoi_external"}}
    legacy = str(h.destination / ".local/share/agent-plugins/marketplace/plugins/superpowers")
    package = str(h.destination / ".local/share/agent-plugins/marketplaces/superpowers-marketplace/plugins/superpowers")
    h.seed(OPEN_CODE, {"plugin": ["foreign", legacy]})
    h.apply(data)
    assert h.read(OPEN_CODE)["plugin"] == ["foreign", package]
    assert h.read(OPEN_CODE)["model"] == "ollama/" + MODEL


@pytest.mark.parametrize("suffix", ["", "/", "////"])
def test_service_roots_normalize_for_host_files(tmp_path, suffix):
    h = RoutingHarness(tmp_path)
    data = copy.deepcopy(ENABLED)
    data["ai"]["ollama"]["host_url"] = ROOT + suffix
    h.apply(data)
    assert h.read(OPEN_CODE)["provider"]["ollama"]["options"]["baseURL"] == ROOT + "/v1"
    assert h.read(PI_MODELS)["providers"]["ollama"]["baseUrl"] == ROOT + "/v1"


def test_native_adds_provider_and_passes_literal_json_arguments(tmp_path):
    h = RoutingHarness(tmp_path, hook=True)
    data = copy.deepcopy(ENABLED)
    marker = tmp_path / "shell-was-evaluated"
    root = f"http://example.invalid/'$(touch {marker})`touch {marker}`"
    data["ai"]["ollama"]["host_url"] = root + "///"
    state = h.state()
    state["records"][KEYS[2]]["value"] = {}
    h.save(state)
    h.apply(data)
    assert not marker.exists()
    assert h.state()["records"][KEYS[2]]["value"] == {
        "ollama-configured": {"url": root + "/v1", "wire": "openai", "name": "Ollama (configured)"},
    }


@pytest.mark.parametrize("field", ["host_url", "sandbox_url", "default_coder_model"])
def test_incomplete_host_selection_reports_prerequisite(tmp_path, field):
    h = RoutingHarness(tmp_path)
    data = copy.deepcopy(ENABLED)
    data["ai"]["ollama"].pop(field)
    result = h.run("diff", data=data)
    assert result.returncode != 0
    assert "prerequisite" in result.stderr.lower()
    assert not (h.destination / PI_MODELS).exists()
