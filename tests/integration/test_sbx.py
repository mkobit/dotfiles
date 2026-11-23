import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHEZMOI_SOURCE = REPO_ROOT / "src" / "chezmoi"
SBX_CATALOG = CHEZMOI_SOURCE / ".chezmoidata" / "bin" / "sbx.toml"
SBX_SETTINGS_CATALOG = CHEZMOI_SOURCE / ".chezmoidata" / "sbx" / "settings.toml"
SBX_RESTART_SCRIPT = CHEZMOI_SOURCE / ".chezmoiscripts" / "005_sbx" / "run_after_01_restart-daemon.py.tmpl"
SBX_SETTINGS_SCRIPT = CHEZMOI_SOURCE / ".chezmoiscripts" / "005_sbx" / "run_after_02_setup-settings.sh.tmpl"
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


def test_sbx_release_catalog_defines_linux_checksums():
    """Require a version and sha256 checksums for all supported Linux platforms."""
    with SBX_CATALOG.open("rb") as catalog_file:
        catalog = tomllib.load(catalog_file)

    sbx = catalog["bin"]["sbx"]
    assert isinstance(sbx["version"], str) and sbx["version"]
    checksums = sbx["github_releases"]["checksums"]
    assert set(checksums) == {"linux_amd64", "linux_arm64"}
    for digest in checksums.values():
        assert re.fullmatch(r"[0-9a-f]{64}", digest), digest


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


def _render_sbx_script(
    script_path: Path, override_data: dict[str, object], destination: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "chezmoi",
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPO_ROOT),
            *(["--destination", str(destination)] if destination is not None else []),
            "execute-template",
            "--file",
            "--override-data",
            json.dumps(override_data),
            str(script_path),
        ],
        capture_output=True,
        check=False,
        text=True,
    )


def _render_sbx_settings_script(
    override_data: dict[str, object], destination: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return _render_sbx_script(SBX_SETTINGS_SCRIPT, override_data, destination=destination)


def _run_rendered_sbx_restart_script(
    tmp_path: Path,
    version_json: str,
    restart_on_update: bool | None = None,
):
    sbx_data: dict[str, object] = {}
    if restart_on_update is not None:
        sbx_data["daemon"] = {"restart_on_update": restart_on_update}
    rendered = _render_sbx_script(
        SBX_RESTART_SCRIPT,
        {
            "local": {"bin": {"sbx": {"installation_method": "github_releases"}}},
            "sbx": sbx_data,
        },
        destination=tmp_path,
    )
    assert rendered.returncode == 0, rendered.stderr

    calls = tmp_path / "calls"
    fake_sbx = tmp_path / "sbx"
    fake_sbx.write_text(
        "#!/bin/sh\n"
        'printf \'%s\\n\' "$*" >> "$SBX_TEST_CALLS"\n'
        "if [ \"$1 $2\" = 'version --json' ]; then\n"
        '  if [ -n "$SBX_TEST_VERSION_JSON" ]; then\n'
        "    printf '%s\\n' \"$SBX_TEST_VERSION_JSON\"\n"
        "  fi\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1 $2\" = 'daemon restart' ]; then\n"
        "  exit 0\n"
        "fi\n",
        encoding="utf-8",
    )
    fake_sbx.chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{tmp_path}:{env['PATH']}",
            "SBX_TEST_CALLS": str(calls),
            "SBX_TEST_VERSION_JSON": version_json,
        }
    )
    result = subprocess.run(
        ["python3", "-"],
        input=rendered.stdout,
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )
    recorded_calls = calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []
    return result, recorded_calls


def _run_rendered_sbx_settings_script(tmp_path: Path, current: str, get_rc: int = 0, set_rc: int = 0):
    rendered = _render_sbx_settings_script(
        {
            "local": {"bin": {"sbx": {"installation_method": "github_releases"}}},
            "sbx": {
                "settings": {
                    "kit_allowed_sources": {
                        "docker_hub": "docker.io/",
                        "github_docker": "github.com/docker/",
                    },
                }
            },
        },
        destination=tmp_path,
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
        "github_docker": "github.com/docker/",
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
                        "github_docker": "github.com/docker/",
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
        'settings set kit.allowedSources ["docker.io/","github.com/docker/"]',
    ]


def test_sbx_settings_script_is_idempotent_for_matching_sources(tmp_path):
    result, calls = _run_rendered_sbx_settings_script(
        tmp_path,
        '["docker.io/", "github.com/docker/"]',
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
        'settings set kit.allowedSources ["docker.io/","github.com/docker/"]',
    ]
    assert "Unable to configure kit.allowedSources" in result.stdout


def test_sbx_restart_script_renders_only_when_enabled():
    disabled = _render_sbx_script(
        SBX_RESTART_SCRIPT,
        {"local": {"bin": {"sbx": {"installation_method": "none"}}}},
    )

    assert disabled.returncode == 0, disabled.stderr
    assert disabled.stdout == ""


