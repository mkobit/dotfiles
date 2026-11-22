# OpenShell host bootstrap and sandbox workflow

This guide covers host initialization, credential provider setup, dedicated agent SSH commit signing, standalone `/sandbox` OCI layer builds, and the isolated-clone workflow for NVIDIA OpenShell (`openshell`).

## 1. Host installation and Gateway startup

When `[data.local.bin.openshell].installation_method` is `"github_releases"` (the default on Linux `amd64`/`arm64` and macOS `darwin/arm64`), `chezmoi apply` installs `~/.local/bin/openshell`, `~/.local/bin/openshell-doctor`, shell completions, and host-gated command policy rules.

1. Apply dotfiles on the host:

   ```bash
   chezmoi apply
   ```

2. On Linux hosts running rootless Docker, enable systemd user linger so the Docker-hosted OpenShell Gateway container survives SSH logout:

   ```bash
   loginctl enable-linger "$USER"
   ```

3. Start the local Docker-hosted OpenShell Gateway:

   ```bash
   openshell gateway start
   ```

## 2. Out-of-band credential bootstrap (`openshell provider`)

Never store GitHub personal access tokens (PATs) or LLM API keys in `chezmoi.toml`.
Register secrets out-of-band in `openshell provider` so the Gateway proxy-substitutes placeholders without exposing raw host credentials inside the sandbox filesystem.

1. Create a fine-grained GitHub PAT scoped only to target repositories with:
   - **Contents**: Read and write
   - **Pull requests**: Read and write
   - **Workflows**: No access (prevents sandboxed runs from modifying `.github/workflows/*`)
   - Pair with GitHub branch rulesets protecting `main`.

2. Register the GitHub provider and LLM API providers on the host:

   ```bash
   openshell provider create github --token "$GITHUB_SANDBOX_PAT"
   openshell provider create anthropic --api-key "$ANTHROPIC_API_KEY"
   openshell provider create openai --api-key "$OPENAI_API_KEY"
   openshell provider create gemini --api-key "$GEMINI_API_KEY"
   ```

3. Run `openshell-doctor` to verify binary presence, Docker daemon readiness, Linux linger status, Gateway health, and redacted provider registration:

   ```bash
   openshell-doctor
   ```

## 3. Dedicated agent SSH signing key setup (`gpg.format = ssh`)

Keep personal GPG keyrings (`~/.gnupg`), `gpg-agent`, `SSH_AUTH_SOCK`, and personal SSH authentication keys strictly on the host.
Provision a dedicated persistent `ed25519` keypair used exclusively for sandboxed commit signing.

1. Generate a passphrase-less signing-only `ed25519` keypair on the host outside any repository workspace:

   ```bash
   install -d -m 0700 ~/.config/openshell/agent-signing
   ssh-keygen -t ed25519 -N "" -C "openshell-agent-signing" -f ~/.config/openshell/agent-signing/id_ed25519
   chmod 0600 ~/.config/openshell/agent-signing/id_ed25519
   ```

2. Register the public key (`~/.config/openshell/agent-signing/id_ed25519.pub`) on GitHub as a **Signing Key only** (never as an Authentication Key).

3. Add the public key to your local `allowed_signers` file so `git log --show-signature` verifies agent-signed commits on the host:

   ```bash
   printf '%s %s\n' "mkobit@gmail.com" "$(cat ~/.config/openshell/agent-signing/id_ed25519.pub)" >> ~/.config/git/allowed_signers
   ```

4. Mount or upload the private key `read_only` (`0600`) at `/sandbox/.agent-signing/id_ed25519` when launching a sandbox.
   Inside `/sandbox`, `GIT_CONFIG_GLOBAL=/sandbox/.config/ai-policy/git/sandbox.gitconfig` sets `gpg.format = ssh`, `gpg.ssh.program = ssh-keygen`, empty `gpg.ssh.defaultKeyCommand =`, and `user.signingkey = /sandbox/.agent-signing/id_ed25519`.
   If `ai.sandbox.signing_key` is empty, `sandbox.gitconfig` falls back to `commit.gpgsign = false` and `tag.gpgSign = false`.

## 4. Building and composing the standalone `/sandbox` OCI layer

Sandboxes do not run `chezmoi apply` at runtime because creation-locked Landlock policies and default-deny OPA egress rules block live downloads and package managers.
Instead, build the reusable `/sandbox` layer from `docker/openshell/Dockerfile`:

1. Build the standalone dotfiles `/sandbox` image from the repository root:

   ```bash
   docker build -f docker/openshell/Dockerfile -t dotfiles-openshell-sandbox:latest .
   ```

2. Compose `/sandbox` into a repository's sandbox image:

   ```dockerfile
   FROM <repo-base-image>
   COPY --from=dotfiles-openshell-sandbox:latest /sandbox /sandbox
   ENV HOME=/sandbox \
       PATH="/sandbox/.local/bin:/sandbox/.local/bin/dotfiles:${PATH}" \
       AGY_CLI_DISABLE_AUTO_UPDATE=true \
       GIT_CONFIG_GLOBAL=/sandbox/.config/ai-policy/git/sandbox.gitconfig
   WORKDIR /sandbox/workspace
   ```

## 5. Isolated-clone sandbox workflow and host `git fetch`

Every sandbox operates on an isolated clone under `/sandbox/workspace` governed by `.openshell/policy.yaml`.
Never mount a host `.git` directory or linked worktree `read_write` into a sandbox.

1. Create and enter a sandbox using the repository's `.openshell/policy.yaml`:

   ```bash
   openshell sandbox create --policy .openshell/policy.yaml --name pilot-task
   ```

2. Inside `/sandbox/workspace`, clone the repository (via the `github` provider or a seeded `git bundle`), create a feature branch, and run the coding agent (`claude`, `codex`, or `agy`).

3. Commit with the agent SSH signing key and push the feature branch over HTTPS via `gh` credential helper:

   ```bash
   gh auth setup-git
   git checkout -b feat/pilot-change
   git commit -S -m "Implement pilot change"
   git push -u origin feat/pilot-change
   ```

4. On the host worktree, fetch and verify the signed branch before review or merge:

   ```bash
   git fetch origin feat/pilot-change
   git log --show-signature origin/feat/pilot-change -n 1
   ```
