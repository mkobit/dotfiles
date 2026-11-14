#!/bin/sh
set -eu

case "${1:-}" in
    system)
        export DEBIAN_FRONTEND=noninteractive
        apt-get update
        apt-get install -y --no-install-recommends ca-certificates git gh gnupg unzip zip xz-utils tar gzip
        if ! command -v npm >/dev/null 2>&1; then
            apt-get install -y --no-install-recommends nodejs npm
        fi
        ;;
    project)
        : "${WORKSPACE_DIR:?The private guest workspace is required}"
        bootstrap=/home/agent/.local/share/dotfiles/bootstrap
        npm install --prefix "$bootstrap" --no-audit --no-fund \
            --before="$(date -u -d '21 days ago' +%Y-%m-%dT%H:%M:%SZ)" mise@2026.10.23
        export PATH="$bootstrap/node_modules/.bin:/home/agent/.local/bin:$PATH"
        export MISE_YES=1
        export MISE_MINIMUM_RELEASE_AGE=7d
        export UV_EXCLUDE_NEWER=P7D
        export UV_PYTHON=/home/agent/.local/share/mise/installs/python/3.14.7/bin/python3
        export UV_PYTHON_PREFERENCE=system
        mkdir -p /home/agent/.local/bin /home/agent/.config/mise
        ln -sf "$bootstrap/node_modules/.bin/mise" /home/agent/.local/bin/mise
        cat > /home/agent/.config/mise/config.toml <<'CONFIG'
[tools]
uv = "0.12.10"
chezmoi = "2.74.0"
python = "3.14.7"
"github:gastownhall/beads" = "1.3.2"

[settings]
minimum_release_age = "7d"
http_retries = 5

[env]
UV_EXCLUDE_NEWER = "P7D"
UV_PYTHON = "/home/agent/.local/share/mise/installs/python/3.14.7/bin/python3"
UV_PYTHON_PREFERENCE = "system"
CONFIG
        cd /home/agent
        mise install
        for tool in uv chezmoi python3 bd; do
            ln -sf "$(mise which "$tool")" "/home/agent/.local/bin/$tool"
        done
        cd "$WORKSPACE_DIR"
        test -d .git
        test -f uv.lock
        mise trust mise.toml
        mise exec -- uv sync --all-packages --frozen
        mise --version
        mise exec -- uv --version
        chezmoi --version
        python3 --version
        bd --version
        git --version
        gh --version
        gpg --version
        ;;
    *)
        printf '%s\n' 'Expected system or project installation phase' >&2
        exit 2
        ;;
esac
