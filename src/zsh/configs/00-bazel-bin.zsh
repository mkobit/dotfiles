# Bazel-managed binary PATH setup
# This file should be sourced early to ensure Bazel-managed binaries take precedence
# over system binaries in the PATH.

if [ -f "${BUILD_WORKSPACE_DIRECTORY:-}/bazel-bin/bazel_bin_path.sh" ]; then
    source "${BUILD_WORKSPACE_DIRECTORY:-}/bazel-bin/bazel_bin_path.sh"
fi 