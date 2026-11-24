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
        printf 'raw apt output: %s\n' "$*"
        if [[ "$TEST_APT_HANG_SECONDS" != 0 ]]; then
            /bin/sleep "$TEST_APT_HANG_SECONDS"
        fi
        if [[ "$1" = install && "$TEST_FAIL_FIRST_INSTALL" = 1 && ! -f "$TEST_INSTALL_FAILED" ]]; then
            touch "$TEST_INSTALL_FAILED"
            exit 100
        fi
        exit "$TEST_APT_EXIT"
        ;;
    add-apt-repository)
        attempt=0
        if [[ -f "$TEST_ADD_ATTEMPTS" ]]; then
            attempt=$(cat "$TEST_ADD_ATTEMPTS")
        fi
        attempt=$((attempt + 1))
        printf '%s\\n' "$attempt" > "$TEST_ADD_ATTEMPTS"
        [[ "$attempt" -ge "$TEST_ADD_SUCCEED_AT" ]]
        ;;
    systemctl) exit 0 ;;
esac
"""
    for command in ("sudo", "dpkg", "apt-get", "add-apt-repository", "systemctl", "sleep"):
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
        add_succeed_at=1,
        ci=True,
        apt_hang_seconds=0,
        timeout_seconds=None,
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
            "TEST_LOG": str(log),
            "TEST_INSTALLED": str(int(installed)),
            "TEST_INSTALLED_PACKAGES": " ".join(installed_packages),
            "TEST_FAIL_FIRST_INSTALL": str(int(fail_first_install)),
            "TEST_INSTALL_FAILED": str(tmp_path / "install-failed"),
            "TEST_SUDO": str(int(sudo)),
            "TEST_ADD_COMMAND": str(int(add_command)),
            "TEST_ADD_ATTEMPTS": str(tmp_path / "add-attempts"),
            "TEST_ADD_SUCCEED_AT": str(add_succeed_at),
            "TEST_APT_EXIT": str(apt_exit),
            "TEST_APT_HANG_SECONDS": str(apt_hang_seconds),
        }
        if ci:
            env["CI"] = "1"
            env["CHEZMOI_APT_REPORT_DIR"] = str(tmp_path / "apt-report")
        command = ["bash", str(script)]
        try:
            result = subprocess.run(
                command,
                env=env,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else error.stdout or ""
            stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else error.stderr or ""
            result = subprocess.CompletedProcess(command, 124, stdout, stderr)
        return result, log.read_text().splitlines(), tmp_path / "state/chezmoi/apt-packages.hash"

    return run


def test_ci_apt_commands_write_timing_and_raw_output_to_report(apt_script):
    result, calls, cache = apt_script(
        packages=BATCH_PACKAGES,
        installed=False,
        fail_first_install=True,
    )
    assert result.returncode == 0, result.stderr
    assert [call for call in calls if call.startswith("apt-get ")] == [
        "apt-get install -y socat strace chafa",
        "apt-get update",
        "apt-get install -y socat strace chafa",
    ]
    report_dir = cache.parents[2] / "apt-report"
    report = sorted(report_dir.glob("apt-command-*.log"))
    assert len(report) == 3
    assert "raw apt output: install -y socat strace chafa" in report[0].read_text()
    assert "raw apt output: update" in report[1].read_text()
    assert "raw apt output: install -y socat strace chafa" in report[2].read_text()
    assert result.stdout.count("APT command started:") == 3
    assert "APT command finished:" in result.stdout
    assert "elapsed_seconds=" in result.stdout
    assert "result=0" in result.stdout
    assert "raw apt output" not in result.stdout


def test_ci_apt_failure_shows_raw_output_tail_and_result(apt_script):
    result, _, cache = apt_script(packages=BATCH_PACKAGES, installed=False, apt_exit=100)
    assert result.returncode != 0
    assert "raw apt output: install -y socat strace chafa" in result.stderr
    assert "result=100" in result.stdout
    assert not cache.exists()


def test_non_ci_apt_output_remains_visible(apt_script):
    result, _, _ = apt_script(packages=BATCH_PACKAGES, installed=False, ci=False)
    assert result.returncode == 0
    assert "raw apt output: install -y socat strace chafa" in result.stdout
    assert "APT command started:" not in result.stdout


def test_non_ci_apt_failure_keeps_command_status(apt_script):
    result, _, cache = apt_script(packages=BATCH_PACKAGES, installed=False, apt_exit=100, ci=False)
    assert result.returncode == 100
    assert "raw apt output: install -y socat strace chafa" in result.stdout
    assert "APT command started:" not in result.stdout
    assert not cache.exists()


def test_ci_apt_hang_emits_start_record_before_timeout(apt_script):
    result, _, cache = apt_script(
        packages=BATCH_PACKAGES,
        installed=False,
        apt_hang_seconds=5,
        timeout_seconds=0.2,
    )
    assert result.returncode == 124
    assert "APT command started:" in result.stdout
    assert "APT command finished:" not in result.stdout
    report = cache.parents[2] / "apt-report/apt-command-1.log"
    assert "raw apt output: install -y socat strace chafa" in report.read_text()


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


@pytest.mark.parametrize("add_succeed_at", [1, 2, 5])
def test_missing_ppa_retries_only_repository_setup(apt_script, add_succeed_at):
    result, calls, cache = apt_script(add_succeed_at=add_succeed_at)
    assert result.returncode == 0, result.stderr
    assert calls.count("add-apt-repository -y --no-update ppa:git-core/ppa") == add_succeed_at
    assert [call for call in calls if call.startswith("sleep ")] == ["sleep 5", "sleep 10", "sleep 20", "sleep 40"][
        : add_succeed_at - 1
    ]
    assert calls.count("apt-get update") == 1
    assert cache.is_file()


def test_missing_ppa_stops_after_five_failures(apt_script):
    result, calls, cache = apt_script(add_succeed_at=6)
    assert result.returncode == 1
    assert calls.count("add-apt-repository -y --no-update ppa:git-core/ppa") == 5
    assert [call for call in calls if call.startswith("sleep ")] == ["sleep 5", "sleep 10", "sleep 20", "sleep 40"]
    assert "apt-get update" not in calls
    assert "apt-get install -y git" not in calls
    assert not cache.exists()


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
