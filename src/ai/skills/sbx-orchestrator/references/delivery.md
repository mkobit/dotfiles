# Autonomous SBX delivery

Use this procedure only for assigned autonomous delivery after all [authority prerequisites](nested-execution.md#verified-autonomous-delivery) pass.
An explicit edit-only contract stops at returned edits and check evidence.
Inaccessible linked-worktree Git metadata forbids guest branching, commits, signing, push, and shipping.
Do not mount extra host metadata or silently move autonomous work to the host to bypass a failed prerequisite.

## Verify and ship

The consuming repository must provide real `mise run verify` and `mise run pr:ship` interfaces and complete tracked runtime assets.
These are required repository interfaces; they are not currently implemented dotfiles tasks.
Do not assume host-global mise tasks or configuration exist in a guest.
The shipping interface must support PR preparation and a review-ready phase without merge.
A missing interface, review gate, signing proof, proxy operation, or required-CI source is a blocker.
Inspect the repository interface before use; do not invoke an ungated automatic merge or invent unsupported flags.

Retain the assigned feature branch and expected repository, remote, base, and PR identity.
Reject main/default branches, detached HEAD, and uncommitted changes at shipping.
Make the required signed commit and verify its signature against the configured key.
Never disable signing or change keys to bypass a failure.
Run the real verification gate against the current head SHA and record the SHA, command, exit, and source evidence.
Use the shared interface and canonical push form:

```text
mise run verify
git push --set-upstream origin HEAD
mise run pr:ship
```

The shipping interface owns push and PR operations; the push line defines its required spelling, not an extra unconditional push.
Inspect relevant CI definitions and the configured required-check source.
Require a defined, nonempty set of required checks for the current pushed head SHA.
An empty result or successful local verification does not establish CI success.
Any head change invalidates prior head verification, CI evidence, and review acceptance; verify and check the new head before proceeding.
After failed CI, read the exact failed run logs and repair only assigned scope.
Allow at most two bounded repair attempts, with verification and current-head CI after each.
Then report the blocker without weakening checks, signing, or scope.

## Independent review before merge

After signing, verification, push, and PR preparation, report `review-ready` to the host.
Include repository, PR URL/identity, assigned scope, branch/base, final tested head SHA, signature proof, and local/CI check evidence.
Stop child writers and checks, retain the same complete assignment and guest session, and wait for host acceptance.
Do not merge, close the task, discard context, or launch a replacement while review is pending.
The root dispatches independent review of that final tested head and records the review result and evidence.
The root then sends acceptance that identifies the same head SHA and permitted repository/PR scope.
This is an internal host/guest gate, not a new human permission request.

The required repository shipping interface must refuse merge without matching independent-review evidence and host acceptance.
Before merge, it must check that the accepted head equals the current local, pushed, and PR head and the head covered by verification and required CI.
It must also check the accepted repository, PR, branch/base, and permitted scope against the assigned contract.
Missing evidence, a scope mismatch, a changed head, or unresolved review findings keeps merge blocked.
After review repairs, retest and request independent review and acceptance for the new head within the same assignment/session.
Recheck this gate immediately before merge; passing signing and CI alone cannot satisfy it.
This is the required shipping contract; runtime implementation belongs to the repository shipping task.

## Return merge evidence

A zero harness or `gh pr merge` exit does not prove merge.
A queued merge or changed head remains incomplete.
Require an observed `MERGED` state with the expected repository, PR, branch/base, and final head SHA.
Return PR URL, final revision, exact required checks and exits, signature proof, and remaining manual work.
Successful guest publication is the return path and does not require host patch reapplication.

For an issue assignment, use the [host confirmation and close contract](tracker.md#merge-confirmation-and-close).
The guest returns `merge-confirmed-close-pending`; the host independently proves merge identity, the same tracker/owner, and unchanged material requirements before close.
A controlled host-close launch contract is required when the guest has no tracker.
A standalone shipping task must fail before publication if neither a tracker nor that explicit contract exists.
Do not treat missing guest tracker access as success.
Close failure preserves the pending phase and permits only confirmation/close recovery.
