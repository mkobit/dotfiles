import json
import os
import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHEZMOI_SOURCE = REPO_ROOT / "src" / "chezmoi"
SBX_CATALOG = CHEZMOI_SOURCE / ".chezmoidata" / "bin" / "sbx.toml"
SBX_SETTINGS_CATALOG = CHEZMOI_SOURCE / ".chezmoidata" / "sbx" / "settings.toml"
SBX_SETTINGS_SCRIPT = CHEZMOI_SOURCE / ".chezmoiscripts" / "run_after_05_configure-sbx-settings.sh.tmpl"
SBX_KVM_SCRIPT = CHEZMOI_SOURCE / ".chezmoiscripts" / "run_after_04_configure-kvm-group.sh.tmpl"
LEGACY_TARGETS = (
    ".local/bin/sbx-agy",
    ".local/bin/tools/sbx-agy",
    ".local/share/sbx/AGENTS.md",
    ".local/share/sbx/mixins/chezmoi-init/spec.yaml",
    ".local/share/sbx/mixins/git-config/files/home/.gitconfig",
    ".local/share/sbx/mixins/git-config/spec.yaml",
    ".local/share/sbx/mixins/mise/files/home/.config/mise/config.toml",
    ".local/share/sbx/mixins/mise/spec.yaml",
    ".local/share/sbx/sandboxes/agy/spec.yaml",
)


def test_sbx_release_catalog_pins_v0_39_0_with_verified_linux_checksums():
    """Keep the SBX release archive pinned to the verified v0.39.0 assets."""
    with SBX_CATALOG.open("rb") as catalog_file:
        catalog = tomllib.load(catalog_file)

    sbx = catalog["bin"]["sbx"]
    assert sbx["version"] == "0.39.0"
    assert sbx["github_releases"]["checksums"] == {
        "linux_amd64": "2ec45bc7938c20c2f406fe8cc72294ad5a954bdc047601484b89bf1a108311d4",
        "linux_arm64": "39c470a5f5e0991b1c2358952e2ab32a7b0309bfa57ac62b6bbc64b466d02c17",
    }


def test_sbx_does_not_manage_legacy_host_integration_targets():
    """Keep SBX limited to its binary rather than host-managed launchers or kits."""
    result = subprocess.run(
        [
            "chezmoi",
            "--source",
            str(CHEZMOI_SOURCE),
            "managed",
            "--include=files",
            "--format=json",
            "--path-style=all",
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    managed_targets = json.loads(result.stdout)

    for target in LEGACY_TARGETS:
        assert target not in managed_targets


def _render_sbx_settings_script(override_data: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPO_ROOT),
            "execute-template",
            "--file",
            "--override-data",
            json.dumps(override_data),
            str(SBX_SETTINGS_SCRIPT),
        ],
        capture_output=True,
        check=False,
        text=True,
    )


def _run_rendered_sbx_settings_script(tmp_path: Path, current: str, get_rc: int = 0, set_rc: int = 0):
    rendered = _render_sbx_settings_script(
        {
            "local": {"bin": {"sbx": {"installation_method": "github_releases"}}},
            "sbx": {
                "settings": {
                    "kit_allowed_sources": {
                        "docker_hub": "docker.io/",
                        "github_shelajev": "github.com/shelajev/",
                    },
                }
            },
        }
    )
    assert rendered.returncode == 0, rendered.stderr

    calls = tmp_path / "calls"
    fake_sbx = tmp_path / "sbx"
    fake_sbx.write_text(
        "#!/bin/sh\n"
        'printf \'%s\\n\' "$*" >> "$SBX_TEST_CALLS"\n'
        "if [ \"$1 $2\" = 'settings get' ]; then\n"
        "  printf '%s\\n' \"$SBX_TEST_CURRENT\"\n"
        '  exit "$SBX_TEST_GET_RC"\n'
        "fi\n"
        "if [ \"$1 $2\" = 'settings set' ]; then\n"
        '  exit "$SBX_TEST_SET_RC"\n'
        "fi\n",
        encoding="utf-8",
    )
    fake_sbx.chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{tmp_path}:{env['PATH']}",
            "SBX_TEST_CALLS": str(calls),
            "SBX_TEST_CURRENT": current,
            "SBX_TEST_GET_RC": str(get_rc),
            "SBX_TEST_SET_RC": str(set_rc),
        }
    )
    result = subprocess.run(
        ["bash"],
        input=rendered.stdout,
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )
    recorded_calls = calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []
    return result, recorded_calls


