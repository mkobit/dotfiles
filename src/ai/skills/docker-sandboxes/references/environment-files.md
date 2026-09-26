# Environment files

Docker environment files are experimental; [SKILL.md](../SKILL.md) records the last-tested SBX version (0.45.1).

Read Docker’s [environment-file reference](https://docs.docker.com/ai/sandboxes/configuration/environment-files/) for file lookup and merge semantics.

## File resolution and naming

`sbx` directory lookup resolves `sbxenv.yaml` (unhidden).
Always name tracked project environments `.sbx/sbxenv.yaml` and `.sbx/sbxenv.agy.yaml`.
Environment files can reference `${{ env.projectDir }}` and `${{ env.fileDir }}` for portable directory references.

## Standalone project environments

Each repository provides a standalone `.sbx/sbxenv.yaml` with its own `./kit` mixin.
Running commands with `sbx env run .sbx/sbxenv.yaml` or `sbx env exec .sbx/sbxenv.yaml -- <cmd>` should work cleanly without requiring personal overlays.
When passing an explicit file path to `sbx env`, `sbx` skips the default `~/.sbxenv.yaml` user file.

## Options and skills

`sbx` v0.43+ replaces `shareSkills: false` with `skills: off|readonly|readwrite`.
Set `sandboxOptions.skills: "off"` (or `"readonly"`) in modern environment configurations.

## Workspace isolation and security

Tracked project files must use `workspace.clone: true` so the agent works in a private in-VM clone and cannot change the host checkout directly.
Keep direct mounts disabled for autonomous work.

However, when using `workspace.clone: false` (such as in `claude.sbxenv.yaml`), the environment directly mounts the project repository, ensuring file changes are immediately visible to host git and beads.
This supports a host-to-sandbox delegation workflow where the host session runs beads, git commits, and reviews, while the sandbox container runs builds, linters, tests, and code generation.

Sandbox agent harnesses (antigravity, claude, codex) already default to auto-approved permissions inside the isolated microVM (e.g. antigravity's kit defaults to `--dangerously-skip-permissions`), so prompts do not need manual permission flags.

Streamlined invocation syntax:
- Antigravity: `sbx env run .sbx/sbxenv.agy.yaml -- -p "<prompt>"`
- Codex: `sbx env run .sbx/sbxenv.yaml -- -q "<prompt>"`
- Claude: `sbx env run .sbx/sbxenv.claude.yaml -- -p "<prompt>"`
Do not commit `secrets`, `bindings`, `registries`, local-command MCP configuration, or writable `additionalWorkspaces`.
These fields can execute host commands, modify host credentials, or expose additional host paths.
Keep machine-specific local settings in an ignored `.sbx/local.sbxenv.yaml` file.

## Lifecycle management

Run `sbx env rm .sbx/sbxenv.yaml --force` and recreate after changing kits, workspace mounts, ports, or environment variables because `sbx env run` does not reprovision those fields on an existing environment.
Resolve toolchain or package updates in-place inside an existing sandbox using `sbx exec <name> -- <command>`, or tear down the environment with `sbx env rm .sbx/sbxenv.yaml --force` for a clean kit rebuild.

