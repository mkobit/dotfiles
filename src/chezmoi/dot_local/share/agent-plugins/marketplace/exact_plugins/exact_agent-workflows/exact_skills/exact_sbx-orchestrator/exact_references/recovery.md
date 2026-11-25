# Progress and recovery

## Durable host task record

Keep the task, scope, authority, baseline, environment, effective sandbox name, clone, branch, prompt, model, verified effort, session, tracker identity and sync procedure, logs, checkpoints, and return paths in a discoverable durable record. Preserve prior logs and use a new log for each resume.

## Incomplete execution

Silence or a disconnect does not prove that a writer stopped. Preserve the sandbox, changes, session, and evidence. Stop on authentication, quota, or unavailable-model errors and report the required action.

## Observe a worker

Record process identity, phase, checks, logs, and exit code. The host may stop active observation while the single guest finishes. Do not assign another unit automatically.

## Resume or replace a worker

Confirm that the previous writer and writable child processes have stopped before resume or replacement. Keep the same run ownership, effective sandbox identity, coordinator model, and saved session. Reconcile the selected issue and native sync, clone and branch, PR, final-head CI, merge, and closure before repeating any side effect. Use native tracker conflict handling. Do not claim a second issue or create a duplicate PR.

After confirmed merge, resume only tracker closure, native sync and read-back, and reporting. Do not repeat implementation, push, or merge. For normal edit/check mode, return the patch and leave delivery and tracker changes to the host. For the pilot, follow the [guest delivery procedure](../../worker-handoff/references/delivery.md).
