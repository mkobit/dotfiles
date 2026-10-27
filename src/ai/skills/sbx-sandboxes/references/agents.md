# Agents

Choose the harness the repository tracks and validates.

Codex, Claude, and AGY environment templates all include the repository `./kit` and direct-mounted workspaces.

## Codex execution

Run this launcher on the host for an existing repository environment.
Reuse verified guest workspace, executable, and tool-version evidence when the environment is unchanged.
If evidence is missing, relevant configuration changes, or execution fails, use installed help and read-only guest probes to verify the assigned workdir, agent executable, and required tool versions.
Keep related edits and checks in this verified workspace and tool context.
Report missing tools or an incompatible workspace to the repository configuration owner; do not install replacements outside the tracked kit.
Set `CODEX_EXECUTABLE` to the verified guest executable path and `SBX_GUEST_WORKDIR` to the verified absolute guest workdir.
Set `CODEX_MODEL` to the selected task model and `SBX_TASK_PROMPT` to the task context, file scope, acceptance criteria, required checks, and task log location.

```sh
agent_executable="${CODEX_EXECUTABLE:?Set CODEX_EXECUTABLE to the verified guest executable}"
guest_workdir="${SBX_GUEST_WORKDIR:?Set SBX_GUEST_WORKDIR to the verified guest workdir}"
model="${CODEX_MODEL:?Set CODEX_MODEL to the selected task model}"
prompt="${SBX_TASK_PROMPT:?Set SBX_TASK_PROMPT to the implementation task}"
sbx env exec .sbx/sbxenv.yaml -- sh -c \
  'cd "$2" && exec "$1" exec --model "$3" --disable hooks --dangerously-bypass-approvals-and-sandbox "$4" </dev/null' \
  sbx-codex "$agent_executable" "$guest_workdir" "$model" "$prompt"
```

The executable, workdir, model, and prompt pass as positional arguments, without shell evaluation of their contents.
The Codex flags permit edits and checks inside SBX without nested approval prompts.
`--disable hooks` disables Codex hooks and `</dev/null` closes stdin for unattended execution.
These flags apply to the inner Codex process; they do not change host permissions.
Save detailed command output in the task log and preserve the exit status.

## Progress and session recovery

Continue related edits, checks, and repairs in the same worker session when the installed harness supports it.
Use supported harness controls for task-specific observation intervals and execution limits; do not assume a fixed stall timeout or resume syntax.
Preserve the log path, session identity when available, workspace and base revision, current phase, active check, and last completed check with its exit code.
Silence alone does not prove a stall; inspect logs and process or check state before intervention.
Before replacing a worker, confirm that the old writer has stopped and preserve its changes and check results.
If exclusive ownership or supported session recovery cannot be established, return the blocker without starting another writer.
Report a disconnect or resume case as verified only after executing it.

## Task feedback

The guest returns friction, user confusion, and frustration in its existing handoff.
Include expected and actual behavior, revision, source instruction, and relevant evidence without credentials; separate observations from suspected causes.
The authorized host coordinator updates the existing owning record only when the workflow uses a tracker.
Guest feedback does not authorize writes to the host tracker or a copied database.
Without a tracker, keep feedback in the handoff; do not require Beads or create a tracker.
Link a proposed instruction correction to an acceptance example and verify the revised prompt in its intended environment before claiming that it works.

## AGY setup

Use AGY only through a repository `.sbx/sbxenv.agy.yaml` environment.

Before creating an AGY environment, inspect `sbx settings get kit.allowedSources`.

The AGY contrib kit needs the narrow `github.com/docker/` source prefix.

Require confirmation before changing that setting when the session authorization does not already cover it.

The setting replaces the complete allowlist, so preserve existing approved entries while adding the required prefix.

If SBX cannot resolve `agent: antigravity`, stop and report the preflight output rather than falling back to a host launcher.

The first AGY run can require a user-completed Google OAuth flow through Docker’s credential proxy.

Keep commits, signing, and pushes on the host.
