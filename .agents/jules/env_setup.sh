#!/bin/bash
# Jules environment setup for Bazel dotfiles repository

set -euo pipefail

echo "Setting up Bazel dotfiles environment..."

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