#!/bin/sh
cd "{{ .chezmoi.sourceDir }}"
exec bazel run {{ .target }} -- "$@"
