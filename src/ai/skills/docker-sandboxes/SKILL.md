---
name: docker-sandboxes
description: Use when setting up, running, or troubleshooting Docker Sandboxes (`sbx`) for a Git repository, including isolated Codex or AGY work.
---

# Docker Sandboxes

Use this skill when setting up, running, delegating tasks into, or troubleshooting Docker Sandboxes (`sbx`) for a repository.

## Sandbox mechanics and architecture

The host agent acts as the root coordinator holding host credentials to manage branches, quality gates, and delivery.
Docker Sandboxes run inside an isolated microVM container managed by the host `sandboxd` daemon.
Host credentials, SSH keys, forge tokens, and host configurations never enter the microVM.
Tracked project environments use `clone: true` so the agent works inside an isolated in-VM clone at `/workspace`.
Host checkouts are never mounted writable for autonomous work.
Every repository must be entirely self-bootable from its own tracked `.sbx/` configuration without requiring external host dotfiles or overlays.

## Kit authoring rules

Every project environment provides its own kit at `.sbx/kit/spec.yaml`.
1. Use `schemaVersion: "2"` with `kind: mixin`.
2. Declare explicit egress domains in `permissions.network.allow` for every tool and package download destination (`mise.run`, `mise.jdx.dev`, `github.com`, registries).
3. Bootstrap `mise` into `/usr/local/bin/mise` in `setup.install`.
4. Append `/home/agent/.local/share/mise/shims:/home/agent/.local/bin` to both `/etc/profile.d/mise.sh` and `/etc/sandbox-persistent.sh` so tool shims persist across non-login `sbx env exec` commands.
5. Install project runtimes matching `mise.toml` via `mise use -g <tool>@<version>` as `user: "1000"`.
6. Validate kits locally with `sbx kit validate .sbx/kit`.

## Execution and state retrieval

1. Run `sbx version`; this workflow was last validated against `0.45.1`.
2. Inspect the repository's `AGENTS.md`, `.agents/skills`, `mise.toml`, CI workflows, build manifests, and `.sbx/` configuration.
3. State the selected agent, clone-mode workspace, and required checks before creating a sandbox; require user confirmation for actions outside session authorization.
4. Validate and plan the environment with `sbx kit validate .sbx/kit` and `sbx env plan .sbx/sbxenv.yaml`.
5. Dispatch tasks into the sandbox using `sbx env exec .sbx/sbxenv.yaml -- <command>`.
6. For interactive or autonomous agent sessions, run `sbx env run .sbx/sbxenv.yaml`.
7. Retrieve committed clone-mode work on the host by fetching the sandbox git remote: `git fetch sandbox-<name> <branch>`.
8. Review changes on the host, run host verification gates, and commit or push with host credentials.
9. Tear down environments when finished with `sbx env rm .sbx/sbxenv.yaml --force`.

For detailed references:
- [Repository setup](references/repository-setup.md) covers `.sbx/sbxenv.yaml` and `.sbx/kit/spec.yaml` creation.
- [Environment files](references/environment-files.md) covers schema, variables, and merge semantics.
- [Nested execution](references/nested-execution.md) covers workload dispatch and git remote retrieval.
- [Agents](references/agents.md) covers agent-specific considerations (Codex, AGY).
- [Optional host overlays](references/optional-host-overlays.md) covers personal dotfile overlays when explicitly requested.

