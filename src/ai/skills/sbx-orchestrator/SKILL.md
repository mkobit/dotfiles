---
name: sbx-orchestrator
description: >-
  Use when coordinating delegated coding tasks in SBX, including worker launch, task prompts, progress, recovery, and handoff.
  Use sbx-sandboxes for lifecycle, configuration, authentication, permissions, and CLI facts.
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
  - Bash(sbx env exec * -- *)
  - Bash(sbx exec *)
---

# SBX orchestrator

Use this skill when the authorized task calls for delegated coding in SBX.
Respect explicit command-only requests and narrower user scope.
Use direct SBX commands for probes and command-only work, not as a substitute for a requested coding worker.

The host coordinator owns task selection, branch management, credentials, review, commits, signing, and publication.
When available, a native host subagent uses host tools to launch a separate guest coding harness.
When no native subagent tool is available, the root coordinator may perform the host supervisor contract directly.
Its tools do not move into the guest.
The guest edits, checks, and repairs the assigned files directly in its workspace.
Task authorization permits this loop without routine nested approval requests.
Reuse that authority for needed task-specific host worktree and environment setup.
Ask only when task authority, actual platform permission, or a required credential action is missing, or when scope must expand.
It does not permit host policy changes or broader task scope.

## Coordinate a task

1. Select or create the feature branch and worktree on the host and confirm one writer per checkout.
2. Save the complete task and baseline in a [durable host record](references/recovery.md) with a discoverable task pointer.
3. Give the supervisor the [host contract](references/host-supervisor.md) and a separate [guest prompt](references/subagent-task.md).
4. Verify the installed guest harness and use the [worker launcher](references/worker-launch.md).
5. Update the record at milestones and use [recovery](references/recovery.md) for any interruption.
6. Return complete or incomplete status to the immediate calling thread for host review of the [handoff](references/nested-execution.md).

Use direct mounts by default; edits return immediately to the assigned host worktree.
A private clone needs an explicit change-return path before launch.
Each worktree must use its own locked dependencies.
Do not share or symlink dependency directories such as `node_modules`.
Do not replace a disconnected worker until the old writer has stopped and exclusive ownership is confirmed.
Silence or disconnect does not prove termination.
When the repository uses a task tracker, supply the task identifier.
The worker reads task specifications directly from the tracker using read-only commands.
Use a supplied Beads issue only when the existing host workflow uses it.

## Read when needed

- [SBX sandboxes](../sbx-sandboxes/SKILL.md): lifecycle, configuration, authentication, permissions, CLI facts, and AGY setup.
- [Worker launch](references/worker-launch.md): installed harness capabilities and tested Codex examples.
- [Host supervisor contract](references/host-supervisor.md): complete host-only task template.
- [Guest task prompt](references/subagent-task.md): complete guest edit, check, and repair template.
- [Progress and recovery](references/recovery.md): durable task records, interruptions, and safe resume.
- [Change return and handoff](references/nested-execution.md): workspace return, final state, and feedback.
