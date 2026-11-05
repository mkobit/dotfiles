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

The root coordinator owns architecture, scope, task division, environment selection, credentials setup, recovery, independent review, and final judgment.
It selects and records either [verified autonomous delivery or edit-only host delivery](references/nested-execution.md#workspace-ownership).
An assigned guest may sign, push, and ship only under the verified autonomous contract.
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

Use the [host-coordinator tracker route](references/tracker.md) when a task ID is supplied.
The host claims once and supplies the complete frozen issue snapshot and actor; the guest must not claim again.
For autonomous delivery, the guest reports review-ready before merge and retains its complete assignment/session.
The root dispatches independent review of the final tested head and returns acceptance for that head and repository/PR scope.
Use the [review gate](references/delivery.md#independent-review-before-merge) before merge and [task delivery](references/nested-execution.md#task-delivery) for closeout.

## Read when needed

- [SBX sandboxes](../sbx-sandboxes/SKILL.md): lifecycle, configuration, authentication, permissions, CLI facts, and AGY setup.
- [Worker launch](references/worker-launch.md): installed harness capabilities and tested Codex examples.
- [Host supervisor contract](references/host-supervisor.md): host launch and supervision template.
- [Guest task prompt](references/subagent-task.md): guest prompt with an explicit delivery mode.
- [Progress and recovery](references/recovery.md): durable task records, interruptions, and safe resume.
- [Change return and handoff](references/nested-execution.md): workspace return, final state, and feedback.
