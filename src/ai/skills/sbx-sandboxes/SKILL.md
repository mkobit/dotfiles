---
name: sbx-sandboxes
description: >-
  Use when inspecting or debugging SBX sandboxes or configuring repository-owned `.sbx/` environments with the `sbx` CLI.
  Route delegated coding execution to sbx-orchestrator.
  Use only `sbx` for sandbox operations; never the `docker` CLI.
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

On the host, use only `sbx` to execute, inspect, or debug SBX sandboxes.
Inside an assigned SBX workspace, run repository commands directly.
A missing guest `sbx` executable does not require nested SBX or host checks.
Docker makes the software; the `docker` CLI cannot manage these sandboxes.
For denied sockets or login-service errors, follow platform escalation and inspect the retry before diagnosing authentication.
Use `sbx diagnose` with the required platform access, never `docker ps`, `docker exec`, or Docker daemon commands.

Keep host credentials, Git review, commits, signing, and pushes on the host.
Each repository owns its complete kit, toolchain, services, and environment configuration.
Use `workspace.clone: false` so sandbox edits are immediately visible to the host.
Use the [workspace contract](../sbx-orchestrator/references/nested-execution.md#workspace-ownership) for worktrees and isolated locked dependencies.
Separate sandbox container status (`sbx list`) from agent binary lookup failures and command exit codes.
For a restart or lost client, follow [recovery](../sbx-orchestrator/references/recovery.md) before resume or replacement.
For a private clone and its change-return process, use [SBX orchestrator](../sbx-orchestrator/SKILL.md).

## Select the work

Use [SBX orchestrator](../sbx-orchestrator/SKILL.md) for delegated coding tasks in SBX.
That skill separates the host supervisor contract from the guest task prompt.
It covers worker launch, progress, recovery, and handoff.

Use direct SBX commands for probes, setup, and explicit command-only requests.
Do not replace a command-only request with a coding worker.
Validate, create, or rebuild only when configuration changed or the environment is missing.
Use existing task authority for needed worktree and environment setup.
Ask only for missing authority, actual platform permission, unavailable credential action, scope expansion, or a destructive unrelated change.

## Read when needed

- [CLI selection](references/cli-automation.md): select commands, output formats, and environment paths.
- [Authentication](references/authentication.md): misleading login-service errors, access restrictions, expired sessions, and verification codes.
- [Permissions](references/permissions.md): standard skill grants, tool support, and execution scope.
- [Agents](references/agents.md): repository harness selection and AGY setup.
- [Repository setup](references/repository-setup.md): create a repository-owned kit and environment.
- [Environment files](references/environment-files.md): workspace boundaries and dynamic host ports.
- [Upstream pins](references/upstream-pins.md): the reviewed AGY kit revision.
