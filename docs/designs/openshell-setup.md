# Replace `sbx` with NVIDIA OpenShell via `chezmoi`

* **Author:** Mike Kobit
* **Status:** Proposed
* **Date:** 2026-11-21

--------------------------------------------------------------------------------

## Overview

This design replaces Docker Sandboxes (`sbx`) with NVIDIA OpenShell (`NVIDIA/OpenShell`) across host workstations and sandboxed agent environments.
A `chezmoi` BOM gate (`[data.local.bin.openshell]`) controls host installation (`openshell` binary, shell completions, `openshell-doctor`, and host-only command permissions), while a static build-time `chezmoi` profile assembles the `/sandbox` agent tooling layer (`claude`, `codex`, `agy`, plugins, and skills) into a reusable OCI builder image.
Individual repositories own contributor-portable `policy.yaml` and base images, while personal dotfiles and `openshell provider` credentials compose on top.

## The problem

1. **Docker account coupling and approval friction**: `sbx` ties sandbox creation to Docker authentication and Docker servers, and running `sbx run` or `sbx exec` on the host triggers repeated command-approval prompts.
2. **Secret and signing isolation**: Sandboxed agents need to push branches and sign commits without exposing host tokens, `~/.gnupg`, or personal SSH keys inside the sandbox.
3. **Host vs. sandbox path and network mismatch**: Repository `policy.yaml` files enforce creation-locked Landlock filesystem rules and deny-by-default OPA network egress.
   Running `chezmoi apply` inside a live sandbox fails when fetching plugins or writing outside repo directories, while raw-copying host `~/.local` or `~/.claude` breaks absolute `{{ .chezmoi.destDir }}` paths.
4. **Contributor portability**: Repositories such as `canopy` and `storagemaxxing` must stay runnable by any contributor without requiring this dotfiles repository or personal provider names.

## Goals

* Gate host `openshell` installation through `[data.local.bin.openshell].installation_method` in `src/chezmoi/.chezmoi.toml.tmpl` (`"github_releases"` on Linux `amd64`/`arm64` and macOS `darwin/arm64`, `"none"` otherwise), defaulting via `dig` to `"none"` for CI and overlays.
* Manage `openshell` release archive installation (`v0.1.9` `openshell-<target>.tar.gz`) through `.chezmoidata/bin/openshell.toml` and `src/chezmoi/dot_local/bin/.chezmoiexternals/bins.toml.tmpl`, alongside host `openshell-doctor` diagnostics.
* Assemble a standalone `/sandbox` OCI builder layer via `chezmoi apply --config /tmp/sandbox-chezmoi.toml --destination /sandbox` (which automatically invokes `plugin_bridge.py` via `run_after_agent-plugin-bridge.sh.tmpl`), excluding host-specific runtime state and requiring zero runtime network fetches inside sandboxes.
* Provision host secrets (such as fine-grained GitHub PATs and LLM API keys) out-of-band into `openshell provider` with documented bootstrap steps, keeping zero plaintext tokens in `chezmoi.toml`.
* Standardize on isolated clones (`/sandbox/workspace`) for v1 sandboxes, using `gh` CLI with proxy-substituted PATs for `git push` and a dedicated persistent signing-only SSH keypair (`gpg.format = ssh`) for verifiable agent commits.
* Retire `sbx` command permissions via `[ai.command_policy.retired_commands]`, gate `openshell` command grants strictly to host installs, and remove `sbx`-specific scripts, templates, and skills.

## Non-goals

* Building a custom Python wrapper around `openshell` (`src/python/sandboxr/` is retired in a separate PR).
* Designing the Layer 4 unattended factory polling daemon, concurrency/TTL/spend tracker, and run-state scheduler (deferred to a separate design).
* Running live `chezmoi apply` network fetches inside locked-down runtime sandboxes.
* Mounting host linked worktrees (`.git` common directory) into sandboxes for v1.
* Forwarding raw host `~/.gnupg`, `gpg-agent`, personal SSH authentication keys, or Gateway operator mTLS credentials (`~/.config/openshell/gateways/`) into any sandbox.
* Solving remote IDE integration (`vscode`, `cursor`, `intellij`) and upstream `NVIDIA/OpenShell#1427` / `#749` caveats in the initial rollout.

## Critical user journeys (CUJs)

### CUJ 1: Host workstation initialization and secret bootstrap