def test_sbx_restart_script_restarts_daemon_on_version_mismatch_by_default(tmp_path):
    mismatch_json = json.dumps(
        {
            "client": {"version": "v0.54.0", "revision": "newrev"},
            "server": {"state": "running", "version": "v0.53.0", "revision": "oldrev"},
        }
    )
    result, calls = _run_rendered_sbx_restart_script(tmp_path, mismatch_json)

    assert result.returncode == 0, result.stderr
    assert calls == ["version --json", "daemon restart"]


def test_sbx_restart_script_skips_daemon_restart_when_disabled(tmp_path):
    mismatch_json = json.dumps(
        {
            "client": {"version": "v0.54.0", "revision": "newrev"},
            "server": {"state": "running", "version": "v0.53.0", "revision": "oldrev"},
        }
    )
    result, calls = _run_rendered_sbx_restart_script(
        tmp_path,
        mismatch_json,
        restart_on_update=False,
    )

    assert result.returncode == 0, result.stderr
    assert calls == ["version --json"]
    assert "sbx.daemon.restart_on_update=false" in result.stderr


def test_sbx_restart_script_is_noop_when_versions_match(tmp_path):
    matching_json = json.dumps(
        {
            "client": {"version": "v0.54.0", "revision": "samerev"},
            "server": {"state": "running", "version": "v0.54.0", "revision": "samerev"},
        }
    )
    result, calls = _run_rendered_sbx_restart_script(tmp_path, matching_json)

    assert result.returncode == 0, result.stderr
    assert calls == ["version --json"]


def test_sbx_settings_script_skips_when_sbx_is_unavailable(tmp_path):
    rendered = _render_sbx_settings_script(
        {
            "local": {"bin": {"sbx": {"installation_method": "github_releases"}}},
            "sbx": {
                "settings": {
                    "kit_allowed_sources": {"docker_hub": "docker.io/"},
                }
            },
        },
        destination=tmp_path,
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
    data = {
        "chezmoi": {"os": "linux", "username": "mkobit"},
        "local": {"bin": {"sbx": {"installation_method": "github_releases"}}},
    }
    for key, val in override_data.items():
        if isinstance(val, dict) and key in data and isinstance(data[key], dict):
            data[key] = {**data[key], **val}
        else:
            data[key] = val

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
            json.dumps(data),
            str(SBX_KVM_SCRIPT),
        ],
        capture_output=True,
        check=False,
        text=True,
    )


def test_sbx_kvm_script_renders_only_when_enabled_on_linux():
    enabled = _render_sbx_kvm_script({})
    assert enabled.returncode == 0, enabled.stderr
    assert "target_user=" in enabled.stdout
    assert "usermod -aG kvm" in enabled.stdout

    disabled = _render_sbx_kvm_script({"local": {"bin": {"sbx": {"installation_method": "none"}}}})
    assert disabled.returncode == 0, disabled.stderr
    assert disabled.stdout == ""

    darwin = _render_sbx_kvm_script({"chezmoi": {"os": "darwin"}})
    assert darwin.returncode == 0, darwin.stderr
    assert darwin.stdout == ""


