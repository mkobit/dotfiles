#!/bin/bash
set -euxo pipefail

# Install required tools for toolchain discovery
sudo apt-get update -qq
sudo apt-get install -qq -y git zsh curl

# Install Bazelisk
echo "=== Installing Bazelisk ==="
BAZELISK_VERSION="v1.19.0" # A recent version of bazelisk
sudo curl -fLo /usr/local/bin/bazel https://github.com/bazelbuild/bazelisk/releases/download/${BAZELISK_VERSION}/bazelisk-linux-amd64
sudo chmod +x /usr/local/bin/bazel

# Verify tools are available
echo "=== Tool Verification ==="
git --version
zsh --version
bazel --version

# Build and test with personal profile
echo "=== Building and testing with personal profile ==="
bazel test //... --//config:profile=personal

# Build and test with work profile
echo "=== Building and testing with work profile ==="
bazel test //... --//config:profile=work

echo "✅ Snapshot script completed successfully"
