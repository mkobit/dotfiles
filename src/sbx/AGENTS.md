# Docker Sandboxes (sbx)

Docker Sandboxes (`sbx`) provides microVM-isolated execution environments for AI coding agents.
It replaces host-level sandboxing tools like `sandboxr` / `bwrap` with container and virtualization boundaries.

## Architecture overview

Docker Sandboxes isolates agent runs inside microVMs managed by Docker Desktop or `sandboxd`.

### MicroVM isolation boundary

Every sandbox runs inside a dedicated microVM instance with separate Linux namespaces, cgroups, and filesystem virtualization.
The guest agent cannot access host devices, host processes, or unmounted host filesystem paths.
CPU and memory limits are enforced at the virtualization boundary (`--cpus`, `--memory`).

### Host credential proxy and sentinel injection

Zero raw credentials exist inside the guest sandbox environment.
API keys and authentication tokens are held on the host machine by `sandboxd` and managed via `sbx secret`.
The host proxy intercepts guest requests and injects actual credentials dynamically at runtime.
Sandboxes receive sentinel token strings that only the host proxy recognizes and resolves.
Exfiltration of in-sandbox environment variables or files yields inert sentinel values rather than actual secrets.

### Network governance profiles

Egress network traffic is gated through policy profiles and explicit allow/deny rules (`sbx policy`).
Global and per-sandbox policies restrict network access to approved endpoints and services.
Local deny rules (`--deny-network`) can only narrow sandbox egress, preventing unauthorized data exfiltration.

## Agent execution modes

Sandboxes support both attended and unattended agent workflows across supported tools (`claude`, `codex`, `copilot`, `cursor`, `docker-agent`, `droid`, `gemini`, `kiro`, `opencode`, `shell`).

### Attended (HITL)

Interactive sessions permit human approval for sensitive commands within the sandbox.
Run the agent directly via `sbx run <agent> [path]`.
Interactive prompts and terminal UI render normally inside the attached session.

### Autonomous

Unattended execution disables approval prompts within the sandbox while relying on the microVM boundary for safety.
Pass tool-specific bypass flags following the `--` separator:
- Claude Code: `sbx run claude -- --dangerously-skip-permissions`
- Antigravity / Gemini: `sbx run gemini -- --mode=accept-edits`
- OpenCode: `sbx run opencode -- --dangerously-skip-permissions`

## Kit architecture

Kits are declarative YAML packages (`spec.yaml`) that configure sandbox capabilities, dependencies, and environment state.
Kit packages contain a `spec.yaml` manifest and an optional `files/` directory containing overlay assets.

### Sandboxes vs mixins (`kind`)

Docker Sandboxes distinguishes between two fundamental kit kinds:

- **`kind: sandbox` (Base environment)**
  Defines a standalone agent microVM environment.
  Specifies the container image (`sandbox.image`), agent entrypoint (`sandbox.entrypoint`), and default invocation command (`sandbox.command.default`).
  Only one base sandbox definition can be used when launching or creating a sandbox instance.
  Authored sandbox kits live under `src/sbx/sandboxes/<name>/`.

- **`kind: mixin` (Capability overlay)**
  Defines a reusable, composable add-on that can attach to *any* base sandbox or agent.
  Does not define a container image or base entrypoint.
  Injects environment variables (`environment.variables`), setup commands (`setup.install` run once at creation, `setup.startup` run on every boot), network egress rules (`permissions.network.allow`), required host credentials (`credentials`), and filesystem assets (`files/`).
  Multiple mixins can be composed and stacked onto a single sandbox run via repeated `--kit` flags:
  ```bash
  sbx run --kit ./src/sbx/mixins/mise --kit ./src/sbx/mixins/ollama-dev claude .
  ```
  Authored mixin kits live under `src/sbx/mixins/<name>/`.

### Repository layout and external kits

- `src/sbx/sandboxes/`: authored standalone sandbox kits (e.g. `agy`).
- `src/sbx/mixins/`: authored capability mixins (e.g. `mise` dev toolchain, `ollama-dev` local LLM bridge, `chezmoi-init` dotfiles bootstrap).
- `.chezmoidata/sbx/kits.toml`: catalog of pinned upstream external kits (e.g. `shelajev/agy-sbx-kit`).
- `.chezmoiexternals/sbx-kits.toml.tmpl`: manages downloading and deploying pinned external kits to `~/.local/share/sbx/`.
- `tests/integration/test_sbx_kits.py`: automated pytest suite validating kit YAML schemas and executing `sbx kit validate` across all kits in CI.

### Manifest schema (spec.yaml)

Kits use `schemaVersion: "2"` with modular configuration blocks:
- `kind`: defines whether the artifact is a `sandbox` specification or a reusable `mixin`.
- `setup`: declares setup commands (`install` for creation-time, `startup` for boot-time).
- `permissions`: configures network egress allowlists and tool constraints.
- `credentials`: declares required service secrets resolved dynamically via the host proxy.
- `environment`: sets environment variables in the guest sandbox.
- `files/`: bundles local configuration files and scripts copied into the sandbox root filesystem.

