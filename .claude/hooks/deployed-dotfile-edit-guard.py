#!/usr/bin/env python3
# PreToolUse hook: block Edit/Write to chezmoi-deployed dotfile targets.
# This repo deploys AI tool config (skills, agents, hooks, settings) from
# src/chezmoi/, src/ai/skills/, etc. to ~/.claude, ~/.cursor, ~/.codex, and
# ~/.gemini/antigravity-cli via chezmoi. Editing the deployed copy directly
# is a dead end: chezmoi overwrites it (or it silently drifts) on next apply.
#
# Static prefix list rather than a live `chezmoi managed` query — the
# read-source-state hook reruns bin/assemble (when composed under an
# overlay) on every chezmoi invocation, which is too slow to run on every
# Edit/Write.
#
# Receives tool call JSON on stdin; prints {"decision":"block","reason":"..."}
# to block, exits 0 silently to allow.

import json
import os
import sys
from textwrap import dedent

HOME = os.path.expanduser("~")

MANAGED_PREFIXES = [
    ".claude/skills/",
    ".claude/agents/",
    ".claude/hooks/",
    ".claude/commands/",
    ".cursor/skills/",
    ".cursor/agents/",
    ".codex/skills/",
    ".codex/agents/",
    ".gemini/antigravity-cli/skills/",
    ".gemini/antigravity-cli/agents/",
    ".config/opencode/agents/",
]
MANAGED_FILES = [
    ".claude/settings.json",
    ".claude/CLAUDE.md",
]

data = json.load(sys.stdin)
file_path = data.get("tool_input", {}).get("file_path", "")
if not file_path:
    sys.exit(0)

abs_path = os.path.abspath(os.path.expanduser(file_path))
if not (abs_path + os.sep).startswith(HOME + os.sep):
    sys.exit(0)

rel = abs_path[len(HOME) + 1 :]
if rel in MANAGED_FILES or any(rel.startswith(p) for p in MANAGED_PREFIXES):
    reason = dedent(f"""\
        Blocked: {file_path} is a chezmoi-deployed target, not the source.

        Edit the source instead — src/chezmoi/ (or an overlay's
        src/overlay-skills/, src/chezmoi/ — check for a composed overlay
        first) — then run `chezmoi apply`.
    """)
    print(json.dumps({"decision": "block", "reason": reason}))

sys.exit(0)
