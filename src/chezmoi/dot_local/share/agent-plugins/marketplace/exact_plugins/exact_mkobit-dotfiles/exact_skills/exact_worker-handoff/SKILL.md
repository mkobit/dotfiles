---
name: worker-handoff
description: >-
  Use when accepting a bounded worker assignment, selecting one authorized queue item, and returning resumable evidence.
---

# Worker handoff

Accept the [assignment](references/assignment.md) before acting. Read the project's instructions and latest state, and use [repository bootstrap](../repo-bootstrap/SKILL.md) for readiness. A project may supply a prompt or issue instead of a tracker; Beads is not mandatory.

For an explicitly authorized queue task, select and work on one eligible unit in one active guest. The guest owns only the tracker operations explicitly assigned to it; general edit/check work retains host delivery by default. Use the project's native tracker procedure, including the [Beads replica guidance](../sbx-orchestrator/references/tracker.md) when applicable. Never infer tracker, delivery, signing, or remote-write authority from tool access.

Assess the unit with [architect scoping](../architect-scoping/SKILL.md). Use actual available native subagent capabilities, with one implementation writer and a separate reviewer; do not invent tools or launch nested sandboxes. Preserve progress and resume pointers using project mechanisms. For an explicitly assigned delivery, follow the [delivery procedure](references/delivery.md). Otherwise return the requested evidence and defer delivery or expanded work.
