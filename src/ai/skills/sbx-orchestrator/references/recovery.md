# Progress and recovery

Continue related edits, checks, and repairs in the same guest session when the installed harness supports it.
Use supported controls for task-specific observation intervals and execution limits.
Do not assume a fixed stall timeout or resume syntax.
Measure duration and detect stalls using monotonic time, check logs, and active process status.
Do not conclude that a worker is stalled from file timestamps or wall clocks.
Preserve session identity when available, workspace, base revision, phase, active check, last completed check, exit codes, and log location.

## Durable host task record

Before launch, save a task-specific record in a persistent host location used by the calling workflow.
Keep a discoverable pointer in the existing task or workflow context so a later host session can find it.
Do not rely only on guest memory, final output, temporary logs, or a tool session handle.
No global schema, tracker, scheduler, update script, or process framework is required.

Record the complete task and launch prompt, owned scope, and acceptance criteria.
Record sandbox identity, the assigned worktree or private clone and base identity, and relevant configuration.
Record the installed harness, selected model and thinking effort, session identity, and log, checkpoint, and artifact paths.
Record pending host operations, including launch calls, with their known state and evidence.
Preserve initial revision, dirty-state, untracked-file, and relevant diff evidence before the guest writes.
Record known task changes separately from this baseline so later edits can be attributed.
Include completed and required checks with exit codes, remaining work, exact failures, and last known worker and child-check state.
Include the supplied host issue ID and verified tracker location only when the existing workflow provides them.

Update the record at launch, observed milestones, interruptions, and return.
Before long checks or a possible abrupt exit, preserve the latest known changes, phase, and check state when possible.
The host owns these updates; guest progress supplies evidence but is not the only durable copy.

## Incomplete execution

Quota, token, context, authentication, tool, and runtime failures produce resumable incomplete work.
Process exit, including exit zero, does not by itself prove task completion.
Record the exact failure, remaining work, verified results, and unknown or incomplete checks.
Do not mark unknown checks as passed or close an unfinished issue.
Do not rapid-retry quota failures or silently change model, account, or credentials.
Preserve the sandbox, worktree, checkpoint, and logs; do not automatically remove or rebuild them.
Return incomplete status and durable evidence pointers to the immediate calling thread.

## Observe a worker

Observe existing sessions and mounted logs before more probes or dispatch.
Inspect the captured log and supported process or check state before intervention.
Resolve a pending launch call and record whether it started a writer before another launch.
A missing client handle is not proof that the launch failed.
Silence alone does not prove a stall.
A reported daemon restart alone does not prove writer or child-process termination.
Inspect `sbx list` and supported process or session state.
If observation needs a sandbox start, start only the recorded environment without launching a writer.
Verify mounted worktrees and artifacts, then follow the termination and ownership gate below before resume.
A disconnected client can leave the guest worker or a child check running.
Preserve the existing task evidence and determine whether the original writer is still active.
Reconnect only with supported observation controls; do not start a resumed writer while an old writer can still run.
Do not claim that disconnect or recovery was tested unless it was executed.

## Resume or replace a worker

A later host session first loads the durable task record through its recorded discovery pointer.
Verify mount mapping, assigned worktree or clone, revision, current diff, and relevant configuration.
Reconcile current source changes against the recorded initial baseline and known previous task changes.
Do not assume the base or source stayed unchanged after other writers or later edits.
Keep checks stale after relevant source changes until required checks run again.

Confirm that the old writer and any child process that can write have stopped before replacement.
Use supported process or session state as termination evidence; silence or disconnect is not evidence.
A missing host tool session also does not prove that the guest stopped.
Preserve changes, logs, completed check results, and the last known phase.
Confirm exclusive ownership of the assigned workspace before a new writer starts.
If termination, ownership, or supported recovery cannot be confirmed, return a blocker without starting another writer.
Do not use sandbox removal or recreation as an automatic recovery action.

Only after termination and exclusive ownership are confirmed, use installed harness-supported resume with the recorded session identity.
If resume is unsupported, build one complete new [guest prompt](subagent-task.md) from the reconciled checkpoint.
Do not start a second active writer.
Run required checks after resumed edits and record their current exit codes.
Keep host permissions unchanged and do not ask the guest for routine edit or check approval.
Report any still-active process in the [final handoff](nested-execution.md).
