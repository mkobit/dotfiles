#!/usr/bin/env bash
# Jules environment setup for dotfiles repository
# Docs: https://jules.google/docs/environment/

set -euo pipefail

echo "Setting up dotfiles environment..."

# Diagnostic Info
echo "--- Diagnostic Information ---"
echo "User: $(whoami)"
GIT_COMMIT_HASH=$(git rev-parse HEAD)
GIT_COMMIT_DATE=$(git log -1 --format=%cI)
export GIT_COMMIT_HASH
export GIT_COMMIT_DATE
echo "Git commit hash: ${GIT_COMMIT_HASH}"
echo "Git commit date: ${GIT_COMMIT_DATE}"
echo "------------------------------"

export MISE_DEBUG=1

# Step 1: Install mise and repo tools.
# Root .mise.toml + mise.lock are self-consistent (uv only), so locking works here.
if ! command -v mise &>/dev/null; then
    echo "Installing mise..."
    curl -s https://mise.run | MISE_VERSION="v2026.4.9" /usr/bin/env bash
    export PATH="$HOME/.local/bin:$PATH"
fi

mise trust
mise install
eval "$(mise activate bash)"
mise doctor

# Step 2: Install chezmoi matching CI version, then apply it.
# This writes the global mise config (dot_config/mise/) to $HOME, which is required
# before global tools can be installed with the correct lockfile.
CHEZMOI_CI_VERSION=$(grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+' .github/workflows/ci.yml | head -n 1)

install_chezmoi() {
    echo "Installing chezmoi ${CHEZMOI_CI_VERSION}..."
    /usr/bin/env bash -c "$(curl -fsLS get.chezmoi.io)" -- -b $HOME/.local/bin -t "${CHEZMOI_CI_VERSION}"
    export PATH="$HOME/.local/bin:$PATH"
}

if ! command -v chezmoi &>/dev/null; then
    install_chezmoi
else
    current_version=$(chezmoi --version | awk '{print $3}' | tr -d ',')
    if [ "${current_version}" != "${CHEZMOI_CI_VERSION}" ]; then
        echo "Updating chezmoi from ${current_version} to ${CHEZMOI_CI_VERSION}..."
        install_chezmoi
    else
        echo "chezmoi ${CHEZMOI_CI_VERSION} is already installed."
    fi
fi

echo "Applying chezmoi..."
chezmoi apply --source="$(pwd)/src/chezmoi" --destination="$HOME"

# Step 3: Install python dependencies
echo "Installing python dependencies..."
uv sync --all-packages --frozen

echo "Environment ready"
