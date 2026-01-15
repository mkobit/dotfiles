#!/bin/sh
cd "{{ .chezmoi.sourceDir }}"

# First build the target and redirect logs. Only show logs if build breaks.
if ! bazel build {{ .target }} > /dev/null 2>&1; then
    # Show the build error
    bazel build {{ .target }}
    exit 1
fi

exec bazel run --ui_event_filters=-info,-stdout,-stderr --noshow_progress {{ .target }} -- "$@"
