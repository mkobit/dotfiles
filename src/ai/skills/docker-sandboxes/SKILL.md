---
name: docker-sandboxes
description: Guide for creating, running, and managing isolated Docker Sandboxes (sbx) for autonomous agent execution, multi-repo workspace mounts, kit packaging, network egress policies, and secret management.
---

# Docker sandboxes

Docker Sandboxes (`sbx`) provides isolated execution environments for AI agents and developer workflows using microVM and container boundaries.

## Sandbox lifecycle and execution

Manage sandboxes through explicit CLI subcommands.

### Running an ephemeral or persistent agent

Run an agent directly inside an isolated sandbox with `sbx run` (built-in `codex`, `claude`, `shell`) or with custom kits (authored `agy`).

```bash
# Run built-in Codex or Claude agent session
sbx run codex .
sbx run claude .

# Run autonomous agent with arguments passed after --
sbx run codex . -- -y
sbx run claude . -- --dangerously-skip-permissions

# Run custom Antigravity (agy) sandbox kit
sbx run --kit ~/.local/share/sbx/sandboxes/agy agy .

# Run an interactive shell sandbox
sbx run shell .
```

### Creating persistent sandboxes

Use `sbx create` to prepare an environment before dispatching commands.

```bash
# Create a named persistent sandbox
sbx create --name dev-sandbox claude /path/to/project

# Execute commands inside the running sandbox
sbx exec dev-sandbox cargo test

# List running and stopped sandboxes
sbx ls

# Stop a running sandbox
sbx stop dev-sandbox

# Remove sandboxes after completion
sbx rm dev-sandbox
```

## Cross-repository workflows and workspace mounts

Mount workspaces into the sandbox to enable cross-repo development while preserving host safety.

### Mounting multiple workspaces

Pass additional paths as positional arguments to `sbx run` or `sbx create`.
Use `:ro` suffixes on dependency or reference repositories to prevent unexpected mutations.

```bash
# Mount current directory as primary workspace and reference docs/libraries as read-only
sbx run claude . /path/to/shared-lib:ro /path/to/docs:ro

# Create a named sandbox with multiple workspace paths
sbx create --name multi-repo-box gemini ./app ../core-lib:ro
```

### Private git clone mode

Use `--clone` during sandbox creation to run the agent on an in-container clone of the host Git repository.
The host repository is mounted read-only and wired back via a host git remote (`sandbox-<name>`).

```bash
# Run agent on a private in-container clone of the current repository
sbx run --clone claude .

# Create a clone-mode sandbox with custom name
sbx create --clone --name review-box claude .
```

## Applying and packaging kits

Kits provide declarative, shareable bundles (`spec.yaml`) defining environment setup, network policies, and credentials.

### Applying kits to sandboxes

Pass a kit directory, archive, or git repository to `sbx run` or `sbx create` using `--kit`.
Stack multiple mixins onto any sandbox run:

```bash
# Apply a standalone sandbox kit
sbx run --kit ~/.local/share/sbx/sandboxes/agy agy .

# Apply a mixin kit for developer tooling (mise)
sbx run --kit ~/.local/share/sbx/mixins/mise claude .

# Stack multiple mixins (mise dev toolchain + git identity) onto a sandbox
sbx run --kit ~/.local/share/sbx/mixins/mise --kit ~/.local/share/sbx/mixins/git-config claude .
```

### Inspecting and packaging kits

Validate and package custom kits before deployment.

```bash
# Inspect kit metadata and manifest
sbx kit inspect ./kits/rust-dev

# Validate kit structure and declarations
sbx kit validate ./kits/rust-dev

# Package kit into a distributable archive
sbx kit pack ./kits/rust-dev -o ./dist/rust-dev.kit.tar.gz
```

## Secrets management and credential proxy

Inject secrets into sandboxes without baking credentials into container layers or history.

### Managing stored secrets

Store and manage sensitive tokens via `sbx secret`.

```bash
# Set a secret in the sbx secret store
sbx secret set GITHUB_TOKEN

# List configured secrets
sbx secret ls
```

### Passing secrets and using credential proxying

Inject configured secrets into running sandboxes.
The host credential proxy handles upstream authentication without leaking root credentials to the sandbox.

```bash
# Run sandbox with specific secrets exposed to the container environment
sbx run --secret GITHUB_TOKEN --secret NPM_TOKEN node:20 npm publish --dry-run
```

## Network governance and egress policies

Enforce network access controls on agent containers to prevent unauthorized outbound traffic or data leakage.

### Inspecting and checking policies

List and verify network governance policies.

```bash
# List active network policies
sbx policy ls

# Check policy enforcement and compliance
sbx policy check
```

### Restricting egress destinations

Apply explicit network restriction flags to prevent external network access or permit only allowed domains.

```bash
# Run with egress restricted to allowed hosts
sbx run --policy restricted-egress node:20 npm test
```

## Diagnostics and verification

Verify system prerequisites, virtualization status, and daemon connectivity before launching sandboxes.

```bash
# Run diagnostic checks on Docker Sandboxes installation and daemon
sbx diagnose

# Check sbx CLI and daemon version
sbx version
```
