"""Run the SBX workflow hook with isolated chezmoi data and a fake native CLI."""

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "src/chezmoi"
SETUP = "run_after_06_configure-sbx-workflow.sh.tmpl"
SYNC = "run_after_07_sync-sbx-skills.sh.tmpl"
ENABLED = {
    "local": {"bin": {"sbx": {"installation_method": "github_releases"}}},
    "ai": {"workflow": {"enabled": True}, "sandbox": {"provider": "sbx"}},
}


class HookHarness:
    """Keep rendering, apply, CLI state, and deployment inside one test directory."""

    def __init__(self, root, hook):
        self.root = root
        self.hook = hook
        self.source = root / "src/chezmoi"
        self.destination = root / "destination"
        self.bin = root / "bin"
        self.source.mkdir(parents=True)
        self.destination.mkdir()
        self.bin.mkdir()
        self.config = root / "config.toml"
        self.config.write_text("", encoding="utf-8")
        for relative in (
            ".chezmoitemplates/python/filter-interpreter",
            "../python/skill_filter/resolve-interpreter.sh",
        ):
            target = self.source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE / relative, target)
        self.state_file = root / "fake-sbx.json"
        self.save({"mode": "off", "policy": {"rules": []}, "secrets": {"secrets": []}, "calls": []})
        self._fake_cli()

    def _fake_cli(self):
        # Nonempty secret records below deliberately have no verified native schema.
        # The consumer must preserve them, even if their fields look plausible.
        script = (
            f"#!{sys.executable}\nSTATE = {str(self.state_file)!r}\nDEST = {str(self.destination)!r}\n"
            r"""
import json
import shutil
import sys
from pathlib import Path
p = Path(STATE)
s = json.loads(p.read_text())
a = sys.argv[1:]
s['calls'].append(a)
p.write_text(json.dumps(s))
if a in s.get('fail', []):
    print('fake-private-command-output', file=sys.stderr)
    sys.exit(1)
if a == ['settings', 'get', 'skills.defaultMode']:
    print(s['mode'])
elif a[:3] == ['settings', 'set', 'skills.defaultMode'] and len(a) == 4:
    s['mode'] = a[3]
elif a == ['policy', 'ls', '--type', 'network', '--format', 'json']:
    print(s.get('policy_raw', json.dumps(s['policy'])))
elif a == ['policy', 'init', 'balanced']:
    if s.get('initialized'):
        sys.exit(1)
    s['initialized'] = True
    s['policy'] = {'rules': [{'type': 'network', 'fixture': 'balanced'}]}
elif a == ['secret', 'ls', '--global', '--service', 'github', '--format', 'json']:
    print(s.get('secrets_raw', json.dumps(s['secrets'])))
elif a == ['secret', 'set', 'github', '--command', 'gh auth token']:
    s['secrets'] = {'secrets': [{'fixture_unknown_metadata': True}]}
elif a == ['skills', 'import', '--force']:
    store = Path(DEST).parent / 'fake-store'
    store.mkdir(exist_ok=True)
    seen = set()
    for relative in ('.agents/skills', '.claude/skills', '.config/opencode/skills',
                     '.copilot/skills', '.cursor/skills', '.factory/skills'):
        source = Path(DEST) / relative
        if not source.is_dir():
            continue
        for skill in sorted(source.iterdir()):
            if not skill.is_dir() or skill.name in seen:
                continue
            seen.add(skill.name)
            target = store / skill.name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(skill, target)
else:
    print('unexpected fake command', file=sys.stderr)
    sys.exit(93)
p.write_text(json.dumps(s))
"""
        )
        fake = self.bin / "sbx"
        fake.write_text(script, encoding="utf-8")
        fake.chmod(0o755)
        gh = self.bin / "gh"
        gh.write_text(
            f"#!{sys.executable}\nfrom pathlib import Path\n"
            f"Path({str(self.root / 'direct-gh-call')!r}).touch()\nraise SystemExit(94)\n",
            encoding="utf-8",
        )
        gh.chmod(0o755)

    def save(self, state):
        self.state_file.write_text(json.dumps(state), encoding="utf-8")

    def state(self):
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def configure(self, **values):
        self.save({**self.state(), **values})

    def calls(self):
        return self.state()["calls"]

    def command(self, *args, data=None):
        return [
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
            json.dumps(data or {}),
            *args,
        ]

    def install(self):
        origin = SOURCE / ".chezmoiscripts" / self.hook
        assert origin.is_file(), f"task3 hook is absent: {origin}"
        target = self.source / ".chezmoiscripts" / self.hook
        target.parent.mkdir(exist_ok=True)
        shutil.copy2(origin, target)
        return target

    def render(self, data):
        target = self.install()
        result = subprocess.run(
            self.command("execute-template", "--file", str(target), data=data),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        return result.stdout

    def run(self, data=None, *, apply=False, missing_cli=False):
        data = copy.deepcopy(ENABLED if data is None else data)
        rendered = self.render(data)
        env = {**os.environ, "PATH": str(self.bin) + os.pathsep + os.environ["PATH"]}
        if missing_cli:
            (self.bin / "sbx").unlink(missing_ok=True)
            env["PATH"] = str(self.bin)
        if apply:
            preview = subprocess.run(
                self.command("diff", data=data),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            assert preview.returncode == 0, preview.stderr
        result = subprocess.run(
            self.command("apply", data=data) if apply else ["/bin/bash"],
            input=None if apply else rendered,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "fake-private-command-output" not in result.stdout + result.stderr
        assert not (self.root / "direct-gh-call").exists()
        return result.stdout + result.stderr


def decisions(**sandbox):
    data = copy.deepcopy(ENABLED)
    data["ai"]["sandbox"].update(sandbox)
    return data


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"ai": {"workflow": {"enabled": True}}},
        {**ENABLED, "local": {}},
        {**ENABLED, "local": {"bin": {"sbx": {"installation_method": "none"}}}},
        {**ENABLED, "ai": {"sandbox": {}}},
        decisions(provider="none"),
    ],
)
def test_setup_missing_or_disabled_decisions_are_noop(tmp_path, data):
    h = HookHarness(tmp_path, SETUP)
    assert not h.render(data).strip()
    h.run(data)
    assert not h.calls()


