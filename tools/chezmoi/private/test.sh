#!/bin/bash
#
# Private test script for the chezmoi toolchain and rules.
#
set -euo pipefail

GENERATED_FILE=$1
EXPECTED_CONTENT="Hello, Bazel!"

# Check if the generated file contains the expected content.
if ! grep -q "${EXPECTED_CONTENT}" "${GENERATED_FILE}"; then
    echo "---"
    echo "ERROR: Generated file did not contain the expected content."
    echo "Expected: '${EXPECTED_CONTENT}'"
    echo "---"
    echo "Generated file content:"
    cat "${GENERATED_FILE}"
    echo "---"
    exit 1
fi

echo "SUCCESS: chezmoi toolchain test passed."