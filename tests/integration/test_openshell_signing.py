"""Verify the OpenShell signing command with real Git and disposable SSH keys."""

import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SIGNER = REPO_ROOT / "docker" / "openshell" / "sign-commit.py"


def test_host_signer_completes_one_guest_commit(tmp_path: Path) -> None:
    guest = tmp_path / "guest"
    host = tmp_path / "host"
    host.mkdir()
    key = host / "disposable"
    email = "agent@example.invalid"
    env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    subprocess.run(["git", "init", "-q", guest], check=True, env=env)
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", key], check=True, env=env)
    allowed_signers = host / "allowed_signers"
    allowed_signers.write_text(f"{email} {key.with_suffix('.pub').read_text()}", encoding="utf-8")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    openshell = bin_dir / "openshell"
    openshell.write_text(
        """#!/bin/sh
set -eu
test "$1" = sandbox && test "$2" = exec
shift 2
while [ "$1" != -- ]; do shift; done
shift
exec "$@"
""",
        encoding="utf-8",
    )
    openshell.chmod(0o755)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    git = ["git", "-C", guest]
    log = host / "relay.log"
    with (
        log.open("wb") as output,
        subprocess.Popen(
            [
                sys.executable,
                SIGNER,
                "--gateway",
                "test-gateway",
                "--sandbox",
                "test-guest",
                "--repo",
                guest,
                "--key",
                key,
                "--identity",
                f"OpenShell Agent <{email}>",
                "--timeout",
                "10",
            ],
            stdout=output,
            stderr=subprocess.STDOUT,
            env=env,
        ) as relay,
    ):
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and relay.poll() is None:
                if "Ready for one signed commit in " in log.read_text(encoding="utf-8"):
                    break
                time.sleep(0.05)
            else:
                raise AssertionError(log.read_text(encoding="utf-8"))
            subprocess.run(
                [*git, "commit", "-S", "--allow-empty", "-m", "Sign in the guest"],
                check=True,
                env=env,
                timeout=12,
            )
            assert relay.wait(timeout=5) == 0, log.read_text(encoding="utf-8")
        finally:
            if relay.poll() is None:
                relay.kill()

    host_clone = host / "verify"
    subprocess.run(["git", "clone", "-q", "--no-local", guest, host_clone], check=True, env=env)
    subprocess.run(
        ["git", "-C", host_clone, "-c", f"gpg.ssh.allowedSignersFile={allowed_signers}", "verify-commit", "HEAD"],
        check=True,
        env=env,
    )

    before = subprocess.check_output([*git, "rev-parse", "HEAD"], env=env)
    second = subprocess.run(
        [*git, "commit", "-S", "--allow-empty", "-m", "Request a second signature"],
        check=False,
        env=env,
        timeout=12,
    )
    assert second.returncode != 0
    assert subprocess.check_output([*git, "rev-parse", "HEAD"], env=env) == before
