#!/bin/sh
if command -v bazel >/dev/null 2>&1; then
    bazel build //src/transcriber:transcribe_bundled
else
    echo "Bazel not found, skipping build of transcriber."
fi
