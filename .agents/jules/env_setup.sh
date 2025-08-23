#!/bin/bash
# Jules environment setup for Bazel dotfiles repository

set -euo pipefail

echo "Setting up Bazel dotfiles environment..."

echo "--- Diagnostic Information ---"
echo "User: $(whoami)"
echo "Environment variables:"
env
export GIT_COMMIT_HASH=$(git rev-parse HEAD)
export GIT_COMMIT_DATE=$(git log -1 --format=%cI)
echo "Git Commit Hash: ${GIT_COMMIT_HASH}"
echo "Git Commit Date: ${GIT_COMMIT_DATE}"
echo "------------------------------"

# Install required tools if not present
install_if_missing() {
    for tool in "$@"; do
        if ! command -v "$tool" &> /dev/null; then
            echo "Installing $tool..."
            sudo apt-get install -y "$tool"
        fi
    done
}

echo "Updating package list..."
sudo apt-get update

echo "Checking for and installing required tools..."
install_if_missing zsh tmux vim neovim jq

# Install bazelisk if not present
if ! command -v bazel &> /dev/null; then
    echo "Installing bazelisk..."
    curl -fsSL https://github.com/bazelbuild/bazelisk/releases/latest/download/bazelisk-linux-amd64 -o /tmp/bazel
    chmod +x /tmp/bazel
    sudo mv /tmp/bazel /usr/local/bin/bazel
fi

# Verify Bazel installation
bazel version

# Build personal profile
echo "Building personal profile..."
bazel build //... --//config:profile=personal

# Run all tests to verify repository
echo "Running tests..."
bazel test //...

echo " Environment ready"