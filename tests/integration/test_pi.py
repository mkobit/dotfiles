"""Check the installed Pi executable and configured settings."""

import json
import shlex

import pytest
from chezmoi_test_data import required_installation_method

pi_enabled = pytest.mark.chezmoi_installation("local.bin.pi", methods={"github_releases", "existing"})


@pytest.fixture
def pi_binary(host, chezmoi_dest, chezmoi_data):
    if required_installation_method(chezmoi_data, "local.bin.pi") == "github_releases":
        return str(chezmoi_dest / ".local/bin/pi")
    result = host.run("command -v pi")
    assert result.rc == 0, f"Pi is not on PATH.\nstderr: {result.stderr}"
    return result.stdout.strip()


@pytest.mark.integration
@pi_enabled
@pytest.mark.parametrize("check", ["file", "executable"])
def test_pi_executable(host, pi_binary, check):
    binary = host.file(pi_binary)
    if check == "file":
        assert binary.is_file, f"{pi_binary} is not a file"
    else:
        assert binary.mode & 0o111, f"{pi_binary} is not executable"


@pytest.mark.integration
@pi_enabled
def test_pi_version(host, pi_binary, chezmoi_data):
    result = host.run(f"{shlex.quote(pi_binary)} --version")
    assert result.rc == 0, f"Pi --version failed.\nstderr: {result.stderr}"
    version = result.stdout.strip()
    assert version, "Pi --version returned no version"
    if required_installation_method(chezmoi_data, "local.bin.pi") == "github_releases":
        assert version == chezmoi_data["bin"]["pi"]["version"]


@pytest.mark.integration
@pi_enabled
def test_pi_configured_settings(host, chezmoi_dest, chezmoi_data):
    target = host.file(str(chezmoi_dest / ".pi/agent/settings.json"))
    settings = json.loads(target.content_string)
    configured = chezmoi_data.get("pi", {}).get("settings", {})
    assert {key: value for key, value in settings.items() if key in configured} == configured


@pytest.mark.integration
@pytest.mark.chezmoi_installation("local.bin.pi", methods={"none"})
def test_pi_disabled_settings_absent(host, chezmoi_dest):
    assert not host.file(str(chezmoi_dest / ".pi/agent/settings.json")).exists
