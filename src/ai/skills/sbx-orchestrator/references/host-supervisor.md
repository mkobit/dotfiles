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
Environment: <existing environment path and recorded effective sandbox name, including any override>
Guest context: <verified absolute workdir, agent executable, required tool versions, and evidence reference>
Harness and model: <repository-supported harness and selected model if supported>
Guest prompt: <complete attached guest task prompt with owned paths and checks>
Host log: <host output log path>
Guest report: <guest report path and verified host retrieval method>
Checkpoint and artifacts: <persistent host paths and verified guest return transport>
Optional host issue: <supplied issue ID and verified tracker location, or none>
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
Private clone: Verify the base and return transport before launch; deliver artifacts to the root-owned feature worktree after host path, base, and conflict checks.
Interruption: Quota, token, context, authentication, tool, or runtime failures leave unfinished work; preserve the record, sandbox, worktree, and logs.
Resume: Load the record, reconcile source and baseline evidence, invalidate stale checks, and confirm old-writer termination and exclusive ownership first.
Tracker: If a host issue was supplied, pass its context to the guest and let the authorized host update that issue after review.
Completion: Process exit does not prove completion; never close an unfinished issue or select another task automatically.
Host ownership: The root coordinator owns review, branch changes, credentials, commits, signing, publication, and live deployment.
Limits: Do not change host policy, remove sandboxes, expand scope, or create a tracker.
Stop: Return when the guest finishes or a blocker needs root or user action.
Handoff: Return to the immediate calling thread with completion, remaining work, changed files, checks and exit codes, blockers, active processes, session identity, and record, artifact, checkpoint, and log pointers.
Evidence: Include workspace, base revision, guest report path, and any unverified or unrun checks.
```

Use [worker launch](worker-launch.md) for the guest process and [recovery](recovery.md) for interrupted sessions.
The supervisor reports evidence; root review and integration remain separate quality gates.
