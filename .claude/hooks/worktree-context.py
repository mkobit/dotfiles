#!/usr/bin/env python3
# Injected once per session via UserPromptSubmit (once: true).
# Outputs worktree context only when not in the main checkout.
# Also warns when local main is behind origin/main.

import subprocess
import sys
from pathlib import Path


def run(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, check=False)
    return result.stdout.strip()


cwd = Path.cwd()

git_root = run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"])
if not git_root:
    sys.exit(0)

worktree_list = run(["git", "-C", str(cwd), "worktree", "list"])
main_worktree = worktree_list.splitlines()[0].split()[0] if worktree_list else ""
branch = run(["git", "-C", str(cwd), "rev-parse", "--abbrev-ref", "HEAD"]) or "unknown"

if git_root != main_worktree:
    print(
        f"Worktree session: branch={branch} path={git_root} (main: {main_worktree}). Run git worktree list + git status before changes."
    )
    sys.exit(0)

# In the primary checkout — warn if on main or if main is behind origin/main.
if branch == "main":
    behind_raw = run(["git", "-C", git_root, "rev-list", "--count", "HEAD..origin/main"])
    behind = int(behind_raw) if behind_raw.isdigit() else 0
    if behind > 0:
        print(
            f"WARNING: Local main is {behind} commit(s) behind origin/main. Run 'git pull' before making any changes."
        )
    print(
        "WARNING: You are on the main branch. GitHub branch protection prevents pushing to origin/main. Use 'git switch -c feat/your-change origin/main' before making commits."
    )
