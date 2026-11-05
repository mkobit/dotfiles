#!/bin/sh
set -eu

bootstrap=/home/agent/.local/share/dotfiles/bootstrap
npm install --prefix "$bootstrap" --no-audit --no-fund mise@2026.10.23
export PATH="$bootstrap/node_modules/.bin:$PATH"
export MISE_YES=1
export MISE_MINIMUM_RELEASE_AGE=7d
export UV_EXCLUDE_NEWER=P7D
cd "${WORKSPACE_DIR:?The sandbox workspace is required}"
mise trust mise.toml
mise install uv@0.12.10
cd /home/agent
mise install chezmoi@2.74.0 python@3.14.7
mkdir -p /home/agent/.local/bin
ln -sf "$bootstrap/node_modules/.bin/mise" /home/agent/.local/bin/mise
ln -sf /home/agent/.local/share/mise/installs/chezmoi/2.74.0/chezmoi /home/agent/.local/bin/chezmoi
ln -sf /home/agent/.local/share/mise/installs/python/3.14.7/bin/python3 /home/agent/.local/bin/python3
cd "${WORKSPACE_DIR:?The sandbox workspace is required}"
mise exec -- uv --version
chezmoi --version
python3 --version
export UV_PYTHON=/home/agent/.local/share/mise/installs/python/3.14.7/bin/python3
export UV_PYTHON_PREFERENCE=system
mise exec -- uv python find --no-python-downloads
