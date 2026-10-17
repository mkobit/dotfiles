# Subagent task

Use this specification with the host's available delegation tool.
Fill the fields from the authorized task, then use the harness in [Agents](agents.md).
The coordinator keeps branch management, credentials, commits, signing, and publication on the host.

```text
Task: <bounded implementation goal>
Environment: <repository environment path or existing sandbox name>
Harness and model: <repository-supported agent; selected model if supported>
Owned files: <explicit paths or modules>
Other agents: You are not alone; preserve others' edits and adapt to them.
Acceptance criteria: <observable required behavior>
Checks: <required build, test, and lint commands>
Log location: <task log path>
Execution: Use sbx only for sandbox operations.
Loop: Edit owned files, run the required checks, and fix failures within scope.
Stop: Return when criteria pass, or when a blocker needs host or user action.
Do not expand scope, change host policy, remove sandboxes, or publish changes.
Handoff: List changed files, checks and exit codes, remaining blockers, and log location.
```

Use a direct-mounted workspace for immediate host review.
With a private clone, include the explicit change-return process from [Nested execution](nested-execution.md).
An authentication failure follows [Authentication](authentication.md); it does not authorize host credential changes.
