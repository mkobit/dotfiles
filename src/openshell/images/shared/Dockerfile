# syntax=docker/dockerfile:1@sha256:572cebbc2b15e6f84c077742952674889cb63cd5e9b80abdffcbe587b6f19183
# Build with a tracked source archive, then copy /sandbox into a repository image.

FROM debian:bookworm-slim@sha256:e67eeead736ff7bbe258ef088bff683635c561b1fcfefad0806c1df4ab49ce0e AS base

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
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder

ARG TARGETARCH
RUN case "$TARGETARCH" in \
        amd64) checksum=1b98a567f726f41540414aea4caf912699d53e248b29ccf8369cf553657b2374 ;; \
        arm64) checksum=bf89495d1aab5e4fa0fc1ba9457837b34ee8dec9b787570f2de3e1c12a5835a5 ;; \
        *) exit 1 ;; \
    esac \
    && curl --retry 5 -fsSL -o /tmp/chezmoi.tar.gz \
        https://github.com/twpayne/chezmoi/releases/download/v2.74.0/chezmoi_2.74.0_linux_${TARGETARCH}.tar.gz \
    && echo "${checksum}  /tmp/chezmoi.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/chezmoi.tar.gz -C /usr/local/bin chezmoi \
    && rm /tmp/chezmoi.tar.gz

RUN --mount=type=bind,target=/tmp/dotfiles,readonly --mount=type=cache,id=openshell-chezmoi,target=/tmp/chezmoi-cache mkdir -p /sandbox/.local/bin && chezmoi apply \
        --no-tty \
        --source /tmp/dotfiles \
        --config /tmp/dotfiles/src/openshell/images/shared/sandbox-chezmoi.toml \
        --destination /sandbox \
        --cache /tmp/chezmoi-cache \
        --persistent-state /tmp/chezmoi-state.boltdb \
    && rm -f /sandbox/.claude.json \
    && chown -R "${SANDBOX_UID}:${SANDBOX_GID}" /sandbox

FROM base
COPY --from=builder /usr/local/bin/chezmoi /usr/local/bin/chezmoi
COPY --from=builder --chown=${SANDBOX_UID}:${SANDBOX_GID} /sandbox /sandbox
WORKDIR /sandbox
