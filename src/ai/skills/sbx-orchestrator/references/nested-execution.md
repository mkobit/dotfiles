# Change return and handoff

## Workspace ownership

The root selects the environment, delivery mode, feature branch, base revision, and workspace before the writer starts.
Default to repo-local `.worktrees/<task>` when project rules permit it.
Check write boundaries, existing worktrees, initial changes, and exclusive ownership.
Use `git check-ignore .worktrees/` and `git worktree list` as applicable.
Record exceptions and use one exclusive workspace for each writer.
Each workspace keeps its own locked dependencies; do not share or symlink dependency directories.
Each consuming repository owns its complete tracked kit and runtime assets for fresh reproduction.
Do not depend on host-global tools or install replacements outside that kit.

### Verified autonomous delivery

The host must verify and record all prerequisites before it assigns guest Git or PR work:

- Usable guest Git metadata, expected repository, assigned feature branch, and base revision.
- Exclusive workspace ownership, separate from tracker claim ownership.
- Signing proof with the configured public key or subkey.
- Successful required Git and GitHub CLI operations through the configured proxy.
- A real repository `mise run verify` gate and a defined, nonempty required-CI source.
- The [host-coordinator tracker contract](tracker.md), including the frozen snapshot and unique launch actor when an issue is supplied.

With these proofs and task authority, the guest may use its assigned branch, implement, check, sign, push, and run `mise run pr:ship`.
The root retains architecture, scope, task division, environment selection, credentials setup, recovery, independent review, and final judgment.
Do not weaken signing or checks, copy raw tokens, or add host metadata mounts to make preflight pass.
Missing autonomous prerequisites are blockers; do not silently change the task to host delivery.
The repository must provide these interfaces and tracked runtime assets before autonomous launch.
They are required interfaces, not a claim that dotfiles currently implements them.
See [SBX delivery](delivery.md) for head, CI, independent review acceptance, and merge evidence.
Autonomous merge requires root acceptance of independent review for the same final tested head and repository/PR scope.
The guest retains its complete assignment/session while review-ready; a new head invalidates acceptance.

### Direct mount and edit-only host delivery

With `workspace.clone: false`, edits return immediately to the assigned host worktree.
Record mount mapping, branch, base, initial changes, and the selected return mode.
A linked worktree can point to Git metadata outside the mount.
If that metadata is inaccessible, use an explicit edit-only host-delivery contract with host-verified repository and base evidence.
The guest must not branch, commit, sign, push, or ship in this mode.
Do not add metadata mounts to change the mode.
Direct whole-unit SBX launch remains valid for this edit, check, and repair loop.
The host reviews returned edits after the writer stops and performs authorized delivery.
Visible edits alone do not prove completion.

### Private clone

Use `workspace.clone: true` only as an explicit private-clone option.
Before launch, verify the guest repository and base, assigned branch, and return transport.
For autonomous delivery, record the branch or PR return path and validate any returned `sandbox-NAME` branch identity.
Successful guest branch publication does not require a second host patch application.
For edit-only delivery, define an artifact route for tracked, untracked, binary, and deleted files and the check evidence.
The host validates paths, base identity, and conflicts before it applies that artifact to the assigned feature worktree.
Preserve baseline and return evidence in the [durable record](recovery.md).
If no return route exists, report the blocker; private-clone edits are not visible on the host.
Both workspace modes use the same host-owned tracker route.

## Required final handoff

Both the guest and host supervisor must report these fields.
Use `none`, `unknown`, or `not run` when appropriate instead of omitting a field.

```text
Completion: <complete or incomplete, with acceptance evidence>
Remaining work: <specific work, including host review, or none>
Changed files: <paths and purpose>
Checks: <exact commands, execution location, exit codes, and passed or skipped counts>
Unrun checks: <commands and reasons>
Blockers: <missing prerequisites or required host action, or none>
Active processes: <identity and state of worker and child checks, or none>
Session identity: <harness session or process identity when available, or unknown>
Log location: <host output log and guest report locations, with access boundaries>
Recovery pointers: <durable host record, checkpoint, and returned artifacts>
Workspace: <assigned worktree or private clone, base revision, and change-return state>
Phase: <current phase, last completed check, and any active or failed check>
```

Preserve failed command exit codes even after a repair passes.
Distinguish a skipped test from a passed check; a skip does not prove deployment.
Return this concise stable summary to the immediate calling or orchestrating thread for both complete and incomplete work.
The supervisor or root owns the final completion and integration judgment.
The host coordinator verifies returned changes and performs independent review before integration.
Run required checks once and repeat only after related changes or failures.

## Task delivery

Guest process completion alone does not prove delivery.
For autonomous work, use the [SBX delivery contract](delivery.md).
For edit-only work, root reviews the diff, resolves findings, runs required checks, and performs authorized feature-branch delivery.
Root dispatches independent review before integration in both modes.
Autonomous delivery must pass the head-bound review gate before merge; guest merged completion cannot start that review.
For a supplied issue, use [host merge confirmation and close](tracker.md#merge-confirmation-and-close).
Keep the claim open for queued or unconfirmed merge and for changed requirements.
Return exact evidence to the tracker owner if access is unavailable.

Preserve required evidence before cleanup.
Confirm no active writers or checks, unreturned changes, or needed artifacts remain before removal.
Remove only authorized task-owned resources and preserve user work.
Report kept resources and incomplete delivery explicitly.

## Task feedback

Keep friction and unclear instructions in the existing handoff.
Include expected and actual behavior, revision, source instruction, and evidence without credentials.
Separate observations from suspected causes.
The authorized host updates an existing owning record only when the workflow uses a tracker.
Do not require Beads, create a tracker, or write to a copied host database.
Link a proposed instruction correction to an acceptance example.
Verify the revised prompt in its intended environment before claiming that it works.
