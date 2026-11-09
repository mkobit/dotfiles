# Assigned work contract

## Delivery mode

The root owns architecture, scope, task division, environment selection, credentials setup, recovery, independent review, and final judgment.
Retain the assigned repository, branch/base, workspace, scope, and delivery mode.
Do not silently switch modes or expand ownership.

For explicit edit-only host delivery, edit and check in the assigned guest and return the changes with evidence.
Inaccessible linked-worktree Git metadata forbids guest branching, commits, signing, push, and shipping.
Use host-verified repository/base evidence; do not add metadata mounts or copy credentials to bypass the boundary.
A direct mount returns edits to the assigned host worktree.
For a private clone, require verified repository/base, assigned branch, and an explicit return route for tracked, untracked, binary, and deleted files and evidence.
The host validates paths, base, and conflicts before applying edit-only artifacts.

Autonomous Git and PR delivery requires recorded host proofs:

- Usable guest Git metadata and the expected repository, assigned feature branch, and base revision.
- Exclusive workspace ownership, separate from tracker claim ownership.
- Successful signing with the configured public key or subkey.
- Proved required Git and GitHub CLI operations through the configured proxy.
- A real repository verification gate, a defined nonempty required-CI source, and a shipping interface with the independent review gate.
- The host-owned frozen issue snapshot and unique launch actor when an issue is supplied.

Each consuming repository owns its complete tracked kit and runtime assets for fresh reproduction.
Do not depend on host-global tasks/configuration or install replacements outside the kit.
Missing autonomous prerequisites are blockers, not permission to change modes, weaken signing/checks, or use host execution.
For a private clone, verify the branch/PR return path and any returned branch identity against the assignment.
Successful authorized guest publication does not require host patch reapplication.
Follow [delivery](delivery.md), including host acceptance of independent review before merge.

## Frozen issue context

The host checks ready work and atomically claims once with a unique actor per launch record before worker launch.
The guest reads the supplied complete frozen snapshot and uses the same actor and material-requirements hash as that record.
The snapshot includes issue/tracker identity, description, design, acceptance criteria, dependencies, agreed scope, owned paths, and current assignee/status.
A task ID alone is insufficient.
The existing host claim satisfies the claim step; never claim again, require guest Beads, copy/import a database, or change task authority.
A repeated claim by the same actor does not prove exclusive workspace ownership.
Return unrelated work, material questions, or blockers to the designated tracker owner without changing their files.
Refresh stale or inconsistent context through the host before dependent work.

## Recovery

Preserve the sandbox, workspace, complete prompt, source baseline, identity, actor, logs, checkpoints, phase, and check exits on interruption.
Record the exact failure and remaining work; quota, disconnect, and process exit do not prove completion.
Do not rapid-retry unknown quota or change model/account, credentials, or environment configuration.
Silence, client loss, a missing session handle, or daemon restart does not prove that old writers or child checks stopped.
Before resume or replacement, prove termination and exclusive ownership with supported process/session evidence.
Reconcile source, mount, repository/base, and current diff with the checkpoint.
Retain the same complete assignment/session during the review-ready wait.
Any head change invalidates review acceptance; relevant source changes also make checks stale.
If ownership or termination cannot be proved, report incomplete status without starting another writer or rebuilding the environment.

## Host confirmation and close

After review acceptance and confirmed merge, return PR URL, repository, branch/base, head SHA, required checks, signature proof, and merge evidence.
For an issue assignment, retain `merge-confirmed-close-pending` until authoritative host close succeeds.
This is a launch phase, not a Beads status.
The host independently proves `MERGED` and the expected repository, PR, branch/base, and head SHA.
It also requires the same tracker identity, issue, expected owner, and unchanged material requirements against the frozen snapshot/hash.
Exclude routine audit timestamps and expected status changes from that comparison.
Changed material requirements leave the issue open for root review even after merge.
Only then may the host close through the saved authoritative route with the verified PR URL/head in the reason and verify closed status.
A zero harness or merge-command exit, queued merge, or missing tracker does not satisfy this contract.
Close failure preserves the pending phase; recover only confirmation/close, never repeat implementation or create another PR.

## Handoff

Report complete or incomplete status and remaining work explicitly.
Include changed paths, source hashes/head, exact check commands and location, exits, passed/skipped counts, unrun checks, and blockers.
Include workspace/base and return state, phase, session/process identity, and log, report, checkpoint, and artifact pointers.
Use `none`, `unknown`, or `not run` for unavailable fields.
Preserve failed results after a repair passes.
Stop child writers and checks before handoff or the review-ready wait.
The root owns final acceptance and authoritative tracker close.
