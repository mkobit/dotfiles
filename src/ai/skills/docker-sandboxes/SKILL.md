---
name: docker-sandboxes
description: Use when configuring a repository-owned `.sbx/` environment or kit, or when coordinating host builds, tests, and delegated agents through `sbx env`.
allowed-tools:
  - Bash(sbx ls --format json)
  - Bash(sbx kit validate .sbx/kit)
  - Bash(sbx env plan .sbx/sbxenv.yaml)
  - Bash(sbx env exec .sbx/sbxenv.yaml -- *)
---

# Docker Sandboxes

Use this skill to configure a repository-owned `.sbx/` environment and kit.

The host agent coordinates builds, tests, and delegated agents through `sbx env`.

Keep host credentials, Git review, commits, signing, and pushes on the host.
Each repository owns its `.sbx/` configuration, including its kit, runtime, toolchain, packages, ports, and services.

## Default workflow

Use `workspace.clone: false` for the normal delegation workflow.

This direct-mounted workspace makes sandbox edits immediately visible to the host checkout.

Use a private clone when the repository needs in-VM Git isolation and a defined change-return process.

1. Inspect the repository `AGENTS.md`, `.sbx/`, toolchain files, required checks, and `sbx ls --format json` output.
2. Reuse a matching existing environment when one is available.
3. If configuration changed or a new environment is needed, run `sbx kit validate .sbx/kit` and `sbx env plan .sbx/sbxenv.yaml`.
4. Create with `sbx env create .sbx/sbxenv.yaml` only when needed and authorized.
5. Run related checks with `sbx env exec .sbx/sbxenv.yaml -- <command>` and keep each failed exit code visible.
6. Review direct-mounted changes, report sandbox and host checks separately, and deliver Git changes from the host when authorized.
7. Remove an environment with `sbx env rm .sbx/sbxenv.yaml --force` only when authorized.

Read [Permissions](references/permissions.md) before requesting an escalated command or configuring command grants.
Read [CLI automation](references/cli-automation.md) for v0.48 command behavior.

## References

- [Repository setup](references/repository-setup.md) describes a repository-owned `./kit` and environment file.
- [Environment files](references/environment-files.md) covers workspace and lifecycle choices.
- [Nested execution](references/nested-execution.md) covers coordinator-to-sandbox delegation.
- [Agents](references/agents.md) covers Codex, Claude, and AGY harnesses.
- [Upstream pins](references/upstream-pins.md) records the AGY kit pin.
- [CLI automation](references/cli-automation.md) covers machine-readable output, prompts, and lifecycle behavior.
