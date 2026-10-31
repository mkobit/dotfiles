# Change return and handoff

## Workspace ownership

Default to repo-local `.worktrees/<task>` when project rules permit it.
Before creation, check project rules, write boundaries, existing worktrees, branch, base revision, and exclusive ownership.
Use `git check-ignore .worktrees/` and `git worktree list` as applicable.
Record the path and reason for any required exception.
A repo-local worktree does not remove platform protection of Git metadata; use required host access for Git operations.
Use one assigned worktree for each concurrent writer.
The host coordinator selects or creates the feature branch and worktree before delegation under the approved task authority.
With `workspace.clone: false`, guest edits return immediately to that host worktree.
No patch transfer or guest commit is needed for a direct mount.
Each worktree must keep its own isolated, locked dependencies (such as `bun install --frozen-lockfile`).
Do not share or symlink dependency directories across worktrees.
The host reviews the diff after the writer stops; visible edits alone do not prove completion.
A worktree mount can leave `.git` metadata or host task records outside the guest mount.
Use the verified [read-only task context](subagent-task.md#read-only-task-context) route when the guest needs task definitions.
Keep branch operations, issue creation, and state transitions on the host coordinator.
Write only explicitly authorized notes or comments.

Use `clone: true` as a deliberate private-clone option.
Before launch, verify the clone base identity and the change-return artifact and transport.
Define how the host receives the diff, untracked and binary files, deletions, and required evidence.
For example, use an authorized patch or artifact export that preserves the task's file changes.
Deliver the returned changes into the root-owned feature worktree, not a separate unreviewed checkout.
The host checks artifact paths, base identity, and conflicts before applying the artifact.
Preserve baseline and received-diff evidence in the [durable record](recovery.md).
If no return path exists, report the blocker; do not assume private-clone edits are visible on the host.
Do not use guest commits, pushes, or credentials as an implicit return process.
Perform host publication only under the task authority and repository rules in [task delivery](#task-delivery).

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

Guest completion is not task delivery.
Root inspects the final diff and documentation, resolves review findings, and runs all required checks.
Under the task authority, commit on a feature branch, push, open a PR, and check required PR results.
Merge only under repository rules and explicit approval requirements.
For a supplied Bead, link the PR, final revision, check results, and review evidence to that issue and sync authoritative tracker state.
Keep the issue open until delivery and root verification are recorded.
If tracker access is unavailable, return the exact evidence for the owning root to attach; do not create another tracker.

Preserve required evidence before cleanup.
Before removal, confirm no active writers, unreturned changes, or needed artifacts remain.
Under the applicable authority, remove task-owned environments, worktrees, temporary reader databases, logs, and branches.
Preserve unrelated or original environments and user work.
List kept resources and reasons, and report incomplete delivery explicitly.

## Optional Beads workflow

Use Beads only when the existing host workflow supplies an issue.
Record that exact issue ID and verified host tracker location in the task-specific durable record.
Pass issue and task context to the guest; the guest returns evidence without copying or writing the tracker database.
After review, the authorized host updates that specific issue.
Before invoking `bd` on the host, use installed `bd --help` and `bd <command> --help` for syntax, consistent with the authored Beads skill.
For guest access, use the selected [read-only task context](subagent-task.md#read-only-task-context) route.
Do not require a `bd` installation, create a tracker, invent a paused status, or select another task automatically.
Quota or token interruption leaves the task unfinished and must not close the issue.

## Task feedback

Keep friction and unclear instructions in the existing handoff.
Include expected and actual behavior, revision, source instruction, and evidence without credentials.
Separate observations from suspected causes.
The authorized host updates an existing owning record only when the workflow uses a tracker.
Do not require Beads, create a tracker, or write to a copied host database.
Link a proposed instruction correction to an acceptance example.
Verify the revised prompt in its intended environment before claiming that it works.