* **Given**: A developer sets up a Linux or macOS host with `chezmoi init` and `openshell` is enabled (`"github_releases"`).
* **When**: `chezmoi apply` runs, followed by starting the Docker-hosted Gateway (`openshell gateway start`), out-of-band `openshell provider create` bootstrap, and `openshell-doctor`.
* **Then**: The `openshell` CLI, completions, host-only command policy, and Gateway are active, `openshell provider` holds credentials without plaintext tokens in `chezmoi.toml`, and `openshell-doctor` confirms Gateway health and placeholder substitution.

### CUJ 2: Sandboxed agent run with isolated clone and SSH agent signing

* **Given**: A repository owns a contributor-portable `policy.yaml` and base image, and the host has built or pulled the standalone `/sandbox` dotfiles OCI layer and uploaded/mounted the dedicated agent signing-only SSH key.
* **When**: A developer or automation launches an OpenShell sandbox with an isolated clone in `/sandbox/workspace` (cloned via `github` provider or seeded from a host `git bundle`).
* **Then**: The agent runs `claude`, `codex`, or `agy` (Antigravity CLI) with personal skills and plugins under Landlock/seccomp/OPA enforcement, signs commits with the dedicated agent SSH key (`gpg.format = ssh`), and pushes via `gh` / HTTPS (`openshell provider` PAT) to a feature branch for host review and fetch.

### CUJ 3: Non-interactive CI and overlay compatibility

* **Given**: GitHub Actions CI runs `chezmoi init` and `chezmoi apply` non-interactively, or a downstream overlay replaces `.chezmoi.toml.tmpl` without defining `[data.local.bin.openshell]` or `[data.ai.sandbox]`.
* **When**: `chezmoi` evaluates templates and scripts.
* **Then**: Interactive prompts are skipped under `CI`, missing keys default via `dig` to `"none"` or `""`, and `chezmoi apply` completes idempotently without errors.

## Technical plan (architecture)

### 1. Three-layer composition model

The architecture separates contributor-portable repository definitions from personal dotfiles and host credentials:

```text
+-----------------------------------------------------------------------+
| Layer 2: Host Gateway & Providers (Host Only)                         |
| - openshell binary + Docker-hosted Gateway (openshell gateway start)  |
| - openshell provider instances (fine-grained GitHub PAT, LLM keys)    |
| - Host-only openshell command policy + personal signing key on host   |
+-----------------------------------+-----------------------------------+
                                    | proxy-substitutes secrets + runs
                                    v
+-----------------------------------------------------------------------+
| Layer 1 + Layer 3: Sandbox Runtime Image (Composed OCI Image)         |
| +-------------------------------------------------------------------+ |
| | Layer 1 (Repo-Owned): Base image, language toolchains,            | |
| |   contributor-portable policy.yaml (Landlock, seccomp, OPA rules) | |
| +-------------------------------------------------------------------+ |
| | Layer 3 (Dotfiles-Owned, COPY --from=<dotfiles-sandbox-image>):   | |
| |   /sandbox/.local/bin/{claude,codex,agy,rg,fd,jq,gh,mise,...}     | |
| |   /sandbox/.local/share/agent-plugins/ & .gemini/config/plugins   | |
| |   /sandbox/.claude/, /sandbox/.codex/, /sandbox/.gemini/,         | |
| |   /sandbox/.dotfiles/git/config & ai-policy/git/sandbox.gitconfig | |
| +-------------------------------------------------------------------+ |
+-----------------------------------------------------------------------+
```

### 2. Chezmoi BOM gating and sandbox profile

* **Host binary gating (`[data.local.bin.openshell]`)** in `src/chezmoi/.chezmoi.toml.tmpl`:
  * Follows the deterministic OS/arch detection pattern of `[data.local.bin.sbx]` (no interactive prompt): sets `installation_method = "github_releases"` on Linux (`amd64`, `arm64`) and Apple Silicon macOS (`arm64`), and `"none"` otherwise.
  * Every template and script reads the value via `dig "local" "bin" "openshell" "installation_method" "none" .` so overlays that omit the key behave as `"none"`.
* **Host-only integrations**:
  * Installs `openshell` shell completions and `openshell-doctor` (which verifies Docker daemon readiness, `openshell gateway info` / `openshell status`, and `openshell provider` substitution).
  * Gates `openshell` command grants in `src/chezmoi/.chezmoidata/ai/command_policy/openshell.toml` under `[ai.command_policy.host_commands.openshell]`, resolved generically in `dot_claude/modify_settings.json` and `dot_gemini/antigravity-cli/modify_settings.json` only when `ne (dig "local" "bin" $feature "installation_method" "none" $) "none"`.