@pytest.mark.parametrize("workflow_enabled", [False, None], ids=["global-disabled", "global-missing"])
def test_explicit_mode_applies_without_global_workflow(tmp_path, workflow_enabled):
    h = HookHarness(tmp_path, SETUP)
    data = decisions()
    if workflow_enabled is None:
        del data["ai"]["workflow"]
    else:
        data["ai"]["workflow"]["enabled"] = workflow_enabled
    h.config.write_text('[data.sbx.settings]\nskills_default_mode = "readonly"\n', encoding="utf-8")
    h.run(data, apply=True)
    assert h.state()["mode"] == "readonly"
    assert h.calls() == [
        ["settings", "get", "skills.defaultMode"],
        ["settings", "set", "skills.defaultMode", "readonly"],
    ]


@pytest.mark.parametrize("mode", ["readonly", "readwrite", "off"])
def test_mode_converges_after_manual_drift_on_ordinary_apply(tmp_path, mode):
    h = HookHarness(tmp_path, SETUP)
    different_mode = "readonly" if mode == "off" else "off"
    h.configure(mode=different_mode)
    h.config.write_text(f'[data.sbx.settings]\nskills_default_mode = "{mode}"\n', encoding="utf-8")
    get = ["settings", "get", "skills.defaultMode"]
    set_mode = ["settings", "set", "skills.defaultMode", mode]
    h.run(apply=True)
    assert h.state()["mode"] == mode
    assert h.calls() == [get, set_mode]
    h.run(apply=True)
    assert h.calls() == [get, set_mode, get]
    # Simulate a manual setting change without running any live SBX setter.
    h.configure(mode=different_mode)
    h.run(apply=True)
    assert h.state()["mode"] == mode
    assert h.calls() == [get, set_mode, get, get, set_mode]
    h.run(apply=True)
    assert h.calls() == [get, set_mode, get, get, set_mode, get]


@pytest.mark.parametrize("failed_operation", ["get", "set"])
def test_mode_failure_retries_on_next_ordinary_apply(tmp_path, failed_operation):
    h = HookHarness(tmp_path, SETUP)
    get = ["settings", "get", "skills.defaultMode"]
    set_mode = ["settings", "set", "skills.defaultMode", "readonly"]
    h.config.write_text('[data.sbx.settings]\nskills_default_mode = "readonly"\n', encoding="utf-8")
    h.configure(fail=[get if failed_operation == "get" else set_mode])
    output = h.run(apply=True)
    assert "skip" in output.lower()
    assert "fake-private-command-output" not in output
    assert h.state()["mode"] == "off"
    failed_calls = [get] if failed_operation == "get" else [get, set_mode]
    assert h.calls() == failed_calls
    h.configure(fail=[])
    h.run(apply=True)
    assert h.state()["mode"] == "readonly"
    assert h.calls() == [*failed_calls, get, set_mode]
    h.run(apply=True)
    assert h.calls() == [*failed_calls, get, set_mode, get]


@pytest.mark.parametrize("mode", [None, "", "unsupported"])
def test_missing_or_unsupported_mode_does_not_call_settings(tmp_path, mode):
    h = HookHarness(tmp_path, SETUP)
    data = decisions()
    if mode is not None:
        data["sbx"] = {"settings": {"skills_default_mode": mode}}
    h.run(data)
    assert not h.calls()


