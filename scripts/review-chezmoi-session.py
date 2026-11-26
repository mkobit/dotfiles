#!/usr/bin/env python3
"""Capture and review sampled Codex sessions from the dotfiles repository."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import UUID

OPT_IN = "CHEZMOI_ENABLE_PERSONAL_SESSION_EVAL_CAPTURE"
REPO = Path(__file__).resolve().parents[1]
REVIEW_SKILL = Path(".agents/skills/session-eval-review/SKILL.md")
REVIEW_PROMPT = "Use $session-eval-review to review the original session for an eval case."


def queue() -> Path:
    """Return the private local directory for Codex session markers."""
    state = os.environ.get("XDG_STATE_HOME")
    state_home = Path(state) if state and Path(state).is_absolute() else Path.home() / ".local/state"
    return state_home / "chezmoi-session-eval/codex"


def git_common_dir(cwd: Path) -> Path | None:
    """Return the Git directory shared by all worktrees of the repository."""
    result = subprocess.run(
        ["git", "-C", str(cwd), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else None


def session_id(value: object) -> str | None:
    """Accept a canonical Codex session UUID for use as a path component."""
    if not isinstance(value, str):
        return None
    try:
        return value if str(UUID(value)) == value else None
    except ValueError:
        return None


def capture() -> None:
    """Record an empty marker for a sampled session in this repo."""
    if os.environ.get(OPT_IN) != "1":
        return
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return
    if not isinstance(event, dict) or event.get("hook_event_name") != "SessionEnd":
        return
    uid = session_id(event.get("session_id"))
    cwd = event.get("cwd")
    if uid is None or not isinstance(cwd, str) or not Path(cwd).is_absolute():
        return
    digest = hashlib.sha256(uid.encode("ascii")).digest()
    if int.from_bytes(digest[:4], "big") % 10 != 0:
        return
    root = git_common_dir(REPO)
    if root is None or root != git_common_dir(Path(cwd)):
        return

    os.umask(0o077)
    markers = queue()
    markers.mkdir(mode=0o700, parents=True, exist_ok=True)
    (markers / uid).mkdir(mode=0o700, exist_ok=True)


def review() -> int:
    """Offer sampled sessions without copying the conversation."""
    markers = queue()
    if not markers.is_dir():
        print("No sampled Codex sessions are available.")
        return 0
    pending = sorted(
        marker
        for marker in markers.iterdir()
        if session_id(marker.name) and marker.is_dir() and not (marker / "handled").exists()
    )
    if not pending:
        print("No sampled Codex sessions are available.")
        return 0

    repo = Path(os.environ.get("CHEZMOI_SKILLS_CHECKOUT") or Path.home() / "workspace/mkobit/chezmoi-skills")
    repo = repo.expanduser().resolve()
    if not (repo / REVIEW_SKILL).is_file():
        print(
            f"Review skill missing in {repo}. Get the latest checkout or set CHEZMOI_SKILLS_CHECKOUT.", file=sys.stderr
        )
        return 1

    for marker in pending:
        answer = input(f"Review sampled Codex session {marker.name}? [y/N/s to skip] ").strip().lower()
        if answer == "s":
            (marker / "handled").touch(mode=0o600)
            continue
        if answer not in {"y", "yes"}:
            return 0

        env = os.environ.copy()
        env.pop(OPT_IN, None)
        result = subprocess.run(
            ["codex", "fork", "--no-daemon", "--cd", str(repo), marker.name, REVIEW_PROMPT],
            env=env,
            check=False,
        )
        if result.returncode == 0:
            (marker / "handled").touch(mode=0o600)
        return result.returncode
    return 0


def main() -> int:
    """Run the hook handler or the interactive review command."""
    try:
        if sys.argv[1:] == ["capture"]:
            capture()
            return 0
        if not sys.argv[1:]:
            if not sys.stdin.isatty():
                print("Run this command in a terminal to review sessions.", file=sys.stderr)
                return 1
            return review()
        print(f"Usage: {Path(sys.argv[0]).name}", file=sys.stderr)
    except EOFError:
        return 0
    except KeyboardInterrupt:
        return 130
    except OSError as exc:
        print(f"Session review: {exc}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
