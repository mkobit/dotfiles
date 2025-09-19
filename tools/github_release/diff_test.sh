#!/bin/bash
set -euo pipefail

GENERATED_FILE="$1"
SOURCE_FILE="$2"

if ! diff -u "$SOURCE_FILE" "$GENERATED_FILE"; then
    echo "Error: Generated file is out of date. Please run:" >&2
    echo "  bazel run //src:$(basename "$SOURCE_FILE" .toml)_update" >&2
    exit 1
fi
