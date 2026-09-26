# Repository setup

Each repository must be fully self-bootable in `sbx` without depending on external host sources or dotfile overlays.

## Host-to-sandbox delegation workflow

The host session runs beads, git commits, and reviews, while the sandbox container runs builds, linters, tests, and code generation.

When using `workspace.clone: false`, the environment directly mounts the project repository, ensuring file changes are immediately visible to host git and beads.

Sandbox agent harnesses (antigravity, claude, codex) already default to auto-approved permissions inside the isolated microVM (e.g. antigravity's kit defaults to `--dangerously-skip-permissions`), so prompts do not need manual permission flags.

Use the streamlined invocation syntax:
- Antigravity: `sbx env run .sbx/sbxenv.agy.yaml -- -p "<prompt>"`
- Codex: `sbx env run .sbx/sbxenv.yaml -- -q "<prompt>"`
- Claude: `sbx env run .sbx/sbxenv.claude.yaml -- -p "<prompt>"`

## File layout

A self-bootable repository contains:
- `.sbx/sbxenv.yaml`: primary environment configuration (Codex or default agent).
- `.sbx/kit/spec.yaml`: repository toolchain kit mixin provisioning `mise` and runtimes.
- `.sbx/sbxenv.agy.yaml`: optional AGY-specific environment configuration when AGY is supported.

Do not use hidden `.sbx/.sbxenv.yaml` names for new setups; `sbx` directory lookup resolves `sbxenv.yaml`.

## Environment configuration (`.sbx/sbxenv.yaml`)

Create `.sbx/sbxenv.yaml` with:
- `schemaVersion: "1"`
- `name: "<project-slug>-codex"` (lowercase, hyphens only, max 63 characters).
- `agent: codex`
- `workspace:` with `path: ..` and `clone: true`.
- `kits:` including `./kit`.
- `ports:` declaring any necessary port forwards for services or dev servers.

Do not include `additionalWorkspaces`, `bindings`, `registries`, `secrets`, or local command MCP servers in tracked files.

## Kit authoring (`.sbx/kit/spec.yaml`)

The repository kit provides guest environment bootstrapping so tests and tools run cleanly.

```yaml
schemaVersion: "2"
kind: mixin
name: <project-slug>-toolchain
version: "0.1.0"
description: Bootstrap mise and project toolchain for <project-slug>

permissions:
  network:
    allow:
      - mise.run
      - mise.jdx.dev
      - github.com
      - api.github.com
      - "*.githubusercontent.com"
      - registry.npmjs.org
      - bun.sh

environment:
  variables:
    PATH: /home/agent/.local/share/mise/shims:/home/agent/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    MISE_YES: "1"

setup:
  install:
    - command: |
        curl -fsSL https://mise.run | MISE_INSTALL_PATH=/usr/local/bin/mise sh
        printf '%s\n' 'export PATH="/home/agent/.local/share/mise/shims:/home/agent/.local/bin:$PATH"' > /etc/profile.d/mise.sh
        printf '%s\n' 'export PATH="/home/agent/.local/share/mise/shims:/home/agent/.local/bin:$PATH"' >> /etc/sandbox-persistent.sh
      description: "Install mise into /usr/local/bin and configure persistent shell paths"
    - command: "mise settings set paranoid false && mise settings set yes true && mise use -g <tool>@<version>"
      user: "1000"
      description: "Install required project tools matching mise.toml"
```

Key requirements for kit authoring:
1. `permissions.network.allow` must include all hosts queried during install and runtime package resolution.
2. `/etc/sandbox-persistent.sh` must be updated with the shim paths because `sbx env exec` executes non-login shells.
3. Tools installed in `setup.install` must align with `mise.toml` so the sandbox provides identical versions to the host.
4. If native packages are needed (e.g. `build-essential`), install them via `apt-get` in the root install step before `mise`.

## Local validation and execution

1. Validate the kit: `sbx kit validate .sbx/kit`.
2. Inspect the environment plan: `sbx env plan .sbx/sbxenv.yaml`.
3. Provision the sandbox: `sbx env create .sbx/sbxenv.yaml`.
4. Run project checks inside the sandbox: `sbx env exec .sbx/sbxenv.yaml -- mise run check`.
5. Remove the sandbox when finished: `sbx env rm .sbx/sbxenv.yaml --force`.

