#!/usr/bin/env bash
# Jules environment setup.
# Full chezmoi apply minus removes. remove_ entries are excluded permanently
# as a defensive policy — removes may delete paths Jules depends on.
set -euo pipefail

echo "Setting up dotfiles environment..."
echo "User: $(whoami)"
export GIT_COMMIT_HASH=$(git rev-parse HEAD)
echo "Commit: ${GIT_COMMIT_HASH}"

export DEBIAN_FRONTEND=noninteractive

CHEZMOI_CI_VERSION=$(grep 'CHEZMOI_VERSION:' .github/workflows/ci.yml | awk '{print $2}' | tr -d '"' | tr -d "'")

install_chezmoi() {
    { set +x; } 2>/dev/null
    sh -c "$(curl -fsLS get.chezmoi.io)" -- -b "$HOME/.local/bin" -t "${CHEZMOI_CI_VERSION}"
    { set -x; } 2>/dev/null
    export PATH="$HOME/.local/bin:$PATH"
}

if ! command -v chezmoi &>/dev/null; then
    install_chezmoi
else
    current_version=$(chezmoi --version | awk '{print $3}' | tr -d ',')
    [ "${current_version}" != "${CHEZMOI_CI_VERSION}" ] && install_chezmoi || echo "chezmoi ${CHEZMOI_CI_VERSION} ok"
fi

CHEZMOI_SOURCE="$(pwd)"
GOMAXPROCS=1 chezmoi apply \
    --source="${CHEZMOI_SOURCE}" --destination="${HOME}" --no-tty \
    --exclude=remove

export PATH="$HOME/.local/bin:${PATH}"

# Detect bash -l stdout pollution before Jules' env-save hook runs.
# The hook executes `bash -l -c 'env'` and parses stdout as KEY=VALUE pairs.
# Any non-KEY=VALUE output (warnings, banners, missing-tool messages) corrupts
# the parse silently, breaking all subsequent Jules tasks with no clear error.
bash_l_stdout=$(bash -l -c 'true' 2>/dev/null)
if [[ -n "$bash_l_stdout" ]]; then
    echo "ERROR: bash -l produced stdout — Jules env-save hook will fail." >&2
    echo "~/.bash_profile or a file it sources is printing to stdout in a non-interactive login shell." >&2
    echo "Fix: gate the output behind [[ \$- == *i* ]] or redirect to stderr." >&2
    echo "Stdout was:" >&2
    printf '%s\n' "$bash_l_stdout" >&2
    exit 1
fi
echo "bash -l stdout: clean"

git config --global commit.gpgsign false
echo "Environment ready"
