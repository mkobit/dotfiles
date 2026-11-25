#!/usr/bin/env python3
"""Sign one Git commit from an OpenShell guest with a host key."""

import argparse
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path, PurePosixPath

MAX_PAYLOAD = 65536
OBJECT_ID = rb"(?:[0-9a-f]{40}|[0-9a-f]{64})"

# Git passes the unsigned commit as a file and expects its signature in a sibling file.
GUEST_SIGNER = """#!/bin/sh
set -eu
dir=${0%/*}
if [ "${1:-}" = -Y ] && [ "${2:-}" != sign ]; then
    exec /usr/bin/ssh-keygen "$@"
fi
[ "$#" -eq 7 ] && [ "$1" = -Y ] && [ "$2" = sign ] &&
    [ "$3" = -n ] && [ "$4" = git ] && [ "$5" = -f ] &&
    [ "$6" = "$dir/key.pub" ] || exit 1
tmp=$(mktemp "$dir/request.XXXXXX")
trap 'rm -f "$tmp"' EXIT
head -c 65537 "$7" > "$tmp"
ln "$tmp" "$dir/request"
for i in $(seq 1 30); do
    if [ -s "$dir/signature" ]; then
        cp "$dir/signature" "$7.sig"
        : > "$dir/received"
        exit 0
    fi
    sleep 1
done
echo "Host signing request expired" >&2
exit 1
"""


def validate_commit(
    payload: bytes, identity: str, expected_parent: str | None = None, expected_tree: str | None = None
) -> None:
    """Accept a commit that matches the authorized identity and object IDs."""
    header, separator, _ = payload.partition(b"\n\n")
    lines = header.splitlines()
    if not separator or not lines or not re.fullmatch(rb"tree " + OBJECT_ID, lines[0]):
        raise ValueError("Signing request is not a Git commit")
    if expected_tree is not None and lines[0] != b"tree " + expected_tree.encode():
        raise ValueError("Commit tree does not match the authorized object ID")
    first_identity = 1
    while first_identity < len(lines) and re.fullmatch(rb"parent " + OBJECT_ID, lines[first_identity]):
        first_identity += 1
    if expected_parent is not None and lines[1:first_identity] != [b"parent " + expected_parent.encode()]:
        raise ValueError("Commit must have the authorized parent as its sole parent")
    identities = lines[first_identity:]
    identity_line = re.escape(identity.encode()) + rb" [0-9]+ [+-][0-9]{4}"
    if len(identities) != 2 or any(
        not re.fullmatch(field + b" " + identity_line, line)
        for field, line in zip((b"author", b"committer"), identities, strict=True)
    ):
        raise ValueError("Commit headers do not match the authorized signing identity")


