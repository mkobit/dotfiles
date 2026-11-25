#!/bin/sh
set -eu

export PATH="/sandbox/.local/bin:/sandbox/.local/bin/dotfiles:$PATH"
export MISE_DATA_DIR=/tmp/project-mise MISE_CACHE_DIR=/tmp/mise-cache MISE_STATE_DIR=/tmp/mise-state
export MISE_HTTP_RETRIES=0 MISE_VERSION_CHECK=0

revision=${1:?Missing project revision}
GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=/bin/false git -c credential.helper= -c http.extraHeader= clone -q --no-checkout https://github.com/mkobit/chezmoi-skills.git /tmp/project
cd /tmp/project
git checkout -q --detach "$revision"
git rev-parse HEAD
mise trust
mise install
mise exec -- bun install --frozen-lockfile
mise run test
