#!/bin/bash
set -euo pipefail

OUTPUT_DIR="$1"

echo "Verifying output in $OUTPUT_DIR"
ls -R "$OUTPUT_DIR"

# Check for Claudecode output
# Depending on rulesync version and config, it might be CLAUDE.md or .claude/rules/...
if [ -f "$OUTPUT_DIR/CLAUDE.md" ]; then
    echo "Found CLAUDE.md"
elif [ -f "$OUTPUT_DIR/.claude/rules/test_rule.md" ]; then
    echo "Found .claude/rules/test_rule.md"
else
    echo "Error: Neither CLAUDE.md nor .claude/rules/test_rule.md found"
    exit 1
fi

# Cursor rule check
if [ ! -f "$OUTPUT_DIR/.cursor/rules/test_rule.mdc" ]; then
    echo "Error: .cursor/rules/test_rule.mdc not found"
    exit 1
fi

echo "Verification successful!"
