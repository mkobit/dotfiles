# Task 7 contract corrections

## Fixed scope

Keep `feat/sbx-rearch` and [draft PR 1014](https://github.com/mkobit/dotfiles/pull/1014).
Keep this migration's linked worktree in edit-only mode.
Do not ship that branch through the new autonomous issue workflow.
The host claims once, freezes the full assignment, dispatches independent review, and closes the issue.
The guest can implement, verify, sign, push, prepare its PR, and merge after exact-head review acceptance.
The guest never invokes `bd`.

## Add one recovery form

Keep the four public task names.
Extend the host command with this form:

```text
mise run agent:work --resume RUN_ID [--review FILE]
```

`RUN_ID` identifies the saved host record, not a new issue or a guest-supplied path.
Reject `--bead`, `--agent`, `--clone`, and `--model` with `--resume`.
Recover those values from the saved record.
Reject path traversal, symlinks, unknown run IDs, wrong repositories, and concurrent resume attempts.
The resume command must confirm that the old writer and its child writers have stopped.
An unknown process state blocks a replacement writer.

Use native harness resume only where installed help proves support.
Otherwise start the same harness with a continuation prompt from the saved record.
This remains the same assigned unit: same run, actor, claim, workspace, sandbox, branch, PR, and snapshot.
It must not claim again, recreate a branch, open a second PR, rebuild the environment, or delete resources.
For `merge-confirmed-close-pending`, run host confirmation and close only; no guest writer is needed.

## Add the review pause

After local verification and required CI succeed for head `H`, guest `pr:ship BEAD_ID` writes `review-ready` and returns a documented pause code, such as `75`.
Record the phase in JSON; the outer harness exit code alone cannot identify it.
The worker prompt must stop on this phase and return the evidence path.
A review pause does not consume a CI repair attempt.
Do not poll indefinitely for a file and do not start a service.

Root dispatches a separate reviewer against `H` and the frozen assignment.
No user permission step is required for this review.
The reviewer returns its result to root.
Root saves that result outside guest-controlled state and calls the resume form with `--review FILE`.
The CLI does not dispatch native subagents itself.
An alternative is to keep the guest process waiting for review.
That avoids a harness restart but holds a writer and needs timeout recovery.
Use the bounded pause and resume route; it requires one continuation launch and keeps process ownership explicit.

Use this minimum review result:

| Field | Required value |
| --- | --- |
| `schema_version`, `run_id` | Supported schema and the saved run |
| `assignment_hash` | Saved hash of material requirements |
| `repository`, `pr_number` | Canonical forge identity and this PR |
| `base_branch`, `head_branch`, `head_sha` | Saved branches and exact tested head |
| `verification_evidence` | Durable evidence for successful verification of this head |
| `reviewer_id`, `dispatch_id`, `review_evidence` | Independent root-dispatched reviewer and its result |
| `decision` | `accepted` or `changes-requested` |

The host validates the result against its own record and live PR identity before accepting it.
The reviewer must be separate from the implementing worker.
Keep the host copy as authority; guest files cannot authorize host close.
Transfer a run-specific copy to the guest through the same asset route as the assignment.
This is a workflow gate, not a new credential or cryptographic signing system.

With acceptance, guest `pr:ship` repeats its identity, clean-tree, signature, verification, and current-head CI gates before merge.
It requires the acceptance head, tested head, local head, and live PR head to be equal.
A changed head invalidates review, verification, and CI evidence.
Changes requested resume implementation and return for a new independent review.
Missing or rejected acceptance must stop before `gh pr merge`.
After merge, return `merge-confirmed-close-pending` for independent host confirmation and close.

Add these phases to the existing durable record rather than a second state system:

```text
claimed -> running -> review-ready -> review-accepted -> merge-confirmed-close-pending -> complete
```

Keep failure and unknown outcomes, evidence paths, and previous attempts in the same record.
On resume, first reconcile live facts; an interrupted merge command can already have merged the PR.
Do not repeat publication or implementation after merge confirmation.

## Fix base resolution before claim

Resolve the configured remote and base branch before claim.
For a missing base setting, use that remote's actual default branch, not the caller's current branch.
Read the remote branch SHA and save it as `expected_base_sha`.
A stale local remote-tracking ref is insufficient.
Require the corresponding local Git object, or stop with the exact fetch action needed before preflight can pass.
Save caller branch/SHA separately for audit.

For direct autonomous delivery, require a clean, exclusive checkout at `expected_base_sha` before claim.
Do not switch an active orchestration checkout or carry its feature commits into a new issue branch.
If the caller is on an unreviewed feature head, stop and identify the required base checkout.
After claim, create the new feature branch from the recorded SHA.

For clone delivery, the host can keep its orchestration branch.
Before claim, prove the expected base object exists in the guest clone and prove its change-return route.
After claim, select the expected base and create the assigned branch before the worker writes.
Require a clean guest checkout and exact SHA equality at that point.
Never treat the clone's inherited HEAD as the requested base without comparison.
Verify the required task and environment prerequisites for the selected base; their presence only in the parent feature tree is insufficient.

## Wait for actual current-head CI

Freeze the nonempty required-check policy in host state.
Use the seven exact names in [the progress note](../sbx-rearch-progress.md), sourced from [CI run 41378483668](https://github.com/mkobit/dotfiles/actions/runs/41378483668).
Use SHA-scoped GitHub check-run/status responses to bind results to the expected head; the documented `gh pr checks` JSON fields alone do not contain a head SHA.
Follow pagination.
Confirm the supported response shape with a read-only probe before implementing its parser.

Use a bounded monotonic deadline for registration and completion.
Empty results and missing names remain waiting states until that deadline; they can never pass.
Pending and queued checks also wait.
Denied API access, a changed PR head, failed, cancelled, skipped, or unknown results cannot pass.
Reject ambiguous duplicate required names rather than selecting a convenient success.
Ignore stale results for other SHAs.
Before merge, re-read the PR head and current results, require the accepted SHA, and pass `--match-head-commit SHA`.
Do not enable auto-merge while review is pending.

## Keep the proven guest asset route

Use [the guest task contract](guest-task-contract.md).
Install only the static `pr:ship` wrapper in `.sbx/kit/files/home/.config/mise/tasks/pr/ship` and set its executable mode in tracked kit setup.
Use the kit's pinned Python `3.14.7` by absolute path.
The host exports its deployed helper, an allowlisted runtime projection, the frozen assignment, and run-specific state paths.
Keep host tracker connection details, credentials, and host state paths out of the projection.
Direct mode uses the workspace mount.
Clone mode uses individual native `sbx cp` operations after clone creation, with content and run-identity checks before launch.
Check that Mise resolves `pr:ship` to the kit-installed task, since repository tasks can override global tasks.

## Transport facts and remaining probes

Installed help rechecked in this review confirms these interfaces:

```text
sbx env plan ENV_PATH --name NAME [--clone]
sbx env run ENV_PATH --name NAME --detach --force [--clone]
sbx env exec --name NAME ENV_PATH -- COMMAND ARG...
sbx exec --workdir GUEST_REPO NAME COMMAND ARG...
sbx cp HOST_FILE NAME:GUEST_FILE
sbx cp NAME:GUEST_FILE HOST_FILE
```

`--clone` forces clone mode on; help lists no `--no-clone` override.
Direct mode must validate an effective `workspace.clone: false` setting.
`env run --detach` starts the environment, not the coding harness.
`exec --detach` is unsupported.
Both `exec` forms can start a stopped sandbox, so guest read probes are not always free of lifecycle effects.
Clone help promises a private clone and host remote `sandbox-NAME`; it does not prove remote URLs, branch visibility, or GitHub push routing for this environment.
Do not replace the native clone route or invent a transport from these descriptions.

Remaining read-only probes, against an already running assigned environment:

1. Inspect `sbx env plan ENV_PATH --name NAME [--clone]` for effective mount, kit, and workspace mapping.
   It applies no changes.
   Check whether the plan exposes a validated guest repository path; do not guess a fallback path.
2. Query `sbx ls --format json` and inspect its actual workspace fields.
   Keep `exec` probes on the recorded running environment.
3. In the guest, read `git rev-parse --show-toplevel`, `--git-dir`, `--git-common-dir`, `HEAD`, branch names, and remote URLs.
   Read `WORKSPACE_DIR` without an environment dump.
   Verify Git metadata access and the configured base object.
4. On the host, inspect the `sandbox-NAME` remote URL and `git ls-remote sandbox-NAME` results.
   In the guest, inspect the configured forge remote and read-only remote refs.
   Compare repository, branch, and SHA identities without fetching or pushing.
5. Run guest `mise tasks ls --json`, inspect its task source, and check pinned Python/tool versions and helper input hashes.
6. Query a real existing PR and SHA-scoped GitHub check/status responses to establish registration, head, pagination, and rerun shapes.

The private clone does not yet exist for this route, so those clone probes require a separately authorized lifecycle test first.
Native clone creation, runtime file copy, retry copy destinations, signed disposable-object creation, and publication are integration tests with writes, not read-only probes.
The prior fresh-kit result proves tools and inherited settings; it does not prove the new wrapper, clone transport, signing, or autonomous delivery.

## Bounded implementation units

Run these units in order where they share files.
Do not assign the helper or its tests to concurrent writers.
Root keeps branch management, final review, commits, and publication for this migration.

| Unit | File ownership | Acceptance |
| --- | --- | --- |
| 7a: task and runtime inputs | `mise.toml`, `.agent-workflow.json`, Mise/runtime templates, static guest wrapper, kit install mode, `test_mise.py` | Each verify command runs once; disabled/overlay rendering works; actual nested-directory Mise invocation works; guest wrapper preserves arguments, task source, settings, and pinned interpreter. |
| 7b: launch and recovery foundation | Standalone helper and `test_agent_workflow.py` | Base is remote-resolved before claim; one saved actor claims once; full snapshot and host record persist; direct/clone ownership and assets validate; failures preserve claims; `--resume` prevents duplicate writers; no guest `bd`. |
| 7c: ship, review, and host close | Same helper and tests, after 7b handoff | Stale/empty CI cannot pass; registration can arrive later; exact-head review pause and resume work; missing acceptance cannot merge; changes invalidate review; merge confirmation precedes saved-route close; failed close resumes without a guest writer. |
| 7d: remaining commands and integration | Same helper and tests, after 7c; root runs final deployment checks | Architect arguments match installed interactive help; bootstrap preserves files, dry-run makes no changes, and checks are real; fresh kit discovers wrapper; permitted direct/clone lifecycle tests prove transport; independent review accepts the final tested implementation head. |

Do not enable unfinished commands as successful placeholders between units.
Return changed files, exact checks and exits, remaining prerequisites, and the durable evidence path at each handoff.
Use temporary Git repositories and command stubs for all offline claim, PR, merge, and recovery tests.
Include a full two-pass test: prepare PR -> review pause -> host acceptance -> same-run guest continuation -> confirmed merge -> host close.
Also test changes requested, changed head, stale acceptance, forged guest close data, ambiguous claim, disconnect, delayed CI registration, and merge success followed by lost output.

## Minimum document amendments

- `tasks.md`: add resume form, review pause/result, exact-head merge gate, remote-base resolution, CI registration wait, and guest asset ownership.
  Replace guest delivery step 13 with pending host close.
- `tracker-route.md`: add independent review before merge and acceptance validation at host close.
  Remove its stale claim that the current brief still requires a feature branch before launch.
- `interfaces.md`: register wrapper and runtime asset ownership and the shared record/review fields.
  No additional machine configuration switch or public task is needed.
- `sbx-rearch.md`: mark its raw shell workflow and obsolete guest Beads steps as superseded by the accepted task, tracker, and review contracts.
  Keep the long-lived migration exception explicit.

## Remaining prerequisites

No new product choice is needed for these contracts.
Actual host tracker directory/version, guest signing route, GitHub proxy operation, clone return route, and fresh-wrapper integration remain unproved prerequisites.
The existing reports do not establish them.
Task 7 must stop before claim or merge at the relevant missing prerequisite and retain recovery evidence.

The read-only review produced this report; root copied it into the shared notes.
It ran local file reads and installed SBX help commands.
It did not create, start, stop, or modify a sandbox, tracker service, credential, branch, or PR.

## Sources

- [Task 7 brief](tasks.md).
- [Tracker route](tracker-route.md).
- [Configuration interface](interfaces.md).
- [Fresh-kit evidence](kit-reproduction-report.md).
- [Guest task and isolated Mise evidence](guest-task-contract.md).
- Installed `sbx create`, `env plan`, `env run`, `env exec`, `exec`, `cp`, and `ls` help, read in this review.
