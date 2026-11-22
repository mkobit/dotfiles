# syntax=docker/dockerfile:1
# Standalone /sandbox OCI builder layer for NVIDIA OpenShell sandboxes.
# Compose into repository sandbox images with:
#   COPY --from=<dotfiles-sandbox-image> /sandbox /sandbox

FROM debian:bookworm-slim

ARG CHEZMOI_VERSION=v2.74.0
ARG SANDBOX_UID=1000
ARG SANDBOX_GID=1000

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/sandbox \
    PATH="/sandbox/.local/bin:/sandbox/.local/bin/dotfiles:${PATH}" \
    AGY_CLI_DISABLE_AUTO_UPDATE=true \
    GIT_CONFIG_GLOBAL=/sandbox/.config/ai-policy/git/sandbox.gitconfig

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        openssh-client \
        python3 \
        tmux \
        xz-utils \
        zsh \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /sandbox/.local/bin \
    && sh -c "$(curl --retry 5 -fsLS https://get.chezmoi.io)" -- -b /usr/local/bin -t "${CHEZMOI_VERSION}"

WORKDIR /tmp/dotfiles
COPY . /tmp/dotfiles
COPY docker/openshell/sandbox-chezmoi.toml /tmp/sandbox-chezmoi.toml

RUN chezmoi apply \
        --no-tty \
        --source /tmp/dotfiles \
        --config /tmp/sandbox-chezmoi.toml \
        --destination /sandbox \
        --cache /tmp/chezmoi-cache \
        --persistent-state /tmp/chezmoi-state.boltdb \
    && rm -f /sandbox/.claude.json \
    && rm -rf /tmp/dotfiles /tmp/sandbox-chezmoi.toml /tmp/chezmoi-cache /tmp/chezmoi-state.boltdb \
    && chown -R "${SANDBOX_UID}:${SANDBOX_GID}" /sandbox

WORKDIR /sandbox
