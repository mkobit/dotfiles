---
name: architect-scoping
description: >-
  Use when assessing a bounded implementation unit and assigning available native subagents to implementation and review.
---

# Architect scoping

Read the [assignment](../worker-handoff/references/assignment.md), project instructions, and current state. Assess complexity, dependencies, risk, acceptance criteria, and the smallest coherent unit before delegating. The assigned scope governs which available subagent models and reasoning efforts may be used; keep the coordinator model fixed for the run. Record choices and rationale through the project's existing mechanisms.

When native subagents are available, use their actual supported capabilities and assign one implementation writer and a separate reviewer with bounded responsibilities. Do not invent tool names or nested sandbox launchers. If required capability or an authorized model is unavailable, preserve evidence and report the prerequisite instead of changing models or credentials without authority.

Split work exceeding the assigned unit into follow-ups instead of unbounded rearchitecture. Resolve routine transient failures pragmatically, preserving evidence and checks; do not disable checks to make progress.
