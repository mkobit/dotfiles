#!/bin/sh
cd "{{ .chezmoi.sourceDir }}"

# Create a temporary file for build logs
log_file=$(mktemp)

# Ensure cleanup on exit (e.g., if build fails or script is interrupted)
trap 'rm -f "$log_file"' EXIT

# First build the target and redirect logs.
if ! bazel build "{{ .target }}" > "$log_file" 2>&1; then
    # Show the build error
    cat "$log_file"
    exit 1
fi

# Build succeeded. Generate execution script.
script_file=$(mktemp)
trap 'rm -f "$log_file" "$script_file"' EXIT

if ! bazel run --script_path="$script_file" "{{ .target }}" > "$log_file" 2>&1; then
    cat "$log_file"
    exit 1
fi

# Clean up log file.
rm -f "$log_file"

# We use a trap to ensure the generated script is deleted after execution.
# We do not use 'exec' here so that the trap will run when the child process finishes.
trap 'rm -f "$script_file"' EXIT
"$script_file" "$@"
