#!/bin/bash
set -euo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Run build
if ! build_output=$(bazel build //... 2>&1); then
    jq -n --arg msg "Build failed" --arg details "$build_output" \
        '{status: "error", message: $msg, details: $details}'
    exit 1
fi

# Run tests
if ! test_output=$(bazel test //... 2>&1); then
    jq -n --arg msg "Tests failed" --arg details "$test_output" \
        '{status: "error", message: $msg, details: $details}'
    exit 1
fi

jq -n '{status: "success", message: "Build and tests passed"}'
