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

On the host, use only `sbx` to execute, inspect, or debug SBX sandboxes.
Inside an assigned SBX workspace, run repository commands directly.
A missing guest `sbx` executable does not require nested SBX or host checks.
Docker makes the software; the `docker` CLI cannot manage these sandboxes.
For denied sockets or login-service errors, follow platform escalation and inspect the retry before diagnosing authentication.
Use `sbx diagnose` with the required platform access, never `docker ps`, `docker exec`, or Docker daemon commands.

Keep host credentials, Git review, commits, signing, and pushes on the host.
Each repository owns its complete kit, toolchain, services, and environment configuration.
Use `workspace.clone: false` so sandbox edits are immediately visible to the host.
Combine `clone: false` with Git worktrees to distribute tasks across parallel sandboxes.
For a private clone and its change-return process, read [Nested execution](references/nested-execution.md).

## Execute a task

For work in SBX, default to a repository-supported AGY, Codex, or other coding harness with one complete bounded prompt.
Let that worker own implementation, checks, repairs, and evidence from start to finish.
The host owns task decomposition, authorization, independent review, integration, and publication.
Use direct SBX commands for probes, setup, and explicit command-only requests, not as a substitute for coding-agent delegation.
Respect explicitly narrower user requests.
For an existing environment with unchanged configuration, launch the worker without repeated setup or discovery.
“Do this task in SBX” authorizes file edits and required checks within that task's scope.
Do not require Beads; use the task supplied by the user or coordinator.

1. Put the task, file ownership, acceptance criteria, required checks, and log location in one complete prompt.
2. From the host, launch the coding harness through `sbx env exec` or `sbx exec`; the guest worker runs its edit, check, and repair loop directly.
3. Review the diff, exit status, and check results on the host.
4. Report the result and log location; the authorized host coordinator updates a task tracker only when the workflow uses one.

Run required checks once; repeat after relevant changes or failures.
Validate, create, or rebuild only when configuration changed or the environment is missing.

## Read when needed

- [CLI selection](references/cli-automation.md): select commands, output formats, and environment paths.
- [Authentication](references/authentication.md): misleading login-service errors, access restrictions, expired sessions, and verification codes.
- [Permissions](references/permissions.md): standard skill grants, tool support, and execution scope.
- [Agents](references/agents.md): host launch, guest context, progress, session recovery, feedback, and AGY setup.
- [Subagent task](references/subagent-task.md): a reusable specification for a bounded edit, test, and fix loop.
- [Repository setup](references/repository-setup.md): create a repository-owned kit and environment.
- [Environment files](references/environment-files.md): workspace boundaries and dynamic host ports.
- [Upstream pins](references/upstream-pins.md): the reviewed AGY kit revision.
