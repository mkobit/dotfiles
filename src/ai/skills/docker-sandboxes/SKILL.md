---
name: docker-sandboxes
description: Use when setting up, delegating work into, or troubleshooting Docker Sandboxes (`sbx`) for a Git repository.
---

# Docker Sandboxes

`sbx` runs a repository workload in an isolated Docker Sandbox microVM.

The host agent coordinates work and keeps host credentials, Git review, commits, signing, and pushes on the host.

Each consuming repository owns its complete `.sbx/` configuration, including the kit, runtime, toolchain, packages, ports, and services.

## Default workflow

Use `workspace.clone: false` for the normal delegation workflow.

This direct-mounted workspace makes sandbox edits immediately visible to the host checkout.

Use a private clone only as an explicit alternative when the repository needs in-VM Git isolation and an intentional change-return process.

1. Inspect the repository `AGENTS.md`, `.sbx/`, toolchain files, and required checks.
2. Validate and plan with `sbx kit validate .sbx/kit` and `sbx env plan .sbx/sbxenv.yaml`.
3. Create the environment with `sbx env create .sbx/sbxenv.yaml`.
4. Delegate commands with `sbx env exec .sbx/sbxenv.yaml -- <command>` or an agent session with `sbx env run .sbx/sbxenv.yaml`.
5. Review the direct-mounted changes and run host checks.
6. Commit, sign, and push from the host when authorized.
7. Optionally remove the environment with `sbx env rm .sbx/sbxenv.yaml --force`.

## References

- [Repository setup](references/repository-setup.md) describes a repository-owned `./kit` and environment file.
- [Environment files](references/environment-files.md) covers workspace and lifecycle choices.
- [Nested execution](references/nested-execution.md) covers coordinator-to-sandbox delegation.
- [Agents](references/agents.md) covers Codex, Claude, and AGY harnesses.
- [Upstream pins](references/upstream-pins.md) records the AGY kit pin.
