#!/bin/bash
set -euo pipefail

# Drift test: verify checked-in rulesync outputs match fresh generation.
# Generates outputs, restores the hand-coded AGENTS.md (which conflicts with
# rulesync's codexcli-generated version), then uses git diff to check for drift.
# Must run with tags=["local"] and env BUILD_WORKSPACE_DIRECTORY.
#
# Usage: rulesync_drift_test.sh <rulesync_binary>

RULESYNC_BINARY="$1"

if [ -z "${BUILD_WORKSPACE_DIRECTORY:-}" ]; then
  echo "ERROR: BUILD_WORKSPACE_DIRECTORY not set. This test must run with tags=[\"local\"]."
  exit 1
fi

cd "$BUILD_WORKSPACE_DIRECTORY"
"$OLDPWD/$RULESYNC_BINARY" generate --silent

# Codex CLI target generates AGENTS.md which conflicts with the hand-coded
# repo-root AGENTS.md. Restore it — the repo version is manually maintained.
git checkout AGENTS.md 2>/dev/null || true

if git diff --quiet; then
  echo "Rulesync outputs are up to date."
else
  echo "ERROR: Rulesync outputs are stale. Run: bazel run @multitool//tools/rulesync -- generate"
  git diff --stat
  exit 1
fi
