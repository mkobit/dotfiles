#!/bin/bash
# Jules environment setup for Bazel dotfiles repository
# Docs: https://jules.google/docs/environment/

set -euo pipefail

echo "Setting up Bazel dotfiles environment..."

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

# Install Bazelisk if missing
if ! command -v bazel &> /dev/null; then
    echo "Installing bazelisk..."
    sudo curl -fsSL https://github.com/bazelbuild/bazelisk/releases/latest/download/bazelisk-linux-amd64 -o /usr/local/bin/bazel
    sudo chmod +x /usr/local/bin/bazel
fi

# Verify Environment
bazel --version

# Build & Test
echo "Building (personal)..."
bazel build //... --//config:profile=personal

echo "Running tests..."
bazel test //...

echo "Environment ready"
