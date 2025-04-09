#!/bin/bash

# Simple test script for toolchains
set -e

# Run the tool tester
$(dirname $0)/test_tools

# Check that the report file was created
if [ ! -f "$(dirname $0)/test_tools.report" ]; then
  echo "FAIL: Report file not created"
  exit 1
fi

echo "Toolchain tests passed"
exit 0