def sign_commit(args: argparse.Namespace, name: str, email: str) -> None:
    """Relay a single commit signature to the selected guest."""
    relay = f"/tmp/openshell-signing-{uuid.uuid4().hex}"  # noqa: S108 - Atomic guest mkdir below.
    base = ["openshell", "sandbox", "exec", "-g", args.gateway, "--no-tty", "--no-login-shell", args.sandbox, "--"]

    gateway_environment = dict(os.environ)
    gateway_environment.pop("OPENSHELL_GATEWAY_ENDPOINT", None)
    gateway_environment.pop("OPENSHELL_GATEWAY_INSECURE", None)

    def guest(*command: str, check: bool = False, **kwargs) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run([*base, *command], env=gateway_environment, check=check, timeout=10, **kwargs)

    environment = dict(os.environ)
    environment.pop("SSH_AUTH_SOCK", None)
    key = str(args.key)
    public = subprocess.run(
        ["ssh-keygen", "-y", "-f", key], env=environment, check=True, capture_output=True, timeout=15
    ).stdout
    guest("mkdir", "-m", "700", relay, check=True)
    try:
        # Transfer only public data and configure the requested guest clone.
        guest(
            "sh",
            "-eu",
            "-c",
            'cat > "$1/key.pub"; chmod 600 "$1/key.pub"',
            "sh",
            relay,
            input=public,
            check=True,
        )
        guest(
            "sh",
            "-eu",
            "-c",
            'cat > "$1/sign"; chmod 700 "$1/sign"',
            "sh",
            relay,
            input=GUEST_SIGNER.encode(),
            check=True,
        )
        guest(
            "sh",
            "-eu",
            "-c",
            """
            repo=$1
            dir=$2
            test "$(git -C "$repo" rev-parse --show-toplevel)" = "$repo"
            git -C "$repo" config --local user.name "$3"
            git -C "$repo" config --local user.email "$4"
            git -C "$repo" config --local user.signingkey "$dir/key.pub"
            git -C "$repo" config --local gpg.format ssh
            git -C "$repo" config --local gpg.ssh.program "$dir/sign"
            git -C "$repo" config --local commit.gpgsign true
            """,
            "sh",
            args.repo,
            relay,
            name,
            email,
            check=True,
        )
        print(f"Ready for one signed commit in {args.sandbox}:{args.repo}", flush=True)
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            result = guest(
                "sh",
                "-eu",
                "-c",
                'test -f "$1/request" || exit 3; head -c 65537 "$1/request"',
                "sh",
                relay,
                stdout=subprocess.PIPE,
            )
            if result.returncode == 0:
                break
            if result.returncode != 3:
                result.check_returncode()
            time.sleep(0.5)
        else:
            raise ValueError("No signing request before the deadline")
        if len(result.stdout) > MAX_PAYLOAD:
            raise ValueError("Signing request exceeds the size limit")
        validate_commit(result.stdout, args.identity, args.expected_parent, args.expected_tree)
        signature = subprocess.run(
            ["ssh-keygen", "-Y", "sign", "-n", "git", "-f", key],
            input=result.stdout,
            stdout=subprocess.PIPE,
            env=environment,
            check=True,
            timeout=15,
        ).stdout
        guest(
            "sh",
            "-eu",
            "-c",
            'cat > "$1/reply"; mv "$1/reply" "$1/signature"',
            "sh",
            relay,
            input=signature,
            check=True,
        )
        # Keep the reply available until Git's wrapper copies it.
        guest(
            "sh",
            "-eu",
            "-c",
            'for i in $(seq 1 8); do test -f "$1/received" && exit 0; sleep 1; done; exit 1',
            "sh",
            relay,
            check=True,
        )
        print("Host signature returned")
    finally:
        guest("sh", "-c", 'rm -r -- "$1"', "sh", relay)


def main() -> int:
    """Run the host signer from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway", required=True)
    parser.add_argument("--sandbox", required=True)
    parser.add_argument("--repo", required=True, help="Absolute guest repository root")
    parser.add_argument("--key", required=True, type=Path, help="Dedicated host SSH private key")
    parser.add_argument("--identity", required=True, help="Git identity in the form Name <email>")
    parser.add_argument("--expected-parent", help="Require the commit to have this object ID as its sole parent")
    parser.add_argument("--expected-tree", help="Require the commit to have this tree object ID")
    parser.add_argument("--timeout", type=int, default=120, help="Seconds to wait for one commit")
    args = parser.parse_args()
    identity = re.fullmatch(r"([^<>\r\n]+) <([^<>\s]+)>", args.identity)
    if identity is None or not PurePosixPath(args.repo).is_absolute() or args.timeout <= 0:
        parser.error("Provide a Git identity, an absolute guest path, and a positive timeout")
    for object_id in (args.expected_parent, args.expected_tree):
        if object_id is not None and not re.fullmatch(OBJECT_ID, object_id.encode()):
            parser.error("Expected object IDs must be full hexadecimal hashes")
    try:
        args.key = args.key.resolve(strict=True)
        sign_commit(args, *identity.groups())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Host signing failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
