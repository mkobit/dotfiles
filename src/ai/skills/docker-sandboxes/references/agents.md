# Agents

Choose the harness the repository tracks and validates.

Codex, Claude, and AGY environment templates all include the repository `./kit` and direct-mounted workspaces.

## Codex execution

Use this tested fallback for an existing environment in this repository.
Set `CODEX_MODEL` to the selected task model and `SBX_TASK_PROMPT` to the claimed bead context, file scope, acceptance criteria, required checks, and task log location.

```sh
model="${CODEX_MODEL:?Set CODEX_MODEL to the selected task model}"
prompt="${SBX_TASK_PROMPT:?Set SBX_TASK_PROMPT to the implementation task}"
sbx env exec .sbx/sbxenv.yaml -- sh -c \
  'exec codex exec --model "$1" --disable hooks --dangerously-bypass-approvals-and-sandbox "$2" </dev/null' \
  rulette-codex "$model" "$prompt"
```

The model and prompt pass as positional arguments, without shell evaluation of their contents.
The Codex flags permit edits and checks inside SBX without nested approval prompts.
`--disable hooks` disables Codex hooks and `</dev/null` closes stdin for unattended execution.
These flags apply to the inner Codex process; they do not change host permissions.
Save detailed command output in the task log and preserve the exit status.

## AGY setup

Use AGY only through a repository `.sbx/sbxenv.agy.yaml` environment.

Before creating an AGY environment, inspect `sbx settings get kit.allowedSources`.

The AGY contrib kit needs the narrow `github.com/docker/` source prefix.

Require confirmation before changing that setting when the session authorization does not already cover it.

The setting replaces the complete allowlist, so preserve existing approved entries while adding the required prefix.

If SBX cannot resolve `agent: antigravity`, stop and report the preflight output rather than falling back to a host launcher.

The first AGY run can require a user-completed Google OAuth flow through Docker’s credential proxy.

Keep commits, signing, and pushes on the host.
