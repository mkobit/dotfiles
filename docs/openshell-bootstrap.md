# OpenShell host bootstrap and sandbox workflow

This guide covers host initialization, credential provider setup, dedicated agent SSH commit signing, standalone `/sandbox` OCI layer builds, and the isolated-clone workflow for NVIDIA OpenShell (`openshell`).

## 1. Host installation and Gateway startup

Run `chezmoi init` to refresh the host install settings.
When `[data.local.bin.openshell].installation_method` is `"github_releases"`, `chezmoi apply` installs the OpenShell CLI, doctor, shell completions, and host command policy.

The base init template also sets `[data.local.bin.openshell].microvm = true` on WSL x86-64.
An overlay must set this key in its own init template to enable the standalone Gateway and VM driver.
The MicroVM Gateway requires read and write access to `/dev/kvm`, the `mke2fs`, `debugfs`, and `e2fsck` tools, and a reachable Docker engine for local image export.

1. Apply these targets on the WSL MicroVM host.

   ```bash
   chezmoi diff ~/.local/bin/openshell ~/.local/bin/openshell-doctor \
     ~/.local/bin/openshell-gateway ~/.local/bin/openshell-driver-vm \
     ~/.config/openshell/microvm-gateway.toml ~/.config/systemd
   chezmoi apply ~/.local/bin/openshell ~/.local/bin/openshell-doctor \
     ~/.local/bin/openshell-gateway ~/.local/bin/openshell-driver-vm \
     ~/.config/openshell/microvm-gateway.toml ~/.config/systemd
   ```

2. Start the user service.
   It listens on `127.0.0.1:17671` and keeps state and certificates under `~/.local/state/openshell-microvm/`.

   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now openshell-microvm.service
   ```

3. Register the Gateway once, then check mutual TLS and run the default guest.

   ```bash
   OPENSHELL_LOCAL_TLS_DIR=~/.local/state/openshell-microvm/tls \
     openshell gateway add https://127.0.0.1:17671 --local --name openshell-microvm
   openshell status -g openshell-microvm
   openshell sandbox create -g openshell-microvm --name microvm-smoke \
     --no-keep --no-tty --no-auto-providers -- id
   ```

Use `systemctl --user restart openshell-microvm.service` after a Gateway or driver update.
Use `systemctl --user disable --now openshell-microvm.service` to stop the service and disable startup.
Use `journalctl --user -u openshell-microvm.service` to inspect Gateway and driver logs.
When you have more than one Gateway, pass `-g openshell-microvm` to provider and sandbox commands for this service.

[OpenShell 0.1.9 MicroVM configuration](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/gateways/configuration#microvm)

## 2. Out-of-band credential bootstrap (`openshell provider`)

Never store GitHub personal access tokens (PATs) or LLM API keys in `chezmoi.toml`.
Register secrets out-of-band in `openshell provider` so the Gateway proxy-substitutes placeholders without exposing raw host credentials inside the sandbox filesystem.

1. Create a fine-grained GitHub PAT scoped only to target repositories with:
   - **Contents**: Read and write
   - **Pull requests**: Read and write
   - **Workflows**: No access (prevents sandboxed runs from modifying `.github/workflows/*`)
   - Pair with GitHub branch rulesets protecting `main`.

2. Review and import the provider profiles for the Gateway.
   Match each profile's executable paths to the tools in the sandbox image.
   Use the official GitHub tutorial to create the provider from a scoped host credential and allow writes to the target repository.
   [OpenShell 0.1.9 GitHub provider and push tutorial](https://docs.nvidia.com/openshell/v0.1.9/tutorials/github-push-access)

3. Check the Gateway and list the registered provider names.

   ```bash
   openshell status -g openshell-microvm
   openshell provider list -g openshell-microvm --names
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

4. Configure how the sandbox receives the dedicated signing key before attempting a signed push.
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

For a local check, use the default policy and the built image.

```bash
openshell sandbox create -g openshell-microvm --name pilot-image \
  --from dotfiles-openshell-sandbox:latest --no-keep --no-tty --no-auto-providers \
  -- /sandbox/.local/bin/codex --version
```

The repository policy still needs the OpenShell 0.1.9 schema update.
Before a GitHub push, use a compatible policy, attach the scoped GitHub provider, and configure dedicated signing.
After the push, fetch the feature branch on the host and verify the signature.

```bash
git fetch origin feat/pilot-change
git log --show-signature origin/feat/pilot-change -n 1
```

[OpenShell 0.1.9 policy schema](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/policies/schema)
