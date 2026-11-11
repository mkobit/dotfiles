import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def apt_script(tmp_path):
    source = tmp_path / "source"
    library = source / ".chezmoitemplates/shell"
    library.mkdir(parents=True)
    logging = Path.cwd() / "src/chezmoi/.chezmoitemplates/shell/logging.sh"
    (library / "logging.sh").write_text(
        logging.read_text() + '\ncheck_command() { [[ "$1" != add-apt-repository || "$TEST_ADD_COMMAND" = 1 ]]; }\n'
    )
    apt = tmp_path / "apt"
    (apt / "sources.list.d").mkdir(parents=True)
    commands = tmp_path / "bin"
    commands.mkdir()
    fake_command = """#!/usr/bin/env bash
set -euo pipefail
name="${0##*/}"
if [[ "$name" = sudo ]]; then
    if [[ "$1" = -n ]]; then
        [[ "$TEST_SUDO" = 1 ]]
        exit
    fi
    exec "$@"
fi
printf '%s %s\\n' "$name" "$*" >> "$TEST_LOG"
case "$name" in
    dpkg)
        if [[ "$TEST_INSTALLED" = 1 || " $TEST_INSTALLED_PACKAGES " = *" ${2} "* ]]; then
            printf 'ii  git  1  amd64  Git\\n'
        fi
        ;;
    apt-get)
        if [[ "$1" = install && "$TEST_FAIL_FIRST_INSTALL" = 1 && ! -f "$TEST_INSTALL_FAILED" ]]; then
            touch "$TEST_INSTALL_FAILED"
            exit 100
        fi
        exit "$TEST_APT_EXIT"
        ;;
    systemctl) exit 0 ;;
esac
"""
    for command in ("sudo", "dpkg", "apt-get", "add-apt-repository", "systemctl"):
        path = commands / command
        path.write_text(fake_command)
        path.chmod(0o755)
    template = Path.cwd() / "src/chezmoi/.chezmoiscripts/run_after_install-apt-packages.sh.tmpl"

    def run(
        contents="",
        filename="git.list",
        installed=True,
        sudo=True,
        add_command=True,
        apt_exit=0,
        packages=None,
        installed_packages=(),
        fail_first_install=False,
    ):
        data = {
            "chezmoi": {"os": "linux"},
            "packages": packages
            or {"git": {"installation_method": "apt", "package": {"apt": {"ppa": "ppa:git-core/ppa"}}}},
        }
        render = subprocess.run(
            [
                "chezmoi",
                "--config",
                "/dev/null",
                "--config-format",
                "toml",
                "--source",
                str(source),
                "--destination",
                str(tmp_path / "dest"),
                "--cache",
                str(tmp_path / "cache"),
                "--persistent-state",
                str(tmp_path / "state.db"),
                "--override-data",
                json.dumps(data),
                "execute-template",
                "-f",
                str(template),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        assert render.stdout.startswith("#!/usr/bin/env bash\n"), render.stdout
        script = tmp_path / "install.sh"
        # Redirect the system APT files into the test directory after chezmoi renders the real template.
        script.write_text(render.stdout.replace("/etc/apt/", f"{apt}/"))

        (apt / "sources.list.d" / filename).write_text(contents)
        log = tmp_path / "commands.log"
        log.write_text("")
        env = {
            **os.environ,
            "PATH": f"{commands}:/usr/bin:/bin",
            "XDG_STATE_HOME": str(tmp_path / "state"),
            "CI": "1",
            "TEST_LOG": str(log),
            "TEST_INSTALLED": str(int(installed)),
            "TEST_INSTALLED_PACKAGES": " ".join(installed_packages),
            "TEST_FAIL_FIRST_INSTALL": str(int(fail_first_install)),
            "TEST_INSTALL_FAILED": str(tmp_path / "install-failed"),
            "TEST_SUDO": str(int(sudo)),
            "TEST_ADD_COMMAND": str(int(add_command)),
            "TEST_APT_EXIT": str(apt_exit),
        }
        result = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True, check=False)
        return result, log.read_text().splitlines(), tmp_path / "state/chezmoi/apt-packages.hash"

    return run


@pytest.mark.parametrize(
    ("filename", "contents"),
    [
        ("git.list", "deb https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/ noble main\n"),
        ("../sources.list", "deb https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/ noble main\n"),
        ("git.list", "deb [signed-by=/key] http://ppa.launchpad.net/git-core/ppa/ubuntu noble main\n"),
        (
            "git.sources",
            "Types: deb\nURIs: https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/\nSuites: noble\nComponents: main\n",
        ),
        (
            "git.sources",
            "Types: deb deb-src\nURIs:\n https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/\nSuites: noble\nComponents: main\nEnabled: yes\n",
        ),
    ],
)
def test_configured_ppa_and_installed_package_need_no_apt_commands(apt_script, filename, contents):
    result, calls, cache = apt_script(contents, filename, add_command=False)
    assert result.returncode == 0, result.stderr
    assert not any(call.startswith(("apt-get ", "add-apt-repository ")) for call in calls), calls
    assert cache.is_file()


@pytest.mark.parametrize(
    ("filename", "contents"),
    [
        ("git.list", "# deb https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/ noble main\n"),
        ("git.list", "deb https://ppa.launchpadcontent.net/git-core/ppa-extra/ubuntu/ noble main\n"),
        ("git.list", "deb https://ppa.launchpadcontent.net/other-git-core/ppa/ubuntu/ noble main\n"),
        ("git.sources", "Types: deb\nURIs: https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/\nEnabled: no\n"),
        ("git.sources", "Types: deb\nURIs: https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/\nEnabled:\n no\n"),
        ("git.sources", "# Types: deb\n# URIs: https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/\n"),
        ("git.sources", "Types: deb-src\nURIs: https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/\n"),
        (
            "git.sources",
            "Types: deb\nURIs: https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/\nEnabled: no\n\nTypes: deb\nURIs: https://example.org/ubuntu/\n",
        ),
    ],
)
def test_missing_enabled_ppa_is_added_even_when_package_is_installed(apt_script, filename, contents):
    result, calls, cache = apt_script(contents, filename)
    assert result.returncode == 0, result.stderr
    assert "add-apt-repository -y --no-update ppa:git-core/ppa" in calls
    assert "apt-get update" in calls
    assert "apt-get install -y git" not in calls
    assert cache.is_file()


def test_configured_ppa_only_installs_missing_package(apt_script):
    result, calls, cache = apt_script(
        "deb https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/ noble main\n",
        installed=False,
    )
    assert result.returncode == 0, result.stderr
    assert "apt-get install -y git" in calls
    assert "apt-get update" not in calls
    assert not any(call.startswith("add-apt-repository ") for call in calls)
    assert cache.is_file()


def test_missing_ppa_installs_repository_helper_when_needed(apt_script):
    result, calls, _ = apt_script(add_command=False)
    assert result.returncode == 0, result.stderr
    assert calls.index("apt-get install -y software-properties-common") < calls.index(
        "add-apt-repository -y --no-update ppa:git-core/ppa"
    )


def test_missing_ppa_without_sudo_does_not_cache_success(apt_script):
    result, calls, cache = apt_script(sudo=False)
    assert result.returncode == 0, result.stderr
    assert not any(call.startswith(("apt-get ", "add-apt-repository ")) for call in calls)
    assert not cache.exists()


def test_failed_apt_update_does_not_cache_success(apt_script):
    result, calls, cache = apt_script(apt_exit=100)
    assert result.returncode == 100
    assert "apt-get update" in calls
    assert not cache.exists()


def test_configured_ppa_and_installed_package_do_not_need_sudo(apt_script):
    result, calls, cache = apt_script(
        "deb https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/ noble main\n", sudo=False, add_command=False
    )
    assert result.returncode == 0, result.stderr
    assert not any(call.startswith(("apt-get ", "add-apt-repository ")) for call in calls)
    assert cache.is_file()


def test_success_cache_skips_next_run(apt_script):
    contents = "deb https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/ noble main\n"
    first, _, cache = apt_script(contents)
    assert first.returncode == 0, first.stderr
    assert cache.is_file()
    second, calls, _ = apt_script(contents)
    assert second.returncode == 0, second.stderr
    assert calls == []


BATCH_PACKAGES = {
    "socat": {"installation_method": "apt"},
    "strace": {"installation_method": "apt"},
    "viewer": {"installation_method": "apt", "package": {"apt": {"name": "chafa"}}},
}


def test_missing_packages_use_one_install_transaction(apt_script):
    result, calls, cache = apt_script(packages=BATCH_PACKAGES, installed=False, installed_packages=("strace",))
    assert result.returncode == 0, result.stderr
    assert [call for call in calls if call.startswith("apt-get ")] == ["apt-get install -y socat chafa"]
    assert cache.is_file()


def test_batch_install_retries_after_update(apt_script):
    result, calls, cache = apt_script(packages=BATCH_PACKAGES, installed=False, fail_first_install=True)
    assert result.returncode == 0, result.stderr
    assert [call for call in calls if call.startswith("apt-get ")] == [
        "apt-get install -y socat strace chafa",
        "apt-get update",
        "apt-get install -y socat strace chafa",
    ]
    assert cache.is_file()


def test_batch_install_failure_does_not_cache_success(apt_script):
    result, calls, cache = apt_script(packages=BATCH_PACKAGES, installed=False, apt_exit=100)
    assert result.returncode != 0
    assert "apt-get update" in calls
    assert not cache.exists()


def test_batch_without_sudo_does_not_cache_success(apt_script):
    result, calls, cache = apt_script(packages=BATCH_PACKAGES, installed=False, sudo=False)
    assert result.returncode == 0, result.stderr
    assert not any(call.startswith("apt-get ") for call in calls)
    assert not cache.exists()


def test_installed_batch_needs_no_sudo_or_install(apt_script):
    result, calls, cache = apt_script(packages=BATCH_PACKAGES, sudo=False)
    assert result.returncode == 0, result.stderr
    assert not any(call.startswith("apt-get ") for call in calls)
    assert cache.is_file()


def test_successful_batch_cache_skips_next_run(apt_script):
    first, _, cache = apt_script(packages=BATCH_PACKAGES, installed=False)
    assert first.returncode == 0, first.stderr
    assert cache.is_file()
    second, calls, _ = apt_script(packages=BATCH_PACKAGES, installed=False)
    assert second.returncode == 0, second.stderr
    assert calls == []


def test_batch_keeps_ppa_and_service_handling(apt_script):
    packages = {
        **BATCH_PACKAGES,
        "git": {"installation_method": "apt", "package": {"apt": {"ppa": "ppa:git-core/ppa"}}},
        "at": {"installation_method": "apt", "systemd": {"service": "atd"}},
    }
    result, calls, cache = apt_script(
        "deb https://ppa.launchpadcontent.net/git-core/ppa/ubuntu/ noble main\n",
        packages=packages,
        installed=False,
    )
    assert result.returncode == 0, result.stderr
    assert [call for call in calls if call.startswith("apt-get ")] == [
        "apt-get install -y at socat strace chafa",
        "apt-get install -y git",
    ]
    assert calls.index("apt-get install -y at socat strace chafa") < calls.index("systemctl is-enabled --quiet atd")
    assert cache.is_file()