* **Sandbox profile (`docker/openshell/sandbox-chezmoi.toml`)**:
  * Container builds never run interactive `chezmoi init` probes; instead they pass a static config file (`chezmoi apply --config /tmp/sandbox-chezmoi.toml --destination /sandbox`) that sets `openshell`, `sbx`, `betterleaks`, host-only OS package managers, GUI tools, `zsh.set_as_default_login_shell = false`, and `git_hooks.pre_commit` to disabled/`"none"`.
  * Renders only the personal AI agent tooling (`claude`, `codex`, `agy`, `termstatus` statusline tool, `.dotfiles/git/config`, `ai-policy/git/sandbox.gitconfig`, plugins, skills, and core CLI utilities `rg`, `fd`, `jq`, `gh`, `mise`, `bd` beads CLI, `pi`).

### 3. Standalone `/sandbox` OCI builder layer

* **Single builder image**: A dedicated dotfiles builder `Dockerfile` (`FROM debian:bookworm-slim` with `zsh` and `tmux` pre-installed so `run_once_install-{zsh,tmux}.sh.tmpl` exit via `check_command`) sets `HOME=/sandbox` and `PATH="/sandbox/.local/bin:${PATH}"` and runs `chezmoi apply --config /tmp/sandbox-chezmoi.toml --destination /sandbox` (which automatically executes `run_after_agent-plugin-bridge.sh.tmpl` and pipes JSON to `plugin_bridge.py reconcile` on `stdin`), then sets unprivileged ownership (`chown -R ${SANDBOX_UID}:${SANDBOX_GID} /sandbox`, defaulting to `1000:1000`) so OpenShell's non-root runtime user can write session state under `/sandbox/.claude/`, `/sandbox/.codex/`, and `/sandbox/.gemini/`.
* **Composition into repo images**: Repository images compose the layer with `COPY --from=<dotfiles-sandbox-image> /sandbox /sandbox`, avoiding an `M x N` `chezmoi` rebuild matrix across repositories.
* **Why `--destination /sandbox` at build time**: Symlinks (`.local/bin/claude`, `.local/bin/codex`), `.claude/plugins/{known_marketplaces.json,installed_plugins.json}`, `.claude/settings.json` (`extraKnownMarketplaces`), `.codex/config.toml` (`[marketplaces.*]`), and `termstatus` uv venv shebangs embed absolute `{{ .chezmoi.destDir }}` paths.
  Rendering to `/sandbox` ensures generated symlinks, plugin manifests, and venv shebangs resolve under `/sandbox` rather than host paths.
* **Sanitized config**: In sandbox mode, `AGY_CLI_DISABLE_AUTO_UPDATE=true` is set, host-specific `[projects.*]` / `trustedWorkspaces` / `~/.claude.json` runtime state is excluded, `claude_code.toml` keeps `sandbox.enabled = false` to avoid nested `bwrap` conflicts under OpenShell seccomp, and `git_hooks.pre_commit` is `"none"` (so missing `betterleaks` secret-scanner hooks do not break `git commit`).

### 4. Isolated clones, SSH agent signing, and `gh` push boundary

* **Isolated clones (`/sandbox/workspace`)**: Every sandbox operates on a self-contained clone under `/sandbox/workspace`, keeping Landlock `filesystem_policy.read_write` rules static (`/sandbox/workspace`, `/tmp`, and `/sandbox/.{claude,codex,gemini}`).
  Host `.git` directories are never mounted `read_write`, preventing `.git/hooks/*` or `.git/config` tampering, and changes return to the host via `git fetch` or `git bundle`.
* **Dedicated signing-only SSH key (`gpg.format = ssh`)**: The host keeps personal GPG/SSH keys strictly on the host.
  A dedicated persistent `ed25519` keypair (registered in `allowed_signers` under an agent identity and on GitHub as a **Signing Key only**, never an Authentication Key) is uploaded or mounted `read_only` outside `/sandbox/workspace` (for example `/sandbox/.agent-signing/id_ed25519`) at sandbox launch.
  `src/chezmoi/dot_config/ai-policy/git/sandbox.gitconfig.tmpl` overrides `personal.gitconfig.tmpl` with `gpg.format = ssh`, `gpg.ssh.program = ssh-keygen`, empty `gpg.ssh.defaultKeyCommand =`, and `user.signingkey` from `dig "ai" "sandbox" "signing_key" "" .` (falling back to `commit.gpgsign = false` when no key path is configured).
