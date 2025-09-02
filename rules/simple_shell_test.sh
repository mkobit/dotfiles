#!/bin/bash
set -euo pipefail

# Ultra-simple shell test runner
# First argument is the command, rest are files
cmd="$1"
shift

echo "Running: $cmd $*"
exec $cmd "$@"