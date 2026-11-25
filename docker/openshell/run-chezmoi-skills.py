#!/usr/bin/env python3
"""Run the read-only chezmoi-skills task in a fresh OpenShell sandbox."""

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import ExitStack
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGE = "dotfiles-openshell-sandbox:8a19efcd"
GUEST_REPO = "/tmp/project"  # noqa: S108 - Private to the fresh sandbox.
GUEST_RESPONSE = "/tmp/codex-dispatch/last-message"  # noqa: S108 - Private to the fresh sandbox.
REVISION = "74cd324f5c48580980eef18350f8b19bebfb2286"
TREE = "409be662c71b375c9e5743c89ad10935441b17a1"
IDENTITY = "Mike Kobit <mkobit@gmail.com>"

AGENT = r"""
export PATH="/sandbox/.local/bin:$PATH" CODEX_HOME=/tmp/codex-dispatch
umask 077
mkdir "$CODEX_HOME"
python3 - <<'INNER'
import base64
import datetime
import json
import os
from pathlib import Path

def segment(value):
    return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")

auth = {
    "auth_mode": "chatgpt",
    "OPENAI_API_KEY": None,
    "tokens": {
        "id_token": ".".join((segment({"alg": "none"}), segment({"sub": "openshell-pilot"}), "placeholder")),
        "access_token": os.environ["CODEX_AUTH_ACCESS_TOKEN"],
        "refresh_token": "unused",
        "account_id": os.environ["CODEX_ACCOUNT_ID"],
    },
    "last_refresh": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
(Path(os.environ["CODEX_HOME"]) / "auth.json").write_text(json.dumps(auth))
INNER
cd "$1"
printf '%s\n' 'Read README.md and mise.toml. State the repository purpose and its unit test command in two lines. Do not modify files.' |
    timeout 75 codex exec --sandbox danger-full-access --ephemeral --output-last-message "$CODEX_HOME/last-message" -
"""


def run(command, *, timeout=30, **kwargs):
    return subprocess.run(command, check=True, timeout=timeout, **kwargs)


def output(command, **kwargs):
    return run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True, **kwargs).stdout.strip()


def login():
    codex_dir = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    try:
        auth = json.loads((codex_dir / "auth.json").read_bytes())
        tokens = auth["tokens"]
        if auth["auth_mode"] != "chatgpt" or not all(
            isinstance(tokens[key], str) and tokens[key] for key in ("access_token", "account_id")
        ):
            raise ValueError
    except (OSError, ValueError, KeyError, TypeError):  # fmt: skip
        raise ValueError("Codex requires an active ChatGPT login in its file credential store.") from None
    return tokens["access_token"], tokens["account_id"]


def profile(name):
    return {
        "id": name,
        "display_name": "Disposable Codex dispatch",
        "category": "agent",
        "inference_capable": True,
        "credentials": [
            {
                "name": "access_token",
                "env_vars": ["CODEX_AUTH_ACCESS_TOKEN"],
                "required": True,
                "auth_style": "bearer",
                "header_name": "authorization",
            }
        ],
        "endpoints": [
            {"host": host, "port": 443, "protocol": "rest", "access": "read-write", "enforcement": "enforce"}
            for host in ("chatgpt.com", "api.openai.com", "ab.chatgpt.com")
        ],
        "binaries": ["/sandbox/.local/lib/codex/bin/codex"],
    }


