#!/bin/bash
# Simple test to validate tmux config syntax

set -e

# Input argument should be the tmux.conf file
TMUX_CONF="$1"

if [ ! -f "$TMUX_CONF" ]; then
    echo "Error: tmux.conf file not found at $TMUX_CONF"
    exit 1
fi

# Check if tmux is available
if ! command -v tmux &> /dev/null; then
    echo "Warning: tmux command not found, skipping syntax check"
    exit 0
fi

# Check the syntax with tmux command
echo "Checking tmux configuration syntax..."
tmux -f "$TMUX_CONF" new-session -d -s syntax_test || {
    echo "Error: tmux configuration syntax check failed"
    exit 1
}
tmux kill-session -t syntax_test

echo "Syntax check passed!"
exit 0