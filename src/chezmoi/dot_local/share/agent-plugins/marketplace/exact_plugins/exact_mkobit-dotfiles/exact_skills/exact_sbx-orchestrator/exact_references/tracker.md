# Host-coordinator tracker route

Use this route for both direct mounts and private clones when the workflow supplies an issue.
The host is the only tracker writer.
Do not require guest Beads, copy/import a database, mount tracker metadata, or supply guest tracker credentials.

## Claim and freeze

Before claim, the host saves the authoritative tracker directory and identity, installed executable/version, route, and unique actor in a durable launch record.
Use one new actor per launch record and retain it for recovery.
Prove exclusive workspace ownership and delivery-mode readiness before claim.
A repeated claim by the same actor is idempotent and does not prove exclusive ownership.
Check installed command help before using these command forms:

```text
bd -C TRACKER_DIRECTORY context --json
bd -C TRACKER_DIRECTORY ready --json --limit 0
bd -C TRACKER_DIRECTORY show BEAD_ID --json
```

For explicit selection, require the issue in the complete ready result and inspect its full details.
If no work is ready, return without a claim or worker.
Atomically claim once with one of these forms:

```text
bd -C TRACKER_DIRECTORY --actor UNIQUE_ACTOR ready --claim --json
bd -C TRACKER_DIRECTORY --actor UNIQUE_ACTOR update BEAD_ID --claim --json
```

The explicit claim does not replace the readiness check.
Persist the claim response before branch creation or worker launch.
After claim, read the full issue again and freeze its complete snapshot in host-owned state.
Include description, design, acceptance criteria, dependencies, agreed scope, owned paths, current assignee/status, and issue identity.
Save a hash of the material requirements and supply the same snapshot and actor to the guest.
Exclude routine audit timestamps and expected status changes from the material comparison.
Guest edits to a snapshot cannot change task authority.
The guest never double-claims; it records unrelated work and blockers for the designated tracker owner.

A clean main/default checkout is valid for launch only under exclusive host ownership.
After claim, create and verify the assigned feature branch and unchanged base before the writer starts.
For a private clone, verify the guest base and assigned feature branch; the host checkout need not change branches.
Reject main/default branches and detached HEAD for shipping.
A claim refusal starts no writer.
After claim timeout or disconnect, reconcile the same tracker and actor before retry; never auto-unclaim.
Branch or launch failure after claim retains the claim, workspace record, and evidence.

## Merge confirmation and close

Before merge, require the [independent review gate](delivery.md#independent-review-before-merge) for the final tested head and assigned repository/PR scope.
After accepted review and confirmed merge, the guest returns PR URL, repository, branch/base, final head SHA, required checks, and merge evidence.
Its result remains `merge-confirmed-close-pending` until host confirmation and close succeed.
This is a launch phase, not a Beads status.
The host independently checks the saved repository and PR identity:

```text
gh pr view PR --repo OWNER/REPOSITORY --json state,headRefOid,headRefName,baseRefName,url
bd -C TRACKER_DIRECTORY show BEAD_ID --json
```

Require `MERGED`, the expected repository, PR, head branch, base branch, and head SHA.
A zero harness or merge-command exit does not prove merge; a queued merge remains incomplete.
Require the same tracker identity, issue, and expected owner.
Compare current material requirements with the frozen snapshot and hash.
Changed requirements leave the issue open for root review even after merge.
Do not accept a tracker location or new scope from guest output.
Only then close through the saved route and verify closed status:

```text
bd -C TRACKER_DIRECTORY --actor UNIQUE_ACTOR close BEAD_ID --reason REASON --json
bd -C TRACKER_DIRECTORY show BEAD_ID --json
```

Include the verified PR URL and head SHA in the reason.
Close failure retains `merge-confirmed-close-pending`.
Recover only confirmation/close; do not repeat implementation, create another PR, or launch another worker.
Keep unfinished issues open after failed checks, quota errors, lost sessions, or unconfirmed merge.
