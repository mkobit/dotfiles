---
name: sbx-sandboxes
description: Use when executing coding tasks, inspecting or debugging SBX sandboxes, or configuring repository-owned `.sbx/` environments with the `sbx` CLI. Use only `sbx` for sandbox operations; never the `docker` CLI.
allowed-tools:
  - Bash(sbx --help)
  - Bash(sbx help)
  - Bash(sbx help *)
  - Bash(sbx * --help)
  - Bash(sbx ls)
  - Bash(sbx ls *)
  - Bash(sbx list)
  - Bash(sbx list *)
  - Bash(sbx version)
  - Bash(sbx --version)
  - Bash(sbx diagnose)
  - Bash(sbx diagnose --format json)
  - Bash(sbx diagnose --format yaml)
  - Bash(sbx kit validate *)
  - Bash(sbx env plan *)
  - Bash(sbx env exec * -- *)
  - Bash(sbx exec *)
---

# SBX sandboxes

Use only `sbx` to execute, inspect, or debug SBX sandboxes.
Docker makes the software; the `docker` CLI cannot manage these sandboxes.
For denied sockets or login-service errors, follow platform escalation and inspect the retry before diagnosing authentication.
Use `sbx diagnose` with the required platform access, never `docker ps`, `docker exec`, or Docker daemon commands.

Keep host credentials, Git review, commits, signing, and pushes on the host.
Each repository owns its complete kit, toolchain, services, and environment configuration.
Use `workspace.clone: false` so sandbox edits are immediately visible to the host.
For a private clone and its change-return process, read [Nested execution](references/nested-execution.md).

## Execute a task

For an existing environment with unchanged configuration, execute the task directly.
“Do this task in SBX” authorizes file edits and required checks within that task's scope.
Do not require Beads; use the task supplied by the user or coordinator.

1. Supply the task, file ownership, acceptance criteria, required checks, and log location.
2. Run the command or coding agent through `sbx env exec` or `sbx exec`.
3. Review the diff, exit status, and check results on the host.
4. Report the result and log location; update a task tracker only when the workflow uses one.

Run required checks once; repeat after relevant changes or failures.
Validate, create, or rebuild only when configuration changed or the environment is missing.

## Read when needed

- [CLI selection](references/cli-automation.md): select commands, output formats, and environment paths.
- [Authentication](references/authentication.md): misleading login-service errors, access restrictions, expired sessions, and verification codes.
- [Permissions](references/permissions.md): standard skill grants, tool support, and execution scope.
- [Agents](references/agents.md): validated Codex execution and AGY setup.
- [Subagent task](references/subagent-task.md): a reusable specification for a bounded edit, test, and fix loop.
- [Repository setup](references/repository-setup.md): create a repository-owned kit and environment.
- [Environment files](references/environment-files.md): workspace boundaries and dynamic host ports.
- [Upstream pins](references/upstream-pins.md): the reviewed AGY kit revision.
