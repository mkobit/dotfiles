# Subagent task

Use this specification with the host's available delegation tool.
Fill the fields from the authorized task; the host uses the launcher in [Agents](agents.md).
The coordinator keeps branch management, credentials, commits, signing, and publication on the host.

```text
Task: <bounded implementation goal>
Environment: <repository environment path or existing sandbox name>
Guest context: <verified absolute workdir, agent executable, required tool versions, and evidence reference>
Harness and model: <repository-supported agent; selected model if supported>
Owned files: <explicit paths or modules>
Other agents: You are not alone; preserve others' edits and adapt to them.
Acceptance criteria: <observable required behavior>
Checks: <required build, test, and lint commands run directly in the guest>
Log location: <task log path>
Progress: <task-specific observation intervals and execution limits supported by the harness>
Execution: Select the verified guest workdir and run repository commands directly; do not launch nested SBX or move checks to the host.
Loop: Edit owned files, run required checks, and repair failures within scope in the same supported session.
Stop: Return when criteria pass, or when a blocker needs host or user action.
Do not expand scope, change host policy, remove sandboxes, or publish changes.
Handoff: Return workspace and base revision, session identity if available, current phase, changed files, last completed check, active or failed check, exit codes, blocker state, and log location.
Feedback: Return expected and actual behavior, revision, source instruction, and evidence for friction; the authorized host updates an existing tracker only if used.
```

Use a direct-mounted workspace for immediate host review.
With a private clone, include the explicit change-return process from [Nested execution](nested-execution.md).
An authentication failure follows [Authentication](authentication.md); it does not authorize host credential changes.
