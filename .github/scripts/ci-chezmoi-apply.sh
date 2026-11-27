#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 {init|doctor|prefetch|apply|sbx-version|mise-prune}" >&2
  exit 2
}

chezmoi_cmd() {
  : "${CHEZMOI_CACHE_DIR:?}" "${CHEZMOI_CONFIG:?}" "${CHEZMOI_DEST:?}" "${GITHUB_WORKSPACE:?}"
  local subcmd="$1"
  shift
  chezmoi "$subcmd" \
    --cache="$CHEZMOI_CACHE_DIR" \
    --config="$CHEZMOI_CONFIG" \
    --source="$GITHUB_WORKSPACE" \
    --destination="$CHEZMOI_DEST" \
    "$@"
}

cmd_init() {
  : "${CHEZMOI_DEST:?}"
  mkdir -p "$CHEZMOI_DEST"
  chezmoi_cmd init
}

cmd_doctor() {
  chezmoi_cmd doctor --no-network
}

cmd_prefetch() {
  : "${RUNNER_TEMP:?}"
  local report_dir="$RUNNER_TEMP/integration-reports"
  mkdir -p "$report_dir"
  # Render and cache target state without running installation scripts.
  # Chezmoi has no HTTP retry option; completed downloads remain cached.
  local attempt
  for attempt in 1 2 3 4 5; do
    if chezmoi_cmd apply --dry-run --exclude=scripts --output=/dev/null --verbose=false --progress=false \
      2>&1 | tee "$report_dir/chezmoi-prefetch-$attempt.log"; then
      return 0
    fi
    echo "::warning::chezmoi prefetch attempt $attempt failed"
    if [[ "$attempt" -lt 5 ]]; then
      sleep $((15 * 2 ** (attempt - 1)))
    fi
  done
  return 1
}

cmd_apply() {
  : "${RUNNER_TEMP:?}"
  local report_dir="$RUNNER_TEMP/integration-reports"
  mkdir -p "$report_dir"
  local apply_started_at=$SECONDS
  local apply_result=0
  printf '%s chezmoi apply started\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  chezmoi_cmd apply 2>&1 | tee "$report_dir/chezmoi-apply.log" || apply_result=$?
  printf '%s chezmoi apply finished elapsed_seconds=%s result=%s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$((SECONDS - apply_started_at))" "$apply_result"
  return "$apply_result"
}

cmd_sbx_version() {
  : "${CHEZMOI_DEST:?}" "${RUNNER_OS:?}"
  if [[ "$RUNNER_OS" == "Linux" ]]; then
    "$CHEZMOI_DEST/.local/bin/sbx" --version
  else
    "$(brew --prefix)/bin/sbx" --version
  fi
}

cmd_mise_prune() {
  : "${CHEZMOI_DEST:?}" "${GITHUB_WORKSPACE:?}"
  local mise_bin_dir="$CHEZMOI_DEST/.local/bin"
  if [[ -n "${GITHUB_PATH:-}" ]]; then
    echo "$mise_bin_dir" >> "$GITHUB_PATH"
  fi
  HOME="$CHEZMOI_DEST" "$mise_bin_dir/mise" prune --yes -C "$GITHUB_WORKSPACE"
  HOME="$CHEZMOI_DEST" "$mise_bin_dir/mise" cache prune --yes
}

subcommand="${1:-}"
case "$subcommand" in
  init) cmd_init ;;
  doctor) cmd_doctor ;;
  prefetch) cmd_prefetch ;;
  apply) cmd_apply ;;
  sbx-version) cmd_sbx_version ;;
  mise-prune) cmd_mise_prune ;;
  *) usage ;;
esac