### Packaging and validation

Kits can be distributed as local directories, ZIP archives, or OCI registry artifacts.
- Validate kit structure: `sbx kit validate <path>`
- Package kit into archive: `sbx kit pack <path> -o <name>.zip`
- Publish to registry: `sbx kit push <image> <path>`
- Attach kit to run: `sbx run --kit <ref> <agent>`

## Multi-repo workflows

Sandboxes support mounting multiple independent repositories and directories.

### Multiple workspace mounts

Pass additional paths as positional arguments to `sbx run` or `sbx create`.
Additional workspaces are attached inside the sandbox alongside the primary working directory:
```bash
sbx run claude /path/to/primary /path/to/secondary
```

### Read-only mounts

Append `:ro` to any workspace path to enforce read-only access:
```bash
sbx run claude . /path/to/reference-repo:ro /path/to/docs:ro
```
Read-only workspaces protect shared libraries and documentation from unintended modifications.

### Private in-container clone (--clone)

Use `--clone` during sandbox creation to create a private working clone inside the container:
```bash
sbx run --clone claude .
```
The sandbox clones the host Git repository into isolated container storage with the host repo set as the remote.
Host working copy files remain untouched while the agent runs, branches, and tests in container-local storage.

## SSH, GPG, and Git commit signing policy

Key isolation is a primary security boundary for AI agent sandboxes.

### Private key isolation

Raw private keys (`~/.ssh/id_*`, `~/.gnupg/private-keys-v1.d`) must never be copied into or mounted inside the sandbox microVM.
Sandboxes run untrusted agent code that could exfiltrate or corrupt static private key material.

### Commit signing strategies

1. **Default: unsigned sandbox commits (`commit.gpgsign = false`)**
   The [`src/sbx/mixins/git-config`](mixins/git-config/) mixin sets `commit.gpgsign = false` by default.
   Unsigned commits distinguish agent-generated history from human-verified commits.
   The human reviews, merges, and signs the resulting branch or PR on the host machine.

2. **Host-side signing via `--clone` Git Daemon mode**
   When creating sandboxes with `sbx run --clone claude .`, the agent commits to its in-container clone.
   The host pulls commits via the host remote (`sandbox-<name>`).
   The human signs merge or squash commits on the host using their host GPG or SSH signing key.

3. **SSH agent forwarding for in-sandbox signing**
   When in-sandbox signing is required, Git uses SSH signing format (`gpg.format = ssh`).
   Signing requests flow through the forwarded SSH agent socket (`SSH_AUTH_SOCK`).
   The private key remains on the host's `ssh-agent`; the guest only sends signing payloads over the socket.

## Living documentation links

Reference the upstream documentation and repositories for official specifications and releases.

### Upstream documentation

- Root CLI reference: [Docker Sandboxes CLI](https://docs.docker.com/reference/cli/sbx/)
- Run command: [sbx run reference](https://docs.docker.com/reference/cli/sbx/run/)
- Create command: [sbx create reference](https://docs.docker.com/reference/cli/sbx/create/)
- Kit management: [sbx kit reference](https://docs.docker.com/reference/cli/sbx/kit/)
- Policy management: [sbx policy reference](https://docs.docker.com/reference/cli/sbx/policy/)
- MCP management: [sbx mcp reference](https://docs.docker.com/reference/cli/sbx/mcp/)
- Template management: [sbx template reference](https://docs.docker.com/reference/cli/sbx/template/)
- Secret management: [sbx secret reference](https://docs.docker.com/reference/cli/sbx/secret/)
- Setup command: [sbx setup reference](https://docs.docker.com/reference/cli/sbx/setup/)
- Skills management: [sbx skills reference](https://docs.docker.com/reference/cli/sbx/skills/)
- Daemon management: [sbx daemon reference](https://docs.docker.com/reference/cli/sbx/daemon/)
- Autocompletion: [sbx completion reference](https://docs.docker.com/reference/cli/sbx/completion/)

### Upstream repositories and community kits

- Release repository: [docker/sbx-releases](https://github.com/docker/sbx-releases)
- Community AGY kit: [shelajev/agy-sbx-kit](https://github.com/shelajev/agy-sbx-kit)

## Agent discovery strategy

Inspect CLI capabilities directly when exploring new `sbx` versions or unreleased flags.

1. Probe top-level commands:
   ```bash
   sbx --help
   ```
2. Probe subcommand trees:
   ```bash
   sbx <command> --help
   ```
3. Probe nested commands:
   ```bash
   sbx kit --help
   sbx policy --help
   sbx secret --help
   ```
4. Diagnose host runtime and connectivity:
   ```bash
   sbx diagnose
   sbx daemon status
   ```
