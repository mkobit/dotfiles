#!/usr/bin/env bash
# Injected once per session via UserPromptSubmit (once: true).
# Outputs worktree context only when not in the main checkout.
git_root=$(git -C "${PWD}" rev-parse --show-toplevel 2>/dev/null) || exit 0
main_worktree=$(git -C "${PWD}" worktree list 2>/dev/null | head -1 | awk '{print $1}')
[[ "$git_root" == "$main_worktree" ]] && exit 0
branch=$(git -C "${PWD}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
echo "Worktree session: branch=$branch path=$git_root (main: $main_worktree). Run git worktree list + git status before changes."
