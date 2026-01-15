#!/bin/sh
cd "{{ .chezmoi.sourceDir }}"

# Create a temporary file for build logs
log_file=$(mktemp)

# Ensure cleanup on exit (e.g., if build fails or script is interrupted)
trap 'rm -f "$log_file"' EXIT INT TERM

# First build the target and redirect logs.
if ! bazel build {{ .target }} > "$log_file" 2>&1; then
    # Show the build error
    cat "$log_file"
    exit 1
fi

# Build succeeded. Clean up log file and untrap before exec.
rm -f "$log_file"
trap - EXIT INT TERM

exec bazel run --ui_event_filters=-info,-stdout,-stderr --noshow_progress {{ .target }} -- "$@"
