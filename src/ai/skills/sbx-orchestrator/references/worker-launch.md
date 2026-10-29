# Worker launch

Choose the coding harness that the repository tracks and validates.
Verify its installed guest executable and help for unattended execution, noninteractive permissions, sessions, resume, and result output.
Use only capabilities that this installed harness supports; do not invent Claude or AGY flags.
Codex below is one tested example, not a required harness.
Keep command text separate from task data and pass prompts as literal arguments.
For an existing environment with unchanged configuration, reuse verified guest context without repeated setup.
If evidence is missing, configuration changed, or execution fails, use installed help and read-only guest probes.
Verify the absolute guest workdir, the guest executable path, and required tool versions.
Report missing tools or an incompatible workspace to the repository configuration owner.
Do not install replacement tools outside the tracked kit.

The host supervisor uses host tools to run `sbx env exec` or `sbx exec`.
This starts a separate coding process in the guest; it does not relocate the host subagent or its tools.
The guest runs repository commands directly and must not launch nested SBX.
For CLI selection, read [CLI automation](../../sbx-sandboxes/references/cli-automation.md).
For missing environments or changed configuration, use [repository setup](../../sbx-sandboxes/references/repository-setup.md).
Use approved task authority for needed task-specific setup without a separate setup confirmation.
Keep actual host platform permissions and do not add unrelated lifecycle actions, credential changes, or publication.
Save the complete prompt, baseline, and launch context in the [durable host record](recovery.md) before launch.

## Codex launcher

Run this launcher on the host, not in the guest.
Set the environment path, guest executable, and absolute workdir from verified evidence.
Set `SBX_SANDBOX_NAME` to the recorded effective sandbox name, including any override used for parallel workers.
Use that same name on every environment command rather than falling back to the configured or derived default.
Set the selected model and the complete [guest task prompt](subagent-task.md).
Set `SBX_TASK_LOG` to a host log path whose parent exists.
The guest report path is separate; a host log path is not a guest mount unless verified.
These examples cover a host-verified worktree whose guest `.git` metadata is outside the mount.
Installed `codex exec --help` and `codex exec resume --help` expose `--skip-git-repo-check` for this case.
Use that flag only after the host verifies the worktree and base; do not mount host Git metadata.
Omit the flag when the guest has valid Git metadata and the check is appropriate.

```sh
environment="${SBX_ENVIRONMENT:?Set SBX_ENVIRONMENT to the selected environment path}"
sandbox_name="${SBX_SANDBOX_NAME:?Set SBX_SANDBOX_NAME to the recorded effective sandbox name}"
agent_executable="${CODEX_EXECUTABLE:?Set CODEX_EXECUTABLE to the verified guest executable}"
guest_workdir="${SBX_GUEST_WORKDIR:?Set SBX_GUEST_WORKDIR to the verified guest workdir}"
model="${CODEX_MODEL:?Set CODEX_MODEL to the selected task model}"
prompt="${SBX_TASK_PROMPT:?Set SBX_TASK_PROMPT to the implementation task}"
task_log="${SBX_TASK_LOG:?Set SBX_TASK_LOG to the host log path}"
if sbx env exec --name "$sandbox_name" "$environment" -- sh -c \
  'cd "$2" && exec "$1" exec --model "$3" --disable hooks --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check "$4" </dev/null' \
  sbx-codex "$agent_executable" "$guest_workdir" "$model" "$prompt" >"$task_log" 2>&1; then
  status=0
else
  status=$?
fi
printf 'Worker exit code: %s\nHost log: %s\n' "$status" "$task_log"
(exit "$status")
```

The executable, workdir, model, and prompt pass as positional arguments without shell evaluation of their contents.
`--disable hooks` disables inner Codex hooks, and `</dev/null` closes inner stdin.
`--dangerously-bypass-approvals-and-sandbox` permits the authorized guest edit, check, and repair loop.
Both flags apply only to the inner guest process; never apply them to a host coding process.
The launcher captures stdout and stderr in the host log and returns the worker exit code.
A nonzero exit is evidence, not permission to discard changes or start another writer.
For host approval boundaries, read [permissions](../../sbx-sandboxes/references/permissions.md).

## Codex resume example

First load the durable record and complete the ownership and source checks in [recovery](recovery.md).
Confirm that the previous writer and child checks stopped before invoking resume.
Use the recorded session ID, not an unverified most-recent session.
Set `SBX_SANDBOX_NAME` to the same recorded effective sandbox name used at launch, including any override.
Set a new host log path so previous evidence is not overwritten.
Keep the recorded model unless a model change is explicitly authorized.

```sh
environment="${SBX_ENVIRONMENT:?Set SBX_ENVIRONMENT to the verified environment path}"
sandbox_name="${SBX_SANDBOX_NAME:?Set SBX_SANDBOX_NAME to the recorded effective sandbox name}"
agent_executable="${CODEX_EXECUTABLE:?Set CODEX_EXECUTABLE to the verified guest executable}"
guest_workdir="${SBX_GUEST_WORKDIR:?Set SBX_GUEST_WORKDIR to the verified guest workdir}"
model="${CODEX_MODEL:?Set CODEX_MODEL to the recorded task model}"
prompt="${SBX_TASK_PROMPT:?Set SBX_TASK_PROMPT to the reconciled continuation task}"
session_id="${SBX_SESSION_ID:?Set SBX_SESSION_ID to the recorded guest session}"
task_log="${SBX_TASK_LOG:?Set SBX_TASK_LOG to a new host log path}"
if sbx env exec --name "$sandbox_name" "$environment" -- sh -c \
  'cd "$2" && exec "$1" exec resume --model "$3" --disable hooks --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check "$5" "$4" </dev/null' \
  sbx-codex "$agent_executable" "$guest_workdir" "$model" "$prompt" "$session_id" >"$task_log" 2>&1; then
  status=0
else
  status=$?
fi
printf 'Worker exit code: %s\nHost log: %s\n' "$status" "$task_log"
(exit "$status")
```

The session ID and continuation prompt also pass as literal positional arguments.
Use installed help for supported JSON events or final-message output if the task needs them.
Record the selected output paths and session identity in the host record.
Do not use ephemeral session storage when later session recovery is required.
