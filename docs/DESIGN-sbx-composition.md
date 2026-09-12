# Sandbox composition

Status: proposal, with the personal guidelines and skill snapshot implemented in [PR #855](https://github.com/mkobit/dotfiles/pull/855).

Every project should build independently, while personal behavior follows the user into each sandbox.
Existing configuration is evidence to evaluate, not a settled architecture.

## Ownership

| Layer | Owns | Source |
| --- | --- | --- |
| Project | Build tools and versions, system dependencies, checks, services, project instructions and required plugins | Repository environment and kit |
| Personal | Shared guidelines, selected skills, optional personal plugins and productivity tools | Catalogs and authored sources in this dotfiles repository |
| Agent integration | Skill discovery, plugin registration and supported configuration for the selected agent | Agent-specific integration tested inside SBX |

Ownership follows necessity: anything required to build or verify a project belongs to the project, even if the user also installs it globally.
Reusable installation mechanics can be shared through pinned kits without moving project version decisions into personal dotfiles.
A project must remain usable without the personal layer.

## Composition

Use the project environment first and the generated personal environment second for every lifecycle command.
For example:

```sh
sbx env run .sbx/sbxenv.yaml ~/.local/share/sbx/personal/personal.sbxenv.yaml
```

Use the same environment paths for planning, creating, executing in, and removing that environment.
Explicit environment paths do not implicitly load the user's default environment file.
Later scalar values override earlier values, so the personal layer must avoid overriding project identity, workspace, agent choice, or tool versions.
See the [SBX environment composition reference](https://docs.docker.com/ai/sandboxes/configuration/environment-files/).

The generated personal kit is a creation-time snapshot, rebuilt by `chezmoi apply` and consumed when a sandbox is created or recreated.
It is not a live mount of host configuration.
The current implementation deliberately disables the native writable shared skill store when using these snapshots.
See [SBX shared skills](https://docs.docker.com/ai/sandboxes/workflows/agent-skills/).

## Implemented and unresolved behavior

The current generator includes shared guidelines and portable skills selected as `present`, including supporting files.
It copies skills to the paths used for Codex, Claude, and AGY.
The live smoke check verified copied files and injected instruction context; it did not prove skill invocation in every agent.

The authored `mkobit-dotfiles` plugin manifests currently describe skill bundles.
Extracting their skills supplies that content, but does not register a native plugin or establish support for hooks, MCP servers, agent definitions, or third-party plugins.
Those capabilities need an explicit adapter for each supported agent, including runtime dependencies and an activation check inside the sandbox.
Do not copy host agent configuration wholesale or overwrite SBX-managed configuration to activate them.

Personal tooling is not yet provisioned by the generated kit.
Add guest-compatible tools through kit installation steps, with versions and installation metadata owned here when they are personal preferences.
Do not copy host binaries into guests or assume a skill's supporting executable has all its runtime dependencies installed.
Keep environment lifecycle hooks for host orchestration and guest installation in kits.
See the [SBX kit reference](https://docs.docker.com/ai/sandboxes/customize/kit-reference/).

## Next implementation gates

1. Inventory each repository's current setup, required tools, skills, plugins, and duplicated installation mechanics, citing the actual files.
2. Choose one real plugin and one personal tool from that inventory, then prove installation and use in a disposable sandbox for the intended agent before generalizing.
3. Generate the proven personal capabilities from this repository's catalogs, with explicit selection and deterministic versions.
4. Verify both the standalone project environment and the composed personal environment; recreate after an update and confirm removed capabilities disappear.

The existing Jules sessions should report repository requirements and make bounded SBX compatibility fixes.
They should not independently invent six personal-layer implementations or make project builds depend on this checkout.
Plugin adapters and reusable tooling kits remain centrally coordinated work until these gates are satisfied.
