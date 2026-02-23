#!/bin/bash
set -euo pipefail

RULES_BINARY="$1"
"$RULES_BINARY" --version
