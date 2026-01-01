#!/bin/bash
# Jules environment setup for Dotfiles repository
# Adapted from https://github.com/mkobit/dotfiles/blob/main/.agents/jules/env_setup.sh

set -euo pipefail

# Define constants
CHEZMOI_BIN_DIR="$HOME/.local/bin"
export PATH="$CHEZMOI_BIN_DIR:$PATH"

echo "Setting up Dotfiles environment..."

# 1. Install System Tools
# Tools listed in integration.yml + neovim from example
# Note: 'rg' is the command for 'ripgrep', 'nvim' for 'neovim'
TOOLS="git tmux vim zsh jq curl eza fzf rg"
MISSING=""

for tool in $TOOLS; do
    if ! command -v "$tool" &> /dev/null; then
        MISSING="$MISSING $tool"
    fi
done

# Check for neovim specifically
if ! command -v nvim &> /dev/null; then
    MISSING="$MISSING neovim" # Use package name for MISSING list to simplify logic
fi

if [ -n "$MISSING" ]; then
    echo "Installing missing tools: $MISSING..."
    if command -v sudo &> /dev/null && sudo -v &> /dev/null; then
         sudo apt-get update -qq
         # Map command names to package names where necessary
         PKG_LIST=""
         for tool in $MISSING; do
             case "$tool" in
                 vim) PKG_LIST="$PKG_LIST vim-nox" ;;
                 rg) PKG_LIST="$PKG_LIST ripgrep" ;;
                 nvim|neovim) PKG_LIST="$PKG_LIST neovim" ;;
                 *) PKG_LIST="$PKG_LIST $tool" ;;
             esac
         done
         # Trim leading space
         PKG_LIST=$(echo "$PKG_LIST" | xargs)

         sudo apt-get install -y -qq $PKG_LIST || echo "⚠️  Some packages failed to install via apt (likely 'eza' if repo not added). Please check manually."
    else
        echo "⚠️  Sudo not available or authorized. Skipping system package installation."
        echo "   Please manually install: $MISSING"
    fi
else
    echo "✅ System tools already installed."
fi

# 2. Install Chezmoi (if missing)
if ! command -v chezmoi &> /dev/null; then
    echo "Installing chezmoi..."
    mkdir -p "$CHEZMOI_BIN_DIR"
    sh -c "$(curl -fsLS get.chezmoi.io)" -- -b "$CHEZMOI_BIN_DIR"
else
    echo "✅ Chezmoi already installed."
fi

# 3. Install Bazelisk (as bazel)
if ! command -v bazel &> /dev/null; then
    echo "Installing bazelisk..."
    mkdir -p "$CHEZMOI_BIN_DIR"
    ARCH="amd64"
    if [[ "$(uname -m)" == "aarch64" ]]; then ARCH="arm64"; fi

    # Download to local bin
    curl -fsSL "https://github.com/bazelbuild/bazelisk/releases/latest/download/bazelisk-linux-${ARCH}" -o "$CHEZMOI_BIN_DIR/bazel"
    chmod +x "$CHEZMOI_BIN_DIR/bazel"
else
    echo "✅ Bazel (Bazelisk) already installed."
fi

# 4. Diagnostic Info
echo "User: $(whoami)"
if command -v git &> /dev/null; then
    echo "Git Commit: $(git rev-parse --short HEAD)"
fi

# 5. Build and Test
# Using personal profile as default
PROFILE="personal"
echo "Building (profile=$PROFILE)..."
bazel build //... --//config:profile=$PROFILE

echo "Running tests (profile=$PROFILE)..."
bazel test //... --//config:profile=$PROFILE

echo "🎉 Environment ready!"
