#!/usr/bin/env python3
# PreToolUse hook: block any git push that targets origin/main.
# GitHub branch protection rejects these, causing local/remote divergence.
#
# Receives tool call JSON on stdin; prints {"decision":"block","reason":"..."}
# to block, exits 0 silently to allow.

import json
import re
import sys
from textwrap import dedent

data = json.load(sys.stdin)
command = data.get("tool_input", {}).get("command", "")

if not command:
    sys.exit(0)

# Match: git push [flags] origin main (including origin main:main, origin HEAD:main, etc.)
if re.search(r"^\s*git\s+push\b.*\borigin\b.*\bmain\b", command):
    print(json.dumps({
        "decision": "block",
        "reason": dedent(f"""\
            Blocked: pushing to origin/main is rejected by GitHub branch protection
            and will cause local/remote divergence.

            Create a feature branch based off origin/main instead:
              git switch -c feat/your-change origin/main
              git push -u origin feat/your-change

            Then open a pull request to merge into main.
        """),
    }))

sys.exit(0)
