"""Reconcile configured shortcuts with macOS text replacements."""

import base64
import hashlib
import json
import os
import pwd
import shutil
import sqlite3
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path

CHANGE_TIMEOUT_SECONDS = 5


def plan_changes(desired, current):
    current = set(current)
    removals = sorted(
        ("remove", shortcut, phrase)
        for shortcut, phrase in current
        if shortcut in desired and desired[shortcut] != phrase
    )
    additions = sorted(
        ("add", shortcut, phrase) for shortcut, phrase in desired.items() if (shortcut, phrase) not in current
    )
    return additions + removals


def read_current(database):
    if not database.is_file():
        return []
    with closing(sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)) as connection:
        return connection.execute(
            "SELECT ZSHORTCUT, ZPHRASE FROM ZTEXTREPLACEMENTENTRY WHERE ZWASDELETED = 0"
        ).fetchall()


def apply_changes(helper, database, changes):
    for action, shortcut, phrase in changes:
        try:
            subprocess.run([str(helper), action, shortcut, phrase], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError((error.stderr or "").strip() or str(error)) from error
        deadline = time.monotonic() + CHANGE_TIMEOUT_SECONDS
        while ((shortcut, phrase) in read_current(database)) != (action == "add"):
            if time.monotonic() >= deadline:
                raise RuntimeError("macOS did not save a text replacement change")
            time.sleep(0.05)


def main():
    destination = Path(os.fsdecode(base64.b64decode(sys.argv[1]))).resolve()
    if destination != Path(pwd.getpwuid(os.getuid()).pw_dir).resolve():
        return
    source = Path(os.fsdecode(base64.b64decode(sys.argv[2])))
    desired = json.loads(base64.b64decode(sys.argv[3]))
    database = destination / "Library/KeyboardServices/TextReplacements.db"
    changes = plan_changes(desired, read_current(database))
    if not changes:
        return
    clang = shutil.which("clang")
    if not clang:
        raise RuntimeError("clang is unavailable")
    cache = destination / ".cache/chezmoi/text-replacements"
    cache.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    helper = cache / f"snipctl-{digest}"
    if not helper.is_file():
        subprocess.run([clang, "-fobjc-arc", "-framework", "Foundation", str(source), "-o", str(helper)], check=True)
    apply_changes(helper, database, changes)
    if plan_changes(desired, read_current(database)):
        raise RuntimeError("macOS text replacements did not match after update")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, sqlite3.Error, subprocess.SubprocessError) as error:
        print(f"Could not configure macOS text replacements: {error}", file=sys.stderr)
        sys.exit(1)