def test_overlay_control_plane_overrides_catalog(tmp_path):
    h = HookHarness(tmp_path, SETUP)
    (h.source / ".chezmoidata.toml").write_text(
        '[sbx.settings]\nskills_default_mode = "readwrite"\n',
        encoding="utf-8",
    )
    h.config.write_text('[data.sbx.settings]\nskills_default_mode = "readonly"\n', encoding="utf-8")
    h.run()
    assert h.state()["mode"] == "readonly"


@pytest.mark.parametrize("rules", [[{"custom": "keep"}], [{"scope": "kit"}, {"scope": "org"}]])
def test_policy_preserves_every_existing_rule(tmp_path, rules):
    h = HookHarness(tmp_path, SETUP)
    h.configure(policy={"rules": rules, "unknown": "preserve"})
    h.run(decisions(network_policy="balanced"))
    assert h.calls() == [["policy", "ls", "--type", "network", "--format", "json"]]
    assert h.state()["policy"] == {"rules": rules, "unknown": "preserve"}


def test_empty_policy_uses_one_time_native_init(tmp_path):
    h = HookHarness(tmp_path, SETUP)
    h.run(decisions(network_policy="balanced"), apply=True)
    h.run(decisions(network_policy="balanced"), apply=True)
    assert h.calls().count(["policy", "init", "balanced"]) == 1


def test_initialized_empty_policy_refusal_has_no_reset_or_retry(tmp_path):
    h = HookHarness(tmp_path, SETUP)
    h.configure(initialized=True)
    output = h.run(decisions(network_policy="balanced"))
    assert len(h.calls()) == 2
    assert "refused" in output.lower()
    assert h.state()["policy"] == {"rules": []}


@pytest.mark.parametrize("raw", ["[]", "{}", '{"rules": null}', '{"rules": {}}', "not json"])
def test_invalid_policy_response_prevents_init(tmp_path, raw):
    h = HookHarness(tmp_path, SETUP)
    h.configure(policy_raw=raw)
    assert "skip" in h.run(decisions(network_policy="balanced")).lower()
    assert len(h.calls()) == 1


@pytest.mark.parametrize("selection", ["", "custom", "strict"])
def test_other_policy_selections_do_nothing(tmp_path, selection):
    h = HookHarness(tmp_path, SETUP)
    h.run(decisions(network_policy=selection))
    assert not h.calls()


def test_resolver_is_explicit_and_uses_verified_native_consumer_only(tmp_path):
    h = HookHarness(tmp_path, SETUP)
    h.run(decisions(proxy_gh_secret=False))
    assert not h.calls()
    h.run(decisions(proxy_gh_secret=True))
    assert h.calls() == [
        ["secret", "ls", "--global", "--service", "github", "--format", "json"],
        ["secret", "set", "github", "--command", "gh auth token"],
    ]
    output = h.run(decisions(proxy_gh_secret=True))
    assert "not verified" in output.lower()
    assert len(h.calls()) == 3


@pytest.mark.parametrize(
    "record",
    [
        {"name": "github"},
        {"source": "command", "command": "gh auth token"},
        {"type": "token", "unknown": {"preserve": True}},
    ],
)
def test_unknown_nonempty_resolver_metadata_is_preserved(tmp_path, record):
    h = HookHarness(tmp_path, SETUP)
    h.configure(secrets={"secrets": [record]})
    assert "not verified" in h.run(decisions(proxy_gh_secret=True)).lower()
    assert h.state()["secrets"] == {"secrets": [record]}
    assert len(h.calls()) == 1


@pytest.mark.parametrize("raw", ["[]", "{}", '{"secrets": null}', "invalid"])
def test_invalid_secret_response_never_sets_resolver(tmp_path, raw):
    h = HookHarness(tmp_path, SETUP)
    h.configure(secrets_raw=raw)
    assert "skip" in h.run(decisions(proxy_gh_secret=True)).lower()
    assert len(h.calls()) == 1


@pytest.mark.parametrize(
    "failure",
    [
        ["settings", "get", "skills.defaultMode"],
        ["settings", "set", "skills.defaultMode", "readonly"],
        ["policy", "ls", "--type", "network", "--format", "json"],
        ["policy", "init", "balanced"],
        ["secret", "ls", "--global", "--service", "github", "--format", "json"],
        ["secret", "set", "github", "--command", "gh auth token"],
    ],
)
def test_service_failures_report_skip_without_private_output(tmp_path, failure):
    h = HookHarness(tmp_path, SETUP)
    h.configure(fail=[failure])
    data = {
        **decisions(network_policy="balanced", proxy_gh_secret=True),
        "sbx": {"settings": {"skills_default_mode": "readonly"}},
    }
    assert "skip" in h.run(data).lower()
    assert failure in h.calls()


def test_missing_sbx_is_reported_without_live_calls(tmp_path):
    h = HookHarness(tmp_path, SETUP)
    assert "unavailable" in h.run(decisions(network_policy="balanced"), missing_cli=True).lower()
    assert not h.calls()
