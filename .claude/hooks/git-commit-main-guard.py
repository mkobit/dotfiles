#!/usr/bin/env python3
# PreToolUse hook: block git commit when on the main branch.
# Committing directly to main diverges from origin/main (which is protected).
#
# Receives tool call JSON on stdin; prints {"decision":"block","reason":"..."}
# to block, exits 0 silently to allow.

import json
import re
import subprocess
import sys
from textwrap import dedent

data = json.load(sys.stdin)
command = data.get("tool_input", {}).get("command", "")

if not command:
    sys.exit(0)

if not re.search(r"^\s*git\s+commit\b", command):
    sys.exit(0)

result = subprocess.run(
    ["git", "branch", "--show-current"],
    capture_output=True,
    text=True,
)
branch = result.stdout.strip()

if branch != "main":
    sys.exit(0)

print(json.dumps({
    "decision": "block",
    "reason": dedent("""\
        Blocked: committing directly to main will diverge from origin/main.
        GitHub branch protection prevents pushing to origin/main.

        Create a feature branch based off origin/main first:
          git switch -c feat/your-change origin/main

        Then commit and push:
          git push -u origin feat/your-change

        Then open a pull request to merge into main.
    """),
}))

sys.exit(0)