def test_sbx_kvm_script_is_noop_when_user_already_in_kvm_group(tmp_path):
    rendered = _render_sbx_kvm_script({})
    assert rendered.returncode == 0, rendered.stderr

    # Create mock `id` that includes `kvm`
    fake_id = tmp_path / "id"
    fake_id.write_text("#!/bin/sh\necho 'mkobit adm kvm'\n", encoding="utf-8")
    fake_id.chmod(0o755)

    # Create fake `sudo` that records calls
    calls = tmp_path / "calls"
    fake_sudo = tmp_path / "sudo"
    fake_sudo.write_text(f'#!/bin/sh\necho "$*" >> {calls}\n', encoding="utf-8")
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
    rendered = _render_sbx_kvm_script({})
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
    rendered = _render_sbx_kvm_script({})
    assert rendered.returncode == 0, rendered.stderr

    # Create mock `id` that does NOT include `kvm`
    fake_id = tmp_path / "id"
    fake_id.write_text("#!/bin/sh\necho 'mkobit adm'\n", encoding="utf-8")
    fake_id.chmod(0o755)

    # Create fake `sudo` that succeeds and records calls
    calls = tmp_path / "calls"
    fake_sudo = tmp_path / "sudo"
    fake_sudo.write_text(
        f'#!/bin/sh\nif [ "$1" = \'-n\' ]; then exit 0; fi\necho "$*" >> {calls}\n',
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


@pytest.mark.parametrize("provider", ["sbx", "none"])
@pytest.mark.parametrize(
    ("system", "arch", "macos_version", "expected"),
    [
        ("linux", "amd64", "", "github_releases"),
        ("linux", "arm64", "", "github_releases"),
        ("linux", "386", "", "none"),
        ("darwin", "arm64", "13.6.9", "none"),
        ("darwin", "arm64", "14.0", "homebrew"),
        ("darwin", "arm64", "15.7.1", "homebrew"),
        ("darwin", "amd64", "15.7.1", "none"),
        ("windows", "amd64", "", "none"),
        ("freebsd", "amd64", "", "none"),
    ],
)
def test_sbx_init_selects_supported_installation(tmp_path, system, arch, macos_version, expected, provider):
    """Select the installation independently of the agent sandbox provider."""
    sw_vers = tmp_path / "sw_vers"
    calls = tmp_path / "sw-vers-calls"
    sw_vers.write_text(
        f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{calls}"\nprintf "%s\\n" "{macos_version}"\n',
        encoding="utf-8",
    )
    sw_vers.chmod(0o755)
    chezmoi = shutil.which("chezmoi")
    assert chezmoi is not None
    config = tmp_path / "config.toml"
    platform = {"chezmoi": {"os": system, "arch": arch}, "ai": {"sandbox": {"provider": provider}}}
    initialized = subprocess.run(
        [
            chezmoi,
            "--config",
            "/dev/null",
            "--config-format",
            "toml",
            "--source",
            str(REPO_ROOT),
            "--destination",
            str(tmp_path),
            "execute-template",
            "--init",
            "--override-data",
            json.dumps(platform),
            "--file",
            str(CHEZMOI_SOURCE / ".chezmoi.toml.tmpl"),
        ],
        env={**os.environ, "CI": "1", "PATH": f"{tmp_path}:{os.defpath}"},
        capture_output=True,
        text=True,
        check=True,
    )
    config.write_text(initialized.stdout, encoding="utf-8")
    data = tomllib.loads(initialized.stdout)["data"]
    assert data["local"]["bin"]["sbx"]["installation_method"] == expected
    if system == "darwin" and arch == "arm64":
        assert calls.read_text().splitlines() == ["-productVersion"]
    else:
        assert not calls.exists()

    def render(relative):
        result = subprocess.run(
            [
                chezmoi,
                "--config",
                str(config),
                "--source",
                str(REPO_ROOT),
                "--destination",
                str(tmp_path),
                "execute-template",
                "--override-data",
                json.dumps(platform),
                "--file",
                str(CHEZMOI_SOURCE / relative),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    brewfile = render("dot_Brewfile.tmpl")
    assert ('cask "docker/tap/sbx"' in brewfile) == (expected == "homebrew")
    external = tomllib.loads(render("dot_local/.chezmoiexternals/sbx.toml.tmpl"))
    symlink = render("dot_local/bin/symlink_sbx.tmpl")
    if expected == "github_releases":
        with SBX_CATALOG.open("rb") as catalog_file:
            sbx_version = tomllib.load(catalog_file)["bin"]["sbx"]["version"]
        assert external["lib/docker-sbx"]["url"].endswith(f"/v{sbx_version}/DockerSandboxes-linux-{arch}.tar.gz")
        assert symlink == f"{tmp_path}/.local/lib/docker-sbx/sbx"
    else:
        assert external == {}
        assert symlink == ""


@pytest.mark.integration
@pytest.mark.chezmoi_installation("local.bin.sbx", methods={"github_releases", "homebrew"})
def test_sbx_installed_cli_version(host, chezmoi_data):
    """Fail when an enabled SBX installation is absent or cannot report its version."""
    present = host.run("command -v sbx")
    assert present.rc == 0, f"SBX is enabled but absent: {present.stderr}"
    result = host.run("sbx --version")
    assert result.rc == 0, f"sbx --version failed: {result.stderr}"
    version = re.search(r"\bsbx version v?(\d+\.\d+\.\d+)\b", result.stdout)
    assert version is not None, result.stdout
    if chezmoi_data["local"]["bin"]["sbx"]["installation_method"] == "github_releases":
        assert version[1] == chezmoi_data["bin"]["sbx"]["version"]


@pytest.mark.integration
@pytest.mark.chezmoi_installation("local.bin.sbx", methods={"github_releases", "homebrew"})
def test_sbx_installed_kit_allowed_sources(host, chezmoi_data):
    """Check that SBX uses the kit sources declared in chezmoi data."""
    expected_sources = chezmoi_data["sbx"]["settings"]["kit_allowed_sources"]
    result = host.run("sbx settings get kit.allowedSources")
    if (
        os.environ.get("GITHUB_ACTIONS") == "true"
        and result.rc != 0
        and "503 Service Unavailable: administrator settings are unavailable" in result.stderr
    ):
        pytest.skip("The CI runner cannot read SBX administrator settings.")
    assert result.rc == 0, f"Unable to read SBX kit.allowedSources: {result.stderr}"
    assert json.loads(result.stdout) == [expected_sources[key] for key in sorted(expected_sources)]
