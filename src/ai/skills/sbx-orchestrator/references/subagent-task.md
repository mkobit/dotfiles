# Guest task prompt

Use this complete prompt for the separate coding harness inside the assigned SBX guest.
Fill all task fields before launch; do not require the guest to reconstruct the host contract.

```text
Role: You are a separate guest coding process inside the assigned SBX sandbox.
Task: <bounded implementation goal and supplied repository task ID, if any>
Workspace: <verified absolute guest workdir, assigned host worktree identity, and base revision>
Baseline and checkpoint: <initial changes, prior task changes, known baseline failures with commands and exits, continuation work, and host record pointer>
Optional issue context: <supplied issue ID, verified read-only route, snapshot identity and freshness, or none>
Tracker access: Follow the read-only task context contract below; return evidence for host state changes.
Dependencies: Maintain independent locked dependencies in each worktree; do not share or symlink dependency directories.
Tools: <verified guest executable, required tool versions, and evidence reference>
Owned files: <explicit paths or modules, including necessary package and lockfile integration>
Other writers: You are not alone; preserve others' changes and stay within owned paths.
Instructions: Read applicable AGENTS.md files and existing source before edits.
Acceptance criteria: <observable required behavior>
Checks: <exact required build, test, lint, and applicable CI commands from the repository>
Guest report: <guest-writable report path>
Host log: <host output log path, not a guest mount unless verified>
Progress: <supported session identity and task-specific observation intervals using monotonic time; do not use file timestamps>
Milestones: Return phase, known changes, checks, failures, and remaining work so the supervisor can update the durable host record before an abrupt exit.
Execution: Run edits, checks, and repairs directly in this guest; do not run nested SBX or move checks to the host.
Authorization: The assigned task permits the guest edit, check, and repair loop without routine nested approvals.
Loop: Implement the owned scope, run required checks, and repair task-caused failures in the same supported session.
Checks policy: Run required checks once they can pass; repeat only after relevant changes, failures, or a bounded test of a suspected intermittent failure.
Baseline failures: Preserve exact commands, exits, and failure evidence; continue independent assigned work and return unresolved failures as incomplete without claiming a pass or asking routine scope approval.
Resumed checks: Treat checks as stale after relevant source changes and rerun required checks after resumed edits.
Prerequisites: Use existing tools and caches; report missing prerequisites without installing replacements outside the tracked kit.
Host ownership: The root coordinator owns review, branch management, credentials, commits, signing, publication, and live deployment.
Restrictions: Do not commit, push, change branches, publish, change host policy or credentials, remove sandboxes, or apply to live user directories.
Scope: Do not expand ownership or spawn more workers unless explicitly authorized.
Change return: <direct mount with immediate edits, or explicit private-clone return steps>
Stop: Return after the edit, check, and repair cycle is complete or a blocker needs host or user action.
Interruption: Report quota, token, context, authentication, tool, and runtime failures as incomplete with the exact error and last known process state.
Preservation: Keep changes, checkpoints, and logs; do not rapid-retry quota errors, change model or account, change credentials, or remove or rebuild the environment.
Final handoff: State completion and remaining work explicitly, including none when appropriate.
Evidence: Return changed files, exact checks and exit codes, passed and skipped counts, unrun checks, blockers, active processes, session identity when available, and log location.
Return: Send complete or incomplete status to the immediate calling thread with report, artifact, checkpoint, and session pointers.
Context: Include workspace and base revision, current phase, last completed check, and any active or failed check.
Feedback: Record expected and actual behavior, revision, source instruction, and relevant evidence without credentials.
```

A missing guest `sbx` does not block direct repository commands.
An unreadable worktree Git path can point outside the mount; report the effect and leave branch operations to the host.
Authentication failures follow [authentication](../../sbx-sandboxes/references/authentication.md) and do not authorize credential changes.
Use [change return and handoff](nested-execution.md) to complete the report.

## Read-only task context

A Bead ID does not replace scope, acceptance criteria, exact checks, or baseline evidence in the prompt.
Before launch, select and verify the read-only context route for the supplied ID.
If that route uses `bd`, verify installed `bd --help`, command help, and guest context routing with a read-only query.
For a text snapshot, verify guest access, readability, issue identity, and freshness; `bd` is not required.
Do not assume a host tracker is inside the guest mount.
For the recorded Beads 1.3.1 snapshot route, `-C` overrides `BEADS_DIR`; do not add `-C` to that route.
Use only the verified command and routing in the task contract.

When live read-only context is unavailable, use a repository-owned export or text snapshot, or an explicitly authorized disposable reader.
Do not copy or mount the authoritative tracker database or host credentials.
Record snapshot identity, digest or revision, export time, and freshness at launch.
Refresh stale context through the host before relying on it.
Keep claims, tracker state changes, and sync on the host.
If no verified route is available, report the missing prerequisite before launch.

## Check selection

Inspect applicable CI definitions; a local aggregate command can omit required gates.
Use valid repository commands and an explicit `./` test path when the test runner requires it.
For Storagemaxxing, include the CI Knip check in addition to `mise run check`.
Its shared fake `bd` fixture can match command substrings in random paths; preserve the failure and use a bounded isolated recheck.
Leave fixture repair to `sm-ybvb`; do not expand the assigned task to repair it.
