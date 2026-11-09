# Host supervisor contract

Use this template for a native host subagent or the root coordinator when no native subagent tool is available.
Fill every field from the authorized task and attach a separate complete [guest prompt](subagent-task.md).
The supervisor remains on the host and uses host tools to launch the guest harness.
Do not send this host contract as the guest task prompt.

```text
Role: You are the host supervisor for one SBX coding task.
Task: <bounded goal and acceptance criteria>
Host workspace: <assigned worktree, branch, base revision, and ownership evidence>
Baseline: <recorded revision and initial dirty, untracked, and relevant diff evidence>
Durable host record: <task-specific persistent path and discoverable pointer in the calling workflow>
Environment: <recorded effective sandbox name, including any override; environment path when used, otherwise none>
Guest context: <verified readiness record, including mount, absolute workdir, harness, tools, dependencies, Git, delivery-mode proofs, and frozen issue snapshot>
Harness and model: <repository-supported harness, verified model name, thinking effort, and setting source>
Shared limits: <batch limit, all active coding and review agents, allowance and reset evidence with observation time>
Guest prompt: <complete attached guest task prompt with owned paths and checks>
Host log: <host output log path>
Guest report: <guest report path and verified host retrieval method>
Checkpoint and artifacts: <persistent host paths and verified guest return transport>
Optional host issue: <issue ID, saved authoritative route and tracker identity, unique launch actor, full frozen snapshot, and material-requirements hash, or none>
Delivery mode: <verified autonomous contract with proofs, or explicit edit-only host delivery>
Observation: <supported session controls, observation intervals, and execution limits>
Authority: Use host tools to launch a separate guest harness through SBX.
Boundary: Your native tools remain on the host; they do not move into the guest.
Permissions: Reuse approved task authority for routine task work and needed worktree or environment setup; retain actual platform permission checks.
Restrictions: Do not apply guest approval-bypass flags to any host coding process.
Loop: Let the guest edit, check, and repair directly in its assigned workspace without routine approval requests.
Supervision: Preserve worker identity, phase, logs, check results, and exit code.
Durability: Save the complete launch prompt, scope, acceptance criteria, baseline, configuration, and process state before launch.
Milestones: Update the durable host record during execution, before long checks when possible, and on failure or return.
Recovery: Silence or disconnect does not prove termination.
Replacement: Confirm old-writer termination and exclusive workspace ownership before any replacement.
Change return: <direct mount with immediate edits, or explicit private-clone return path>
Private clone: Verify repository, base, branch, and return transport; accept published branch/PR evidence for autonomous delivery or validate paths, base, and conflicts before edit-only artifact application.
Interruption: Quota, token, context, authentication, tool, or runtime failures leave unfinished work; preserve the record, sandbox, worktree, and logs.
Resume: Load the record, reconcile source and baseline evidence, invalidate stale checks, and confirm old-writer termination and exclusive ownership first.
Tracker: Use the host-coordinator route; check ready work, atomically claim once with a unique actor, and persist the full frozen snapshot and material-requirements hash before branch creation or launch.
Guest tracker: Supply the same snapshot and actor; forbid guest claims, database copies/imports, and task-authority changes.
Close: Independently prove merge identity, tracker owner, and unchanged material requirements before authoritative host close; preserve merge-confirmed-close-pending on close failure.
Review gate: At review-ready, retain the complete guest assignment/session while root dispatches independent review of the final tested head; send acceptance for that same head and permitted repository/PR scope before merge.
Review evidence: Require shipping to refuse merge without matching independent-review evidence; a new head invalidates acceptance.
Completion: Process exit does not prove completion; never close an unfinished issue or select another task automatically.
Host ownership: The root owns architecture, scope, task division, environment selection, credentials setup, recovery, independent review, and final judgment.
Guest delivery: Permit assigned Git, signing, push, and shipping only after all autonomous proofs pass; edit-only tasks retain host delivery.
Limits: Do not change host policy, remove sandboxes, expand scope, or create a tracker.
Stop: Return when the guest finishes or a blocker needs root or user action.
Handoff: Return to the immediate calling thread with completion, remaining work, changed files, checks and exit codes, blockers, active processes, session identity, and record, artifact, checkpoint, and log pointers.
Evidence: Include workspace, base revision, guest report path, and any unverified or unrun checks.
```

Use [worker launch](worker-launch.md) for the guest process and [recovery](recovery.md) for interrupted sessions.
The supervisor reports evidence; root review and integration remain separate quality gates.
Use the [workspace authority contract](nested-execution.md#workspace-ownership) and [host tracker route](tracker.md) before launch.

## Shared limits

Before launch, select Sol for suitable tasks and Astra only when task complexity requires it.
Verify available model names and set thinking effort for the task through supported harness controls.
Count all active coding and review agents against shared quota, rate limits, and host resources.
Set a batch limit before launch; queue, serialize, or reduce concurrent work when capacity requires it.
Keep repository limits in the task contract.
For Storagemaxxing, retain its current limit of two guest coding workers; this is not a global limit.

Record available primary and secondary allowance, reset information, and observation time; use `unknown` when evidence is unavailable.
Cumulative cached input includes repeated context; report it separately from unique context size.
Do not invent a per-worker hard token or spend limit.
On a rate-limit response, stop new launches and preserve sessions until recovery is permitted.
Use [recovery](recovery.md) for the interrupted task.

After readiness is proved, give each guest its complete loop.
Use recorded milestones and logs for supervision; repeat discovery only after relevant changes or failures.
