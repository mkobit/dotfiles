#!/bin/bash
set -euo pipefail

# Simple wrapper to run Python tools via their Bazel wrappers
# Usage: python_check_wrapper.sh <tool> <args...>

TOOL="$1"
shift

case "$TOOL" in
    ruff)
        exec "$(dirname "$0")/../rules/common/ruff_wrapper" "$@"
        ;;
    mypy)
        exec "$(dirname "$0")/../rules/common/mypy_wrapper" "$@"
        ;;
    *)
        echo "Error: Unknown tool '$TOOL'" >&2
        exit 1
        ;;
esac