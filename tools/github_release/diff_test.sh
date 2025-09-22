#!/bin/bash
set -euo pipefail

GENERATED_FILE="$1"
SOURCE_FILE="$2"

if ! diff -u "$SOURCE_FILE" "$GENERATED_FILE"; then
    echo "Error: Generated file is out of date. Please run:" >&2
    echo "  bazel build //src:fzf_release" >&2
    echo "  And copy the generated file to src/.chezmoiexternals/fzf.toml" >&2
    exit 1
fi
