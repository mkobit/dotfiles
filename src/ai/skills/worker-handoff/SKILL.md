---
name: worker-handoff
description: Use when an SBX guest receives a bounded issue assignment or a host-frozen issue snapshot.
---

# Worker handoff

Read the assigned prompt, applicable repository instructions, complete issue snapshot, and baseline before edits.
Retain the assigned repository, scope, branch/base, actor, and delivery mode.
The host owns architecture, scope, task division, environment selection, credentials setup, recovery, independent review, and final judgment.

Use the [assignment and delivery-mode contract](references/assignment.md#delivery-mode).
For a supplied issue, use the [frozen issue contract](references/assignment.md#frozen-issue-context).
The host checks ready work and claims once; the guest never claims again or requires guest Beads.
Record unrelated work, blockers, and material questions for the designated owner without expanding scope.

Implement, check, and repair only the assigned files in the guest.
Use the repository's tracked kit and runtime assets; report missing prerequisites without ad hoc installation or host-global assumptions.
Run repository commands directly and do not run nested SBX.
Keep source-sensitive checks stale after relevant edits.

For explicit edit-only host delivery, return changes and exact check evidence without guest Git writes or shipping.
For verified autonomous delivery, follow [delivery](references/delivery.md) for signing, current-head verification, CI, independent review before merge, and host close.
Report review-ready and retain the same complete assignment/session while waiting for root acceptance of the final tested head and repository/PR scope.
A new head invalidates acceptance; the shipping interface must refuse merge without matching independent-review evidence.
Do not silently switch between delivery modes.

On interruption, preserve workspace, prompt, baseline, identity, actor, logs, checkpoints, phase, and check exits.
Use [recovery](references/assignment.md#recovery) before resume or replacement.
Silence or a lost client does not prove termination.
Prove old-writer termination and exclusive ownership first; do not rapid-retry unknown quota or change model/account.

Return the [required handoff](references/assignment.md#handoff) with completion, remaining work, source identity, exact checks/exits/counts, blockers, and evidence pointers.
Stop child writers and checks before handoff.
Root review acceptance precedes autonomous merge; host merge confirmation and authoritative close follow it.
