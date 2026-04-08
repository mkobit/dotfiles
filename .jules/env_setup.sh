#!/bin/bash
# Jules environment setup for dotfiles repository
# Docs: https://jules.google/docs/environment/

set -euo pipefail

echo "Setting up dotfiles environment..."

# Check and install tools first
TOOLS="zsh tmux vim jq curl git"
MISSING=""
for tool in $TOOLS; do
    if ! command -v "$tool" &> /dev/null; then
        MISSING="$MISSING $tool"
    fi
done

# Special check for neovim (command 'nvim', package 'neovim')
if ! command -v nvim &> /dev/null; then
    MISSING="$MISSING neovim"
fi

if [ -n "$MISSING" ]; then
    echo "Installing missing tools:$MISSING..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq $MISSING
fi

# Diagnostic Info
echo "User: $(whoami)"
echo "Git Commit: $(git rev-parse --short HEAD) ($(git log -1 --format=%cI))"


echo "Environment ready"