* **`gh` CLI + proxy-substituted PAT push**: `git push` over HTTPS uses `gh auth git-credential` with `GH_TOKEN` / `GITHUB_TOKEN` injected by `openshell provider`.
  The host uses a fine-grained PAT (or GitHub App token) scoped to target repositories with **Contents: Read and write**, **Pull requests: Read and write**, and **Workflows: No access**, paired with GitHub branch rulesets protecting `main`.

## Alternatives considered

### Alternative A: Runtime `chezmoi apply` inside live sandboxes

* **Pros**: No host or CI image build step; sandboxes pull dotfiles directly on startup.
* **Cons**: Landlock locks filesystem policies at creation, strict OPA egress rules block GitHub and package-manager fetches, and full `chezmoi apply` triggers host-only OS package steps and rate limits.
* **Reason for rejection**: Live network and filesystem restrictions inside contributor-portable `policy.yaml` files prevent runtime `chezmoi apply` from succeeding without weakening sandbox isolation.

### Alternative B: Host-rendered directory mounted into `/sandbox`

* **Pros**: Fast iteration without rebuilding OCI images; works against any base image without `COPY --from`.
* **Cons**: Requires driver bind-mount support (`enable_bind_mounts = true`, disabled by default in OpenShell), Landlock `filesystem_policy` entries for mounted host paths, and splitting read-only static assets from runtime-writable session files inside `~/.claude/`, `~/.codex/`, and `~/.gemini/`.
* **Reason for rejection**: A standalone `/sandbox` OCI builder image keeps `/sandbox` self-contained with native copy-on-write and avoids host-mount path coupling.

### Alternative C: Forwarding host `gpg-agent` or `ssh-agent` (`SSH_AUTH_SOCK`) into sandboxes

* **Pros**: Agents sign commits directly with the developer's personal key without managing a separate agent key.
* **Cons**: OpenShell isolates host SSH (`SSH_AUTH_SOCK` forwarding is unsupported), and an unfiltered agent socket lets a sandboxed process sign arbitrary commits (including `.github/workflows/` changes) or authenticate to SSH hosts as the developer.
* **Reason for rejection**: A dedicated signing-only SSH keypair keeps personal keys on the host while preserving cryptographic attribution on agent commits.

### Alternative D: Mounting host linked worktrees (`read_write` on shared `.git` common dir)

* **Pros**: Edits appear immediately on the host filesystem without `git fetch` or `git bundle`.
* **Cons**: Landlock rules are strictly additive, so granting `read_write` to the shared `.git` common directory exposes `.git/hooks/*` and `.git/config` (`core.fsmonitor`, `core.hooksPath`) to sandbox tampering that later executes unsandboxed on the host; linked `.git` files also embed host-absolute `gitdir:` paths that break inside `/sandbox/workspace`.
* **Reason for rejection**: Isolated clones eliminate host `.git` execution risk and keep `policy.yaml` paths static and portable.

### Alternative E: Storing GitHub PATs via `chezmoi promptStringOnce` in `chezmoi.toml`

* **Pros**: Uses existing `[data.secrets]` prompt pattern in `src/chezmoi/.chezmoi.toml.tmpl`.
* **Cons**: Stores raw credentials in plaintext inside `chezmoi.toml`, undermining OpenShell's proxy-substitution model.
* **Reason for rejection**: Out-of-band `openshell provider create` with host bootstrap instructions keeps raw tokens out of `chezmoi` config files.

--------------------------------------------------------------------------------

## Non-functional requirements

* **Security & privacy**: Zero personal signing keys, `~/.gnupg` keyrings, `SSH_AUTH_SOCK` sockets, raw host PATs, or Gateway mTLS operator credentials may enter any sandbox.
  `openshell-doctor` must verify provider placeholder substitution without printing secret values.
* **Reliability**: On Linux, headless hosts running rootless Docker must enable `loginctl enable-linger` so the Docker-hosted Gateway container survives SSH logout.
* **Rollout & rollback**: Phase 0–1 deploy `[data.local.bin.openshell]` (`dig` default `"none"`) while keeping `sbx` active, so rollback requires only setting `openshell.installation_method = "none"` and running `chezmoi apply`.
  Retiring `sbx` command grants uses `[ai.command_policy.retired_commands]` because `modify_settings.json` retains live permissions.

## Risks & mitigations

* **Agent signing key readable inside sandbox**: Because the dedicated agent `ed25519` private key is uploaded/mounted into the sandbox for `ssh-keygen -Y sign`, sandbox code can read it.
  *Mitigation*: Register the key on GitHub **only** as a Signing Key (never an Auth Key), store it outside `/sandbox/workspace` (`0600`), keep it under a distinct agent identity in `allowed_signers`, and rotate it if compromised.
* **Unattended `git push` blast radius**: A compromised sandbox with push access could attempt to alter workflows or protected branches.
  *Mitigation*: Scope the `openshell provider` GitHub token with **Workflows: No access** and enforce GitHub branch rulesets protecting `main`.
* **Builder image staleness**: Pre-building `/sandbox` into a standalone OCI layer can drift from dotfiles updates if not rebuilt.
  *Mitigation*: Trigger dotfiles `/sandbox` image rebuilds on `src/chezmoi/` changes and pin or tag images cleanly.

## Additional resources

* [NVIDIA OpenShell documentation](https://docs.nvidia.com/openshell/)
* [NVIDIA/OpenShell v0.1.9 release](https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.9)
* Existing `sbx` binary catalog and gating: [src/chezmoi/.chezmoi.toml.tmpl](../../src/chezmoi/.chezmoi.toml.tmpl), [src/chezmoi/.chezmoidata/bin/sbx.toml](../../src/chezmoi/.chezmoidata/bin/sbx.toml), [src/chezmoi/.chezmoidata/ai/command_policy/sbx.toml](../../src/chezmoi/.chezmoidata/ai/command_policy/sbx.toml)
* Existing sandbox gitconfig: [src/chezmoi/dot_config/ai-policy/git/sandbox.gitconfig.tmpl](../../src/chezmoi/dot_config/ai-policy/git/sandbox.gitconfig.tmpl)

## Future improvements

* **Interactive remote IDE workflows**: Validate `openshell sandbox ssh-config` / `--editor` (`vscode`, `cursor`) and JetBrains Gateway against upstream `NVIDIA/OpenShell#1427` (`memfd_create` seccomp block) and `NVIDIA/OpenShell#749` (`/dev/ptmx` Landlock issue) once core CLI workflows are stable.
* **Layer 4 factory orchestration**: Design the deterministic host polling daemon, concurrency/TTL/spend caps, orphan sandbox reconciliation, and `$XDG_STATE_HOME/openshell-factory/` logging in a separate design document.
* **Interactive subscription OAuth**: Evaluate whether `openshell provider` can support interactive OAuth flows without placing raw `~/.claude.json` or `~/.codex/auth.json` tokens inside sandboxes.

--------------------------------------------------------------------------------

## Detailed implementation plan

All repository changes below must execute in a dedicated git worktree branched from `main`.

### Rollout phases

| Phase | Scope | Exit criteria |
| :--- | :--- | :--- |
| **Phase 0 (Host & BOM)** | Add `[data.local.bin.openshell]`, binary catalog, completions, `openshell-doctor`, and host-gated command policy alongside intact `sbx`. | `chezmoi apply` passes idempotently on Linux/macOS/CI; `openshell gateway start` and `openshell-doctor` pass on host. |
| **Phase 1 (Sandbox layer & pilot)** | Add `sandbox-chezmoi.toml`, standalone `/sandbox` builder Dockerfile, SSH agent signing gitconfig updates, `openshell` skills/docs, and portable pilot `policy.yaml`. | `/sandbox` OCI layer builds without host leaks; sandboxed agent commits with SSH signing and pushes via `gh` provider. |
| **Phase 2 (`sbx` retirement, deferred)** | Move `sbx` grants to `[ai.command_policy.retired_commands]`, remove `sbx` chezmoi scripts/templates/CI checks/skills, and decouple `exact_repo-bootstrap` / `exact_worker-handoff`. Deferred while `sbx` and `openshell` coexist. | Zero `sbx` references remain in active templates or CI; `pytest`, `ruff`, `ty`, and `shellcheck` pass. |

### WSL MicroVM pilot

On 2026-11-23, the stock Ubuntu MicroVM test passed on the Linux x86-64 WSL 2 host with OpenShell 0.1.9.
The standalone Gateway and VM driver archives matched the published SHA-256 digests.
The test used a temporary Gateway on `127.0.0.1:17671` with separate CLI configuration, state, and TLS credentials.
The CLI reported mutual TLS authentication, the sandbox supervisor reported ready, and `id` exited with code `0` and returned `uid=1000(ubuntu) gid=1000(ubuntu) groups=1000(ubuntu)`.
The test used `nvcr.io/nvidia/base/ubuntu:24.04` and the default policy with no providers or host mounts.

The first host run failed during root disk formatting because the test's `PATH` excluded `/usr/sbin`.
The retry used fresh test state and the installed `mke2fs` 1.47.0.
The VM driver used the local Docker engine to export the Ubuntu image root filesystem.
The test stopped the temporary Gateway and driver after the run.
Keep the managed OpenShell install gated by `[data.local.bin.openshell].installation_method` in the `chezmoi init` configuration.
The standalone Gateway and VM driver were temporary pilot binaries.

The next checks are the `chezmoi` sandbox image and the two-session test.
Define the session topology and its pass criteria before running the two-session test.
Phase 1 still requires evidence that the `/sandbox` image builds without host data and that an agent can sign a commit with SSH and push through the `gh` provider.
Keep SBX available during the pilot.

[OpenShell 0.1.9 release assets](https://github.com/ai-openshell/openshell/releases/expanded_assets/v0.1.9) · [MicroVM Gateway configuration](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/gateways/configuration#microvm)

### Target files to create or modify

#### 1. `src/chezmoi/.chezmoi.toml.tmpl` (Modify)

* **Type / scope**: Chezmoi init control plane.
* **Proposed changes**:
  * Add `[data.local.bin.openshell]` using deterministic OS/arch detection matching `[data.local.bin.sbx]` (`"github_releases"` on Linux `amd64`/`arm64` and macOS `arm64`, `"none"` otherwise, overridable via `--override-data`).
  * Keep `[data.local.bin.sbx]` intact in Phase 0–1 and remove it in Phase 2.

#### 2. `src/chezmoi/.chezmoidata/bin/openshell.toml` & `src/chezmoi/.chezmoidata/bin-updates.toml` (Create / Modify)

* **Type / scope**: Binary catalog and update cadence metadata.
* **Proposed changes**:
  * Define `[bin.openshell]` pinning `NVIDIA/OpenShell` `v0.1.9` with `external_type = "archive-file"`, `executable = true`, `path_format = "openshell"`, and `filename_format = "openshell-{target}.tar.gz"` (so `src/chezmoi/dot_local/bin/.chezmoiexternals/bins.toml.tmpl` dispatches it automatically with no new `.chezmoiexternals` file needed).
  * Pin verified `v0.1.9` assets and SHA256s: `openshell-x86_64-unknown-linux-musl.tar.gz` (`3856ac7b6b2e33d6c8ab72a1036444156516e7303da85a9b13f661a2aa63bd2d`), `openshell-aarch64-unknown-linux-musl.tar.gz` (`cb923d08703b966f7e0e6b1483ed4ba6ed77bc10812c5502bcc1fb6ee0f6ad59`), and `openshell-aarch64-apple-darwin.tar.gz` (`355bf612159eaa0c5375facd8f27536d9cb54e5af030328ea839a927a7901da5`).
  * Register `openshell = "10d"` under `[bin_updates.tools]` in `src/chezmoi/.chezmoidata/bin-updates.toml` so `bin_updater` enforces a 10-day release cooldown before opening update PRs, and remove `sbx = "5d"` in Phase 2.

#### 3. `src/chezmoi/.chezmoidata/ai/command_policy/openshell.toml`, `sbx.toml`, `src/chezmoi/dot_claude/modify_settings.json`, & `src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json` (Create / Modify)

* **Type / scope**: AI tool command approval policy and renderers.
* **Proposed changes**:
  * Create `openshell.toml` under `[ai.command_policy.host_commands.openshell]` granting `"allow"` for `openshell --help`, `openshell --version`, `openshell help`, `openshell status`, `openshell doctor`, `openshell logs`, `openshell gateway list`, `openshell gateway info`, `openshell sandbox list`, `openshell sandbox get`, `openshell sandbox ssh-config`, `openshell provider list`, `openshell profile list`, `openshell profile describe`, `openshell profile export`, `openshell profile lint`, `openshell policy get`, `openshell rule get`, and `openshell forward list`.
  * Map mutating/exec/secret-adjacent subcommands to `"prompt"` (`openshell sandbox create`, `openshell sandbox exec`, `openshell sandbox connect`, `openshell sandbox start`, `openshell sandbox stop`, `openshell sandbox delete`, `openshell gateway add`, `openshell gateway remove`, `openshell gateway select`, `openshell gateway login`, `openshell gateway logout`, `openshell gateway start`, `openshell gateway stop`, `openshell gateway destroy`, `openshell provider create`, `openshell provider update`, `openshell provider delete`, `openshell provider refresh`, `openshell profile import`, `openshell policy set`, `openshell policy update`, `openshell rule approve`, `openshell rule reject`, `openshell forward start`, `openshell forward stop`) and omit all other subcommands (`"ask"` fallback).
  * Update both `modify_settings.json` renderers to iterate `dig "ai" "command_policy" "host_commands" (dict) .` and merge entries for `$feature` only when `ne (dig "local" "bin" $feature "installation_method" "none" $) "none"`, before merging `[ai.command_policy.commands]`.
  * In Phase 2, move `sbx` grants into `[ai.command_policy.retired_commands]` so `modify_settings.json` strips stale permissions.

#### 4. `src/chezmoi/.chezmoitemplates/shell/openshell.sh`, `src/chezmoi/dot_dotfiles/bash/config.bash.tmpl`, & `src/chezmoi/dot_dotfiles/zsh/config.zsh.tmpl` (Create / Modify)

* **Type / scope**: Shell completions and environment setup.
* **Proposed changes**:
  * Add `openshell.sh` gated on `ne (dig "local" "bin" "openshell" "installation_method" "none" .) "none"` to load `openshell` completions (using the verified `v0.1.9` `openshell completions` subcommand syntax) when on `PATH`.
  * Wire `openshell.sh` into bash and zsh config templates, and remove `shell/sbx.sh` includes in Phase 2.

#### 5. `src/chezmoi/dot_local/bin/executable_openshell-doctor.tmpl` (Create)

* **Type / scope**: Host Gateway and provider diagnostics.
* **Proposed changes**:
  * Create `openshell-doctor.tmpl` gated on `ne (dig "local" "bin" "openshell" "installation_method" "none" .) "none"` to verify Docker daemon availability, `openshell gateway info` / `openshell status`, `loginctl enable-linger` status on Linux (when rootless Docker is used), and `openshell provider` placeholder substitution without printing secrets, returning non-zero on failure.

#### 6. `src/chezmoi/dot_config/ai-policy/git/sandbox.gitconfig.tmpl` (Modify)

* **Type / scope**: Sandbox gitconfig and SSH signing overrides.
* **Proposed changes**:
  * Update `sandbox.gitconfig.tmpl` to set `gpg.format = ssh`, `gpg.ssh.program = ssh-keygen`, empty `gpg.ssh.defaultKeyCommand =`, and `user.signingkey` from `dig "ai" "sandbox" "signing_key" "" .` (enabling `commit.gpgsign = true` and `tag.gpgSign = true` when set, and falling back to `false` when empty).
  * Remove stale `sandboxr` comments.

#### 7. Standalone `/sandbox` builder & pilot policy (`docker/openshell/Dockerfile`, `docker/openshell/sandbox-chezmoi.toml`, `.openshell/policy.yaml`) (Create)

* **Type / scope**: Standalone `/sandbox` OCI builder layer and Phase 1 pilot policy.
* **Proposed changes**:
  * Create `docker/openshell/sandbox-chezmoi.toml` with `[scriptEnv]` (`MISE_CONFIG_DIR`, `MISE_DATA_DIR`, `MISE_STATE_DIR` under `/sandbox`), `[data.zsh] set_as_default_login_shell = false`, `[data.claude_code] installation_method = "direct_release"`, `[data.local.bin.*]` (`"github_releases"` for `codex`, `agy` with `auto_update = false`, `mise`, `gh`, `ripgrep`, `fd`, `jq`, `bat`, `delta`, `fzf`, `nvim`, `shellcheck`, `starship`, `zoxide`, `eza`, `btop`, `bkt`, `pi`), `[data.ai.plugins.{superpowers,egm}] installation_method = "chezmoi_external"`, `[data.ai.plugin_bridge] default_hosts = ["claude", "codex"]`, `[data.git.personal] enabled = true`, `[data.git_hooks] backend = "config"` + `[data.git_hooks.pre_commit] installation_method = "none"`, `[data.gemini.general] enable_auto_update = false`, `[data.codex.telemetry] enabled = false`, and `[data.ai.sandbox] signing_key = "/sandbox/.agent-signing/id_ed25519"`.
  * Create `docker/openshell/Dockerfile` (`FROM debian:bookworm-slim` with `zsh` and `tmux` installed, `ARG SANDBOX_UID=1000`, `ARG SANDBOX_GID=1000`, `ENV HOME=/sandbox PATH="/sandbox/.local/bin:${PATH}"`) running `chezmoi apply --config /tmp/sandbox-chezmoi.toml --destination /sandbox` (which drives `plugin_bridge.py reconcile` via `run_after_agent-plugin-bridge.sh.tmpl`) and `chown -R ${SANDBOX_UID}:${SANDBOX_GID} /sandbox`, excluding `~/.claude.json`, `[projects.*]`, and `trustedWorkspaces`.
  * Create a contributor-portable `.openshell/policy.yaml` with Landlock `read_write` on `/sandbox/workspace`, `/tmp`, and `/sandbox/.{claude,codex,gemini}`, seccomp, and default-deny OPA `network_policies`.

#### 8. `src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/` (Modify / Create / Delete in Phase 2)

* **Type / scope**: Agent workflow skills.
* **Proposed changes**:
  * Decouple `exact_repo-bootstrap/SKILL.md` and `exact_worker-handoff/SKILL.md` from `sbx` CLI specifics.
  * Add `exact_openshell-sandboxes/SKILL.md` covering `policy.yaml`, isolated clone setup, `gh` provider push, and `openshell` inspection.
  * Delete `exact_sbx-sandboxes/` and `exact_sbx-orchestrator/` in Phase 2.

#### 9. Host bootstrap docs & `sbx` retirement cleanup (`docs/openshell-bootstrap.md`, `src/chezmoi/AGENTS.md`, `.github/workflows/ci.yml`, `tests/integration/`) (Create / Modify / Delete)

* **Type / scope**: Operator documentation, CI, and automated tests.
* **Proposed changes**:
  * Create `docs/openshell-bootstrap.md` documenting `openshell gateway start`, `openshell provider create`, dedicated agent SSH signing key setup, `allowed_signers` / GitHub Signing Key-only registration, and isolated-clone host `git fetch` workflow.
  * Update `src/chezmoi/AGENTS.md` to reference OpenShell instead of `sbx`.
  * Add `tests/integration/test_openshell.py`, `tests/integration/test_openshell_command_policy.py`, and update `tests/integration/test_chezmoi_data.py` to verify `dig` defaults, host-only `openshell` grants, `sbx` retirement, and `sandbox.gitconfig` SSH signing rendering.
  * In Phase 2, delete `src/chezmoi/.chezmoidata/bin/sbx.toml`, `src/chezmoi/.chezmoidata/sbx/settings.toml`, `src/chezmoi/.chezmoiscripts/run_after_setup-sbx-settings.sh.tmpl`, `src/chezmoi/.chezmoiscripts/run_after_04_configure-kvm-group.sh.tmpl`, `src/chezmoi/.chezmoitemplates/shell/sbx.sh`, `.sbx/`, `tests/integration/test_sbx*.py`, and the `Check SBX version` step in `.github/workflows/ci.yml`.

### Verification plan

* **Template and apply idempotency**: Run `chezmoi init` and `chezmoi apply` non-interactively with `CI=true` for `"none"`, `"github_releases"`, and static `--config` `--destination /sandbox`, verifying zero errors on re-apply.
* **Integration and policy tests**: Run `pytest` on `tests/integration/test_openshell.py`, `tests/integration/test_openshell_command_policy.py`, and `tests/integration/test_chezmoi_data.py`.
* **Static analysis and linting**: Run `ruff check .`, `ruff format --check .`, `ty check --python .venv`, and `tests/integration/test_shellcheck.py`.
* **Pilot E2E verification**:
  * Run `openshell gateway start` and `openshell-doctor` on a Linux host with Landlock enabled.
  * Build the `/sandbox` OCI layer and compose it into the pilot image.
  * Launch a sandbox with an isolated clone and dedicated agent SSH signing key.
  * Verify `claude`, `codex`, and `agy` plugins load with zero runtime network fetches.
  * Verify `git commit` signs with the agent SSH key and `gh` / `git push` succeeds via `openshell provider`.
  * Verify zero personal signing keys, `~/.gnupg`, or raw host tokens exist inside the sandbox.
