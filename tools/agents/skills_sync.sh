#!/bin/bash
set -euo pipefail

# Sync portable skills from canonical source to chezmoi tool directories.
# Discovers skills from src/agents/skills/*/SKILL.md.
# Discovers target tools from src/chezmoi/dot_*/skills/ directories.
# Must run via `bazel run` (BUILD_WORKSPACE_DIRECTORY is set).
#
# Usage: bazel run //tools/agents:sync

if [ -z "${BUILD_WORKSPACE_DIRECTORY:-}" ]; then
  echo "ERROR: BUILD_WORKSPACE_DIRECTORY not set. Run with: bazel run //tools/agents:sync"
  exit 1
fi

cd "$BUILD_WORKSPACE_DIRECTORY"

CANONICAL_DIR="src/agents/skills"
CHEZMOI_DIR="src/chezmoi"
SYNCED=0

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

echo "Target tools: ${tools[*]}"

# Discover and sync each canonical skill
for skill_dir in "$CANONICAL_DIR"/*/; do
  [ -d "$skill_dir" ] || continue
  skill=$(basename "$skill_dir")
  canonical="$skill_dir/SKILL.md"

  if [ ! -f "$canonical" ]; then
    continue
  fi

  for tool in "${tools[@]}"; do
    target_dir="$CHEZMOI_DIR/dot_$tool/skills/$skill"
    target="$target_dir/SKILL.md"

    mkdir -p "$target_dir"

    if [ ! -f "$target" ] || ! diff -q "$canonical" "$target" > /dev/null 2>&1; then
      cp "$canonical" "$target"
      echo "  Synced: $skill → $tool"
      SYNCED=$((SYNCED + 1))
    fi
  done
done

if [ "$SYNCED" -eq 0 ]; then
  echo "All skill copies already up to date."
else
  echo "Synced $SYNCED file(s)."
fi
