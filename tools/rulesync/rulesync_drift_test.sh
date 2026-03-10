#!/bin/bash
set -euo pipefail

# Drift test: verify checked-in rulesync outputs match fresh generation.
# Uses rulesync's built-in --check flag which exits 1 if files are stale.
# Must run with tags=["local"] and env BUILD_WORKSPACE_DIRECTORY.
#
# Usage: rulesync_drift_test.sh <rulesync_binary>

RULESYNC_BINARY="$1"

if [ -z "${BUILD_WORKSPACE_DIRECTORY:-}" ]; then
  echo "ERROR: BUILD_WORKSPACE_DIRECTORY not set. This test must run with tags=[\"local\"]."
  exit 1
fi

cd "$BUILD_WORKSPACE_DIRECTORY"
"$OLDPWD/$RULESYNC_BINARY" generate --check --silent
echo "Rulesync outputs are up to date."