def test_sbx_settings_catalog_declares_complete_approved_kit_source_list():
    with SBX_SETTINGS_CATALOG.open("rb") as catalog_file:
        catalog = tomllib.load(catalog_file)

    assert catalog["sbx"]["settings"]["kit_allowed_sources"] == {
        "docker_hub": "docker.io/",
        "github_shelajev": "github.com/shelajev/",
    }


def test_sbx_settings_script_renders_only_when_enabled():
    disabled = _render_sbx_settings_script(
        {
            "local": {"bin": {"sbx": {"installation_method": "none"}}},
            "sbx": {
                "settings": {
                    "kit_allowed_sources": {"docker_hub": "docker.io/"},
                }
            },
        }
    )

    assert disabled.returncode == 0, disabled.stderr
    assert disabled.stdout == ""


def test_sbx_settings_script_uses_existing_sbx_installation_opt_in():
    rendered = _render_sbx_settings_script(
        {
            "local": {"bin": {"sbx": {"installation_method": "github_releases"}}},
            "sbx": {
                "settings": {
                    "kit_allowed_sources": {
                        "docker_hub": "docker.io/",
                        "github_shelajev": "github.com/shelajev/",
                    },
                }
            },
        }
    )

    assert rendered.returncode == 0, rendered.stderr
    assert "settings get kit.allowedSources" in rendered.stdout


def test_sbx_settings_script_preserves_every_declared_source_when_updating(tmp_path):
    result, calls = _run_rendered_sbx_settings_script(tmp_path, '["docker.io/"]')

    assert result.returncode == 0, result.stderr
    assert calls == [
        "settings get kit.allowedSources",
        'settings set kit.allowedSources ["docker.io/","github.com/shelajev/"]',
    ]


def test_sbx_settings_script_is_idempotent_for_matching_sources(tmp_path):
    result, calls = _run_rendered_sbx_settings_script(
        tmp_path,
        '["docker.io/", "github.com/shelajev/"]',
    )

    assert result.returncode == 0, result.stderr
    assert calls == ["settings get kit.allowedSources"]


def test_sbx_settings_script_skips_update_when_daemon_is_unavailable(tmp_path):
    result, calls = _run_rendered_sbx_settings_script(tmp_path, "", get_rc=1)

    assert result.returncode == 0, result.stderr
    assert calls == ["settings get kit.allowedSources"]
    assert "Skipping SBX settings configuration" in result.stdout


def test_sbx_settings_script_skips_when_daemon_fails_during_update(tmp_path):
    result, calls = _run_rendered_sbx_settings_script(tmp_path, '["docker.io/"]', set_rc=1)

    assert result.returncode == 0, result.stderr
    assert calls == [
        "settings get kit.allowedSources",
        'settings set kit.allowedSources ["docker.io/","github.com/shelajev/"]',
    ]
    assert "Unable to configure kit.allowedSources" in result.stdout


def test_sbx_settings_script_skips_when_sbx_is_unavailable(tmp_path):
    rendered = _render_sbx_settings_script(
        {
            "local": {"bin": {"sbx": {"installation_method": "github_releases"}}},
            "sbx": {
                "settings": {
                    "kit_allowed_sources": {"docker_hub": "docker.io/"},
                }
            },
        }
    )
    assert rendered.returncode == 0, rendered.stderr

    env = os.environ.copy()
    env["PATH"] = str(tmp_path)
    result = subprocess.run(
        ["/bin/bash"],
        input=rendered.stdout,
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "sbx is unavailable" in result.stdout


def _render_sbx_kvm_script(override_data: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPO_ROOT),
            "execute-template",
            "--file",
            "--override-data",
            json.dumps(override_data),
            str(SBX_KVM_SCRIPT),
        ],
        capture_output=True,
        check=False,
        text=True,
    )


