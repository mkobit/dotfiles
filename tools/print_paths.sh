#!/bin/bash
# Script to print paths to generated dotfiles
set -euo pipefail

# Build the targets first to ensure they exist
echo "Building vim configurations..."
bazel build //modules/vim:vimrc //modules/vim:work_vimrc //modules/vim:personal_vimrc

# Get the bazel-bin directory
BAZEL_BIN=$(bazel info bazel-bin)

# Define paths to the generated files
DEFAULT_VIMRC="${BAZEL_BIN}/modules/vim/vimrc.vimrc"
WORK_VIMRC="${BAZEL_BIN}/modules/vim/work_vimrc.vimrc"
PERSONAL_VIMRC="${BAZEL_BIN}/modules/vim/personal_vimrc.vimrc"

echo ""
echo "Generated dotfiles paths:"
echo "  vimrc: ${DEFAULT_VIMRC}"
echo "  work_vimrc: ${WORK_VIMRC}"
echo "  personal_vimrc: ${PERSONAL_VIMRC}"

echo ""
echo "Instructions for manual installation:"
echo "  1. Create symbolic links to the generated files"
echo "  2. Example: ln -sf ${DEFAULT_VIMRC} ~/.vimrc"
echo "  3. Or include in your existing configuration:"
echo "     source ${DEFAULT_VIMRC}"
echo ""

# Verify the files exist and show content preview
echo "Verifying files..."
for file in "${DEFAULT_VIMRC}" "${WORK_VIMRC}" "${PERSONAL_VIMRC}"; do
  if [ -f "${file}" ]; then
    echo "✅ $(basename ${file}) exists"
    echo "   First 3 lines:"
    head -n 3 "${file}" | sed 's/^/   /'
    echo ""
  else
    echo "❌ $(basename ${file}) does not exist"
    echo ""
  fi
done

echo ""
echo "How to use these files:"
echo "  1. Direct symlink (replaces your existing .vimrc):"
echo "     ln -sf ${DEFAULT_VIMRC} ~/.vimrc"
echo ""
echo "  2. Include in existing .vimrc (preserves your config):"
echo "     echo 'source ${DEFAULT_VIMRC}' >> ~/.vimrc"
echo ""
echo "  3. Switch between variants:"
echo "     ln -sf ${WORK_VIMRC} ~/.vimrc   # Work configuration"
echo "     ln -sf ${PERSONAL_VIMRC} ~/.vimrc   # Personal configuration"