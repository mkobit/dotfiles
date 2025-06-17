#!/bin/bash
set -euo pipefail

echo "=== Integration Testing ==="

# Build all configurations
echo "Building configurations..."
bazel ${BAZEL_STARTUP_OPTS} build \
  //tmux:tmux_conf \
  //git:gitconfig \
  //vim:vimrc \
  //zsh:generated_zshrc \
  ${BAZEL_BUILD_OPTS}

# Test tmux configuration
echo "Testing tmux configuration..."
cp bazel-bin/tmux/tmux.conf ~/.tmux.conf
if tmux -f ~/.tmux.conf -L integration_test new-session -d "echo 'tmux test successful'"; then
  echo "✅ tmux configuration test passed"
else
  echo "❌ tmux configuration test failed"
fi

# Test git configuration
echo "Testing git configuration..."
cp bazel-bin/git/gitconfig ~/.gitconfig.test
if git config -f ~/.gitconfig.test --list >/dev/null 2>&1; then
  echo "✅ git configuration test passed"
else
  echo "❌ git configuration test failed"
fi

# Test vim configuration
echo "Testing vim configuration..."
cp bazel-bin/vim/vimrc ~/.vimrc.test
if vim -u ~/.vimrc.test -c "echo 'vim test successful'" -c "quit" 2>/dev/null; then
  echo "✅ vim configuration test passed"
else
  echo "❌ vim configuration test failed"
fi

echo "Integration tests completed"
