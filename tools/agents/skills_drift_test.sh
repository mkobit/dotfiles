#!/bin/bash
set -euo pipefail

# Drift test: verify committed skill copies match canonical source.
# Discovers skills from src/agents/skills/*/SKILL.md.
# Discovers target tools from src/chezmoi/dot_*/skills/ directories.
# Must run via `bazel run` (BUILD_WORKSPACE_DIRECTORY is set).
#
# Usage: bazel run //tools/agents:check

if [ -z "${BUILD_WORKSPACE_DIRECTORY:-}" ]; then
  echo "ERROR: BUILD_WORKSPACE_DIRECTORY not set. Run with: bazel run //tools/agents:check"
  exit 1
fi

cd "$BUILD_WORKSPACE_DIRECTORY"

CANONICAL_DIR="src/agents/skills"
CHEZMOI_DIR="src/chezmoi"
DRIFT_FOUND=0

# Discover target tools from existing dot_*/skills/ directories
tools=()
for tool_dir in "$CHEZMOI_DIR"/dot_*/skills/; do
  [ -d "$tool_dir" ] || continue
  tool=$(basename "$(dirname "$tool_dir")")
  tool=${tool#dot_}
  tools+=("$tool")
done

if [ ${#tools[@]} -eq 0 ]; then
  echo "No target tool directories found (expected $CHEZMOI_DIR/dot_*/skills/)."
  exit 1
fi

# Check each canonical skill against each tool's copy
for skill_dir in "$CANONICAL_DIR"/*/; do
  [ -d "$skill_dir" ] || continue
  skill=$(basename "$skill_dir")
  canonical="$skill_dir/SKILL.md"

  if [ ! -f "$canonical" ]; then
    continue
  fi

  for tool in "${tools[@]}"; do
    target="$CHEZMOI_DIR/dot_$tool/skills/$skill/SKILL.md"

    if [ ! -f "$target" ]; then
      echo "MISSING: $target (expected copy of $canonical)"
      DRIFT_FOUND=1
      continue
    fi

    if ! diff -q "$canonical" "$target" > /dev/null 2>&1; then
      echo "DRIFT: $target differs from $canonical"
      diff --unified "$canonical" "$target" || true
      DRIFT_FOUND=1
    fi
  done
done

if [ "$DRIFT_FOUND" -ne 0 ]; then
  echo ""
  echo "Skill copies are out of date. Run: bazel run //tools/agents:sync"
  exit 1
fi

echo "All skill copies are up to date."
