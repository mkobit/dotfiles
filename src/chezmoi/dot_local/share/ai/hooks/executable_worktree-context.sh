#!/usr/bin/env bash
# UserPromptSubmit hook: injects git worktree context when Claude is running
# outside the main worktree checkout.

git_root=$(git -C "${PWD}" rev-parse --show-toplevel 2>/dev/null) || exit 0
main_worktree=$(git -C "${PWD}" worktree list 2>/dev/null | head -1 | awk '{print $1}')
branch=$(git -C "${PWD}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

[[ "$git_root" == "$main_worktree" ]] && exit 0

cat <<EOF
Git worktree context: this session is running in a worktree, NOT the main checkout.
  Branch:        $branch
  Worktree path: $git_root
  Main worktree: $main_worktree
Run \`git worktree list\` and \`git status\` to confirm state before making changes.
EOF
