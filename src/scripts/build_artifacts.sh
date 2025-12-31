#!/bin/bash
set -euo pipefail

# This script builds the hello_world tool using Bazel and copies the artifact
# to a cache location where chezmoi templates can pick it up.

CACHE_DIR="${HOME}/.cache/dotfiles/bazel_artifacts"
mkdir -p "${CACHE_DIR}"

echo "Building hello_world tool..."
# Ensure we run from the repo root.
REPO_ROOT="${CHEZMOI_SOURCE_DIR:-.}"
if [ -d "${REPO_ROOT}/src" ]; then
    # We are likely at repo root
    BAZEL_CMD="bazel"
else
    echo "Could not locate repo root."
    exit 1
fi

# Run Bazel build with --build_python_zip to generate a zipapp
"${BAZEL_CMD}" build --build_python_zip //src/python_tools/hello_world:hello_world

# Locate the zip output
# Bazel output layout can vary, but standard is bazel-bin/package/name.zip
ZIP_OUTPUT="bazel-bin/src/python_tools/hello_world/hello_world.zip"

if [ ! -f "${ZIP_OUTPUT}" ]; then
    echo "Error: Expected output ${ZIP_OUTPUT} not found."
    exit 1
fi

DEST="${CACHE_DIR}/hello_world"

# Create the executable zipapp
# 1. Write the shebang
echo '#!/usr/bin/env python3' > "${DEST}"
# 2. Append the zip content
cat "${ZIP_OUTPUT}" >> "${DEST}"
# 3. Make executable
chmod +x "${DEST}"

echo "Artifact available at ${DEST}"
