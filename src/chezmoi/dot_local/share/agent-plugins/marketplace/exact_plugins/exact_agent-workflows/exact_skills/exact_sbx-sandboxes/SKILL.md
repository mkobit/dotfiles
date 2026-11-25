---
name: sbx-sandboxes
description: >-
  Use when inspecting or debugging SBX sandboxes or configuring repository-owned `.sbx/` environments with the `sbx` CLI.
  Route delegated coding execution to sbx-orchestrator.
  Use only `sbx` for sandbox operations; never the `docker` CLI.
---

# SBX sandboxes

On the host, use only `sbx` to execute, inspect, or debug SBX sandboxes.
Inside an assigned SBX workspace, run repository commands directly.
A missing guest `sbx` executable does not require nested SBX or host checks.
Docker makes the software; the `docker` CLI cannot manage these sandboxes.
For denied sockets or login-service errors, follow platform escalation and inspect the retry before diagnosing authentication.
Use `sbx diagnose` with the required platform access, never `docker ps`, `docker exec`, or Docker daemon commands.

The central command policy owns approvals; this skill grants no commands.
Use `sbx help <command path>` for CLI help, for example `sbx help env exec`.
Execution-prefix approval rules also match `sbx env exec --help`; the `sbx help` form avoids that prompt without changing execution approval.
For one complete task from a person or an agent, use [repository bootstrap](../repo-bootstrap/SKILL.md).
Record scope, branch and base, checks, authority, and return location before creation or launch.
Keep Git delivery, signing, publishing, and tracker changes on the host for normal edit/check tasks.
An explicit private-clone task can assign these actions to the guest worker.
Use [repository setup](references/repository-setup.md) for that authority and its prerequisites.
Each repository owns its complete kit, toolchain, services, and environment configuration.
Creation must leave the guest ready without manual tool installation, trust, or dependency bootstrap.
Report a setup defect if required tools or dependencies are missing.
Keep `workspace.clone: false` for direct-mounted tasks; use `clone: true` for assigned private-clone work.
Use the [workspace contract](../sbx-orchestrator/references/nested-execution.md#workspace-ownership) for worktrees and isolated locked dependencies.
Separate sandbox container status (`sbx list`) from agent binary lookup failures and command exit codes.
For a restart or lost client, follow [recovery](../sbx-orchestrator/references/recovery.md) before resume or replacement.
Use the [setup reference](references/repository-setup.md#private-git-and-change-return) for private Git and change return.

## Select the work

Use [SBX orchestrator](../sbx-orchestrator/SKILL.md) for delegated coding tasks in SBX.
That skill separates the host supervisor contract from the guest task prompt.
It covers worker launch, progress, recovery, and handoff.
It does not grant delivery, signing, or tracker authority.

Use direct SBX commands for probes, setup, and explicit command-only requests.
Do not replace a command-only request with a coding worker.
Build, create, or rebuild only when configuration changed or the environment is missing.
Use existing task authority for needed worktree and environment setup.
Ask only for missing authority, actual platform permission, unavailable credential action, scope expansion, or a destructive unrelated change.

## Read when needed

- [CLI selection](references/cli-automation.md): select commands, output formats, and environment paths.
- [Authentication](references/authentication.md): misleading login-service errors, access restrictions, expired sessions, and verification codes.
- [Permissions](references/permissions.md): platform access, tool support, and execution scope.
- [Agents](references/agents.md): repository harness selection and AGY setup.
- [Repository setup](references/repository-setup.md): create a repository-owned kit and environment.
- [Environment files](references/environment-files.md): workspace boundaries and dynamic host ports.
- [Upstream pins](references/upstream-pins.md): the reviewed AGY kit revision.
