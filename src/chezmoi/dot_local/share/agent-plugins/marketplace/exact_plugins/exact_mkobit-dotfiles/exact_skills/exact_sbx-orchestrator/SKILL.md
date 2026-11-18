---
name: sbx-orchestrator
description: >-
  Use when coordinating delegated coding tasks in SBX, including worker launch, task prompts, progress, recovery, and handoff.
  Use sbx-sandboxes for lifecycle, configuration, authentication, permissions, and CLI facts.
---

# SBX orchestrator

Use this skill when the authorized task calls for delegated coding in SBX.
Respect explicit command-only requests and narrower user scope.
Use direct SBX commands for probes and command-only work, not as a substitute for a requested coding worker.

The root coordinator owns task division, unresolved questions, risk, integration, final review, and publication.
For normal edit/check tasks, it also owns branch management, tracker changes, commits, and signing.
An explicit private-clone assignment can give the guest delivery and tracker authority for one unit.
When available, a native host subagent uses host tools to launch a separate guest coding harness.
When no native subagent tool is available, the root coordinator may perform the host supervisor contract directly.
Its tools do not move into the guest.
The guest edits, checks, and repairs the assigned files directly in its workspace.
Task authorization permits this loop without routine nested approval requests.
Reuse that authority for needed task-specific host worktree and environment setup.
Ask only when task authority, actual platform permission, or a required credential action is missing, or when scope must expand.
It does not permit host policy changes or broader task scope.

## Coordinate a task

1. Use the [workspace contract](references/nested-execution.md#workspace-ownership) to select the feature branch and worktree.
2. Save the complete task and baseline in a [durable host record](references/recovery.md) with a discoverable task pointer.
3. Give the supervisor the [host contract](references/host-supervisor.md) and a separate [guest prompt](references/subagent-task.md).
4. Prove [environment readiness](../sbx-sandboxes/references/repository-setup.md#environment-readiness), set [shared limits](references/host-supervisor.md#shared-limits), and use the [worker launcher](references/worker-launch.md).
5. Update the record at milestones and use [recovery](references/recovery.md) for any interruption.
6. Return complete or incomplete status to the immediate calling thread for host review of the [handoff](references/nested-execution.md).

For edit/check tasks, use the [task context contract](references/subagent-task.md#read-only-task-context) and return changes for host review.
For an assigned pilot, use [delivery](references/delivery.md) and let the guest complete the assigned delivery without a routine host pause.

## Read when needed

- [SBX sandboxes](../sbx-sandboxes/SKILL.md): lifecycle, configuration, authentication, permissions, CLI facts, and AGY setup.
- [Worker launch](references/worker-launch.md): installed harness capabilities and tested Codex examples.
- [Host supervisor contract](references/host-supervisor.md): complete host-only task template.
- [Guest task prompt](references/subagent-task.md): complete guest edit, check, and repair template.
- [Progress and recovery](references/recovery.md): durable task records, interruptions, and safe resume.
- [Change return and handoff](references/nested-execution.md): workspace return, final state, and feedback.