def sign(guest, gateway, name, key, environment, results):
    with (results / "signer.log").open("wb") as log:
        signer = subprocess.Popen(
            [
                sys.executable,
                str(HERE / "sign-commit.py"),
                "--gateway",
                gateway,
                "--sandbox",
                name,
                "--repo",
                GUEST_REPO,
                "--key",
                key,
                "--identity",
                IDENTITY,
                "--expected-parent",
                REVISION,
                "--expected-tree",
                TREE,
                "--timeout",
                "35",
            ],
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if signer.poll() is not None:
                    raise ValueError("The host signer exited before it was ready. See signer.log.")
                if "Ready for one signed commit" in (results / "signer.log").read_text():
                    break
                time.sleep(0.25)
            else:
                raise ValueError("The host signer did not become ready. See signer.log.")
            guest(
                "git",
                "-C",
                GUEST_REPO,
                "commit",
                "-S",
                "--allow-empty",
                "-m",
                "Verify unattended OpenShell dispatch",
                timeout=45,
            )
            if signer.wait(timeout=20):
                raise ValueError("The host signer failed. See signer.log.")
        finally:
            if signer.poll() is None:
                signer.terminate()
                try:
                    signer.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    signer.kill()
                    signer.wait()


def verify_bundle(bundle, public_key, scratch):
    allowed = scratch / "allowed_signers"
    allowed.write_text(f'mkobit@gmail.com namespaces="git" {public_key}\n')
    git = ["git", "-C", str(scratch)]
    run([*git, "init", "--bare", "-q"], stdin=subprocess.DEVNULL)
    run([*git, "bundle", "verify", str(bundle)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    run([*git, "-c", "fetch.fsckObjects=true", "fetch", "-q", str(bundle), "HEAD"], stdin=subprocess.DEVNULL)
    head_and_parents = output([*git, "rev-list", "--parents", "-1", "FETCH_HEAD"]).split()
    if head_and_parents[1:] != [REVISION]:
        raise ValueError("The returned commit must have the pinned revision as its sole parent.")
    if output([*git, "rev-parse", "FETCH_HEAD^{tree}"]) != TREE:
        raise ValueError("The returned commit changed the project tree.")
    run(
        [*git, "-c", "gpg.format=ssh", "-c", f"gpg.ssh.allowedSignersFile={allowed}", "verify-commit", "FETCH_HEAD"],
        stdin=subprocess.DEVNULL,
    )
    return head_and_parents[0]


def dispatch(gateway):
    access_token, account_id = login()
    try:
        key = str(Path(output(["git", "-C", str(HERE), "config", "--path", "user.signingkey"])).resolve(strict=True))
        public_key = " ".join(output(["ssh-keygen", "-y", "-P", "", "-f", key], stderr=subprocess.DEVNULL).split()[:2])
    except (OSError, subprocess.SubprocessError):  # fmt: skip
        raise ValueError("Git user.signingkey must point to a host SSH private key usable without a prompt.") from None

    name = f"codex-{uuid.uuid4().hex[:13]}"
    environment = os.environ.copy()
    for variable in ("OPENSHELL_GATEWAY_ENDPOINT", "OPENSHELL_GATEWAY_INSECURE", "CODEX_AUTH_ACCESS_TOKEN"):
        environment.pop(variable, None)

    def openshell(*command, env=environment, stdin=subprocess.DEVNULL, **kwargs):
        return run(["openshell", "--gateway", gateway, *command], env=env, stdin=stdin, **kwargs)

    def guest(*command, **kwargs):
        return openshell("sandbox", "exec", "--no-tty", "--no-login-shell", name, "--", *command, **kwargs)

    cleanup_failures = []

    def delete(resource):
        try:
            openshell(resource, "delete", name)
        except (OSError, subprocess.SubprocessError) as error:
            cleanup_failures.append(resource)
            print(f"Could not delete {resource} {name} on {gateway}. {error}", file=sys.stderr)

    results = Path(tempfile.mkdtemp(prefix="chezmoi-skills-result-"))
    print(f"Task results directory {results}", flush=True)
    with tempfile.TemporaryDirectory(dir=results) as directory:
        scratch = Path(directory)
        profile_file = scratch / "profile.json"
        profile_file.write_text(json.dumps(profile(name)))
        with ExitStack() as cleanup:
            # Schedule each deletion before its request in case the Gateway creates a resource after a client error.
            cleanup.callback(delete, "profile")
            openshell("profile", "import", "-f", str(profile_file))
            cleanup.callback(delete, "provider")
            try:
                openshell(
                    "provider",
                    "create",
                    "--name",
                    name,
                    "--type",
                    name,
                    "--credential",
                    "CODEX_AUTH_ACCESS_TOKEN",
                    env={**environment, "CODEX_AUTH_ACCESS_TOKEN": access_token},
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.SubprocessError:
                raise ValueError("The Gateway could not create the temporary Codex provider.") from None
            cleanup.callback(delete, "sandbox")
            openshell(
                "sandbox",
                "create",
                "--name",
                name,
                "--from",
                IMAGE,
                "--policy",
                str(HERE / "chezmoi-skills-policy.yaml"),
                "--provider",
                name,
                "--env-from",
                "CODEX_ACCOUNT_ID",
                "--no-auto-providers",
                "--detach",
                "--",
                "sleep",
                "900",
                env={**environment, "CODEX_ACCOUNT_ID": account_id},
                timeout=180,
            )
            with (HERE / "chezmoi-skills-setup.sh").open("rb") as setup, (results / "tests.log").open("wb") as log:
                guest("sh", "-es", "--", REVISION, stdin=setup, stdout=log, stderr=subprocess.STDOUT, timeout=480)
            with (results / "agent.log").open("wb") as log:
                guest("sh", "-ec", AGENT, "sh", GUEST_REPO, stdout=log, stderr=subprocess.STDOUT, timeout=95)
            reply = guest("cat", GUEST_RESPONSE, stdout=subprocess.PIPE).stdout
            if b"mise run test" not in reply:
                raise ValueError("Codex did not identify the expected test command. See agent.log.")

            repo_git = ("git", "-C", GUEST_REPO)
            if guest(*repo_git, "rev-parse", "HEAD", stdout=subprocess.PIPE).stdout.decode().strip() != REVISION:
                raise ValueError("The guest checkout moved from the pinned revision.")
            if guest(*repo_git, "status", "--porcelain", "--untracked-files=all", stdout=subprocess.PIPE).stdout:
                raise ValueError("The guest checkout has changes.")
            sign(guest, gateway, name, key, environment, results)
            bundle = scratch / "result.bundle"
            with bundle.open("wb") as stream:
                guest(*repo_git, "bundle", "create", "-", "HEAD", stdout=stream, timeout=60)
            commit = verify_bundle(bundle, public_key, scratch)
        if cleanup_failures:
            raise ValueError("OpenShell could not remove all task resources.")
        bundle.rename(results / bundle.name)
    return commit


def interrupt(_signal_number, _frame):
    raise KeyboardInterrupt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway", default="openshell-microvm", help="Name of the existing OpenShell Gateway")
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupt)
    try:
        commit = dispatch(args.gateway)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Task failed. {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Task interrupted.", file=sys.stderr)
        return 130
    print(f"Verified commit {commit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
