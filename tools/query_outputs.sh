#!/bin/bash
# Simple script to query the output paths of generated vimrc files
set -euo pipefail

# Get the bazel-bin directory
BAZEL_BIN=$(bazel info bazel-bin)

# Define the generated .vimrc files
DEFAULT_VIMRC="${BAZEL_BIN}/modules/vim/vimrc.vimrc"
WORK_VIMRC="${BAZEL_BIN}/modules/vim/work_vimrc.vimrc"
PERSONAL_VIMRC="${BAZEL_BIN}/modules/vim/personal_vimrc.vimrc"

# Print the paths
echo "${DEFAULT_VIMRC}"
echo "${WORK_VIMRC}"
echo "${PERSONAL_VIMRC}"