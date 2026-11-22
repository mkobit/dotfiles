---
name: openshell-sandboxes
description: >-
  Use when inspecting, launching, or debugging NVIDIA OpenShell sandboxes or configuring repository-owned `.openshell/policy.yaml` policies with the `openshell` CLI.
  Keep command approvals in central policy; never forward personal host GPG/SSH keys or raw tokens into a sandbox.
---

# OpenShell sandboxes

On the host, use `openshell` and `openshell-doctor` to inspect, verify, or run NVIDIA OpenShell sandboxes.
Inside an assigned OpenShell sandbox (`/sandbox/workspace`), run repository commands directly.
A missing guest `openshell` executable is expected because `openshell` is gated to host installations only.
The central command policy (`[ai.command_policy.host_commands.openshell]`) owns approvals; this skill grants no commands.
Use `openshell help <subcommand>` or `openshell --help` for CLI usage, and run `openshell-doctor` to check Docker daemon readiness, Gateway health, Linux rootless Docker linger state, and redacted `openshell provider` availability.

## Three-layer architecture

1. **Repository layer (contributor-portable)**:
   - Each repository owns `.openshell/policy.yaml` and its base runtime toolchain image.
   - Do not embed personal provider names, personal dotfiles paths, or user-specific secrets in `.openshell/policy.yaml`.
2. **Host Gateway and providers (host only)**:
   - The host runs the Docker-hosted OpenShell Gateway (`openshell gateway start`) and holds credentials in `openshell provider` instances (`github`, `anthropic`, `openai`, `gemini`).
   - Raw credentials stay in `openshell provider` and are proxy-substituted; never store plaintext PATs or API keys in `chezmoi.toml`.
3. **Standalone `/sandbox` OCI layer (dotfiles-owned)**:
   - Built via `docker/openshell/Dockerfile` using `chezmoi apply --config /tmp/sandbox-chezmoi.toml --destination /sandbox`.
   - Composed into repository images via `COPY --from=<dotfiles-sandbox-image> /sandbox /sandbox`.
   - Pre-renders `claude`, `codex`, `agy`, plugins, skills, and `/sandbox/.config/ai-policy/git/sandbox.gitconfig` with zero runtime network fetches inside the sandbox.

## Policy and filesystem boundaries (`.openshell/policy.yaml`)

- **Creation-locked Landlock rules**:
  - `filesystem_policy.read_write` is limited to `/sandbox/workspace`, `/tmp`, `/sandbox/.claude`, `/sandbox/.codex`, and `/sandbox/.gemini`.
  - `filesystem_policy.read_only` covers system paths (`/bin`, `/etc`, `/lib`, `/lib64`, `/sbin`, `/usr`) and pre-built `/sandbox` assets (`/sandbox/.agent-signing`, `/sandbox/.config`, `/sandbox/.dotfiles`, `/sandbox/.local`).
- **Process and seccomp isolation**:
  - Run as unprivileged user/group `1000:1000` with `seccomp.enabled: true`.
  - Keep inner tool sandboxes disabled (`claude_code.settings.sandbox.enabled = false`, `gemini.tools.sandbox = false`) so nested `bwrap` does not conflict with OpenShell seccomp.
- **Default-deny OPA network egress**:
  - Set `network_policies.default_action: deny` and explicitly allow only required HTTPS (`443`) domains (`github.com`, `api.github.com`, and required LLM API endpoints).

## Isolated clones, SSH agent signing, and `gh` push flow

- **Isolated clones in `/sandbox/workspace`**:
  - Always operate on an isolated Git clone inside `/sandbox/workspace` (cloned via the `github` provider or seeded from a host `git bundle`).
  - Never mount a host `.git` directory or linked worktree `read_write` into a sandbox.
- **Dedicated agent SSH commit signing (`gpg.format = ssh`)**:
  - Never forward host `~/.gnupg`, `gpg-agent`, `SSH_AUTH_SOCK`, or personal SSH authentication keys into a sandbox.
  - Mount or upload a dedicated signing-only `ed25519` key at `/sandbox/.agent-signing/id_ed25519` (`read_only`, `0600`), registered in `allowed_signers` and on GitHub as a **Signing Key only** (never an Authentication Key).
  - `GIT_CONFIG_GLOBAL=/sandbox/.config/ai-policy/git/sandbox.gitconfig` configures `gpg.format = ssh`, `gpg.ssh.program = ssh-keygen`, empty `gpg.ssh.defaultKeyCommand =`, and `user.signingkey = /sandbox/.agent-signing/id_ed25519` (or falls back to `commit.gpgsign = false` when no key is configured).
- **Pushing and returning changes to the host**:
  - Inside the sandbox, authenticate HTTPS pushes via `gh auth git-credential` backed by the `openshell provider` fine-grained PAT (**Contents: Read and write**, **Pull requests: Read and write**, **Workflows: No access**).
  - Push to a feature branch (never `main`), then run `git fetch origin <branch>` on the host worktree to inspect signed commits (`git log --show-signature`) before review or merge.

## Inspection and debugging commands

- Read-only host inspection (allowed by command policy):
  - `openshell status`
  - `openshell doctor` and `openshell-doctor`
  - `openshell gateway info` and `openshell gateway list`
  - `openshell sandbox list`, `openshell sandbox get <name>`, and `openshell logs <name>`
  - `openshell provider list`, `openshell policy get`, and `openshell profile list`
- Mutating lifecycle and execution subcommands (`openshell sandbox create`, `openshell sandbox exec`, `openshell sandbox connect`, `openshell sandbox delete`, `openshell gateway start`, `openshell provider create`) require explicit prompt confirmation under central command policy.