def test_sbx_kvm_script_renders_only_when_enabled_on_linux():
    enabled = _render_sbx_kvm_script(
        {"local": {"bin": {"sbx": {"installation_method": "github_releases"}}}}
    )
    assert enabled.returncode == 0, enabled.stderr
    assert "target_user=" in enabled.stdout
    assert "usermod -aG kvm" in enabled.stdout

    disabled = _render_sbx_kvm_script(
        {"local": {"bin": {"sbx": {"installation_method": "none"}}}}
    )
    assert disabled.returncode == 0, disabled.stderr
    assert disabled.stdout == ""


def test_sbx_kvm_script_is_noop_when_user_already_in_kvm_group(tmp_path):
    rendered = _render_sbx_kvm_script(
        {"local": {"bin": {"sbx": {"installation_method": "github_releases"}}}}
    )
    assert rendered.returncode == 0, rendered.stderr

    # Create mock `id` that includes `kvm`
    fake_id = tmp_path / "id"
    fake_id.write_text("#!/bin/sh\necho 'mkobit adm kvm'\n", encoding="utf-8")
    fake_id.chmod(0o755)

    # Create fake `sudo` that records calls
    calls = tmp_path / "calls"
    fake_sudo = tmp_path / "sudo"
    fake_sudo.write_text(f"#!/bin/sh\necho \"$*\" >> {calls}\n", encoding="utf-8")
    fake_sudo.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    result = subprocess.run(
        ["/bin/bash"],
        input=rendered.stdout,
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert not calls.exists()


def test_sbx_kvm_script_skips_when_no_sudo_access(tmp_path):
    rendered = _render_sbx_kvm_script(
        {"local": {"bin": {"sbx": {"installation_method": "github_releases"}}}}
    )
    assert rendered.returncode == 0, rendered.stderr

    # Create mock `id` that does NOT include `kvm`
    fake_id = tmp_path / "id"
    fake_id.write_text("#!/bin/sh\necho 'mkobit adm'\n", encoding="utf-8")
    fake_id.chmod(0o755)

    # Create fake `sudo` that fails for `-n true`
    fake_sudo = tmp_path / "sudo"
    fake_sudo.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    fake_sudo.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    result = subprocess.run(
        ["/bin/bash"],
        input=rendered.stdout,
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "skipping kvm group" in result.stdout


def test_sbx_kvm_script_adds_user_to_kvm_when_missing(tmp_path):
    rendered = _render_sbx_kvm_script(
        {"local": {"bin": {"sbx": {"installation_method": "github_releases"}}}}
    )
    assert rendered.returncode == 0, rendered.stderr

    # Create mock `id` that does NOT include `kvm`
    fake_id = tmp_path / "id"
    fake_id.write_text("#!/bin/sh\necho 'mkobit adm'\n", encoding="utf-8")
    fake_id.chmod(0o755)

    # Create fake `sudo` that succeeds and records calls
    calls = tmp_path / "calls"
    fake_sudo = tmp_path / "sudo"
    fake_sudo.write_text(
        f"#!/bin/sh\nif [ \"$1\" = '-n' ]; then exit 0; fi\necho \"$*\" >> {calls}\n",
        encoding="utf-8",
    )
    fake_sudo.chmod(0o755)

    # Create fake `getent`
    fake_getent = tmp_path / "getent"
    fake_getent.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_getent.chmod(0o755)

    # Create fake `stat` reporting kvm:660
    fake_stat = tmp_path / "stat"
    fake_stat.write_text(
        "#!/bin/sh\nif [ \"$2\" = '%G' ]; then echo 'kvm'; elif [ \"$2\" = '%a' ]; then echo '660'; fi\n",
        encoding="utf-8",
    )
    fake_stat.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    result = subprocess.run(
        ["/bin/bash"],
        input=rendered.stdout,
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    recorded_calls = calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []
    assert any("usermod -aG kvm" in call for call in recorded_calls)

