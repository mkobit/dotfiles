#!/bin/bash
set -euxo pipefail

# Install required tools
sudo apt-get update -qq
sudo apt-get install -qq -y git tmux vim-nox zsh

# Install Bazelisk
echo "=== Installing Bazelisk ==="
npm install -g @bazel/bazelisk

# Verify tools are available
echo "=== Tool Verification ==="
git --version
tmux -V
vim --version | head -1
zsh --version
bazel --version

# Build and test with personal profile
echo "=== Building and testing with personal profile ==="
bazel test //... --//config:profile=personal

# Build and test with work profile
echo "=== Building and testing with work profile ==="
bazel test //... --//config:profile=work

echo "✅ Snapshot script completed successfully"
