#!/usr/bin/env bash
set -euo pipefail

: "${APT_CACHE_DIR:?APT_CACHE_DIR must be set}"

mkdir -p "$APT_CACHE_DIR"
sudo install -d -o _apt -g root -m 0700 "$APT_CACHE_DIR/partial"
printf 'Dir::Cache::archives "%s";\nAPT::Keep-Downloaded-Packages "true";\n' "$APT_CACHE_DIR" \
  | sudo tee /etc/apt/apt.conf.d/99-ci-download-cache >/dev/null

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "week=$(date -u +%G-%V)" >> "$GITHUB_OUTPUT"
fi
