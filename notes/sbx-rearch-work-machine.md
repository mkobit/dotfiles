# Work-machine handoff

Use this machine for isolated implementation and review with native subagents.
Real SBX execution is not available here and is not required for the assigned offline work.
Do not install SBX or change host policy to work around that limit.
Keep real sandbox, signing, credential-proxy, and model-endpoint checks pending for the home coordinator.

## Branches and current state

- Integration branch: `feat/sbx-rearch`.
- Draft PR: [#1014](https://github.com/mkobit/dotfiles/pull/1014).
- Handoff and task claim branch: `docs/sbx-rearch-handoff`.
- Work-machine implementation branch: `feat/sbx-rearch-model-routing`.
- Plan: [implementation plan](sbx-rearch-plan.md).
- Progress: [decisions and verification](sbx-rearch-progress.md).

Fetch both remote branches before work.
Use the current remote progress note; do not repeat completed tasks.
The home coordinator owns integration, task 3 repairs, permissions, skills, global task execution, and real SBX checks.
Task 6 model routing is available for work-machine execution under the claim protocol below.
Other repositories and new kit repositories remain follow-up work.

## Claim before implementation

The authoritative record is `notes/sbx-rearch-work-claim.json` on the remote `docs/sbx-rearch-handoff` branch.
Do not use a copied record on an implementation branch as authority.

1. Fetch the handoff branch and create a separate coordination worktree from its current remote head.
2. Read the record. A new claim requires `status == ready` and empty `owner` and `run_id`. Stop for every other state, including a claim with the same machine label.
3. Change `status` from `ready` to `claimed`, set `owner` to `work-machine` or `home`, and add a unique `run_id`.
4. Commit the record with configured signing and push `HEAD:refs/heads/docs/sbx-rearch-handoff` without force.
5. Start implementation only after that push succeeds. A rejected push means another session changed the record; fetch and inspect it before any work.

This normal fast-forward push prevents two sessions from claiming the same task.
Do not rebase a losing claim over another owner's claim or replace an active owner.
The home coordinator can claim the same task if it is still ready when needed.
An interrupted owner keeps the claim until its writer has stopped and its work is recovered or released.
Resume and completion updates require both the saved owner and run ID.
After an uncertain push result, fetch and inspect the remote record; resume only when both identities match the saved claim, and do not create a second claim.

## Task 6 ownership

Read [the model routing brief](sbx-rearch-tasks/model-routing.md).
Own only:

- `src/chezmoi/dot_config/opencode/modify_opencode.json`.
- `src/chezmoi/dot_pi/agent/modify_models.json` and `modify_settings.json`.
- The Pi target gate in `src/chezmoi/.chezmoiignore.tmpl`.
- `src/chezmoi/.chezmoiscripts/run_after_08_configure-local-models.sh.tmpl`.
- `tests/integration/test_ollama_routing.py` and directly related existing OpenCode tests.
- `notes/sbx-rearch-work-machine-report.md` for the handoff report.

Use a separate implementation worktree from the latest `origin/feat/sbx-rearch`.
Do not edit the coordination worktree's source or push code to the integration branch.
Do not depend on uncommitted home-worker files.
Preserve other sessions' changes.

Use native host subagents for the edit, test, repair, and independent review cycle.
Use real Chezmoi rendering with isolated destinations and fake SBX executables.
Do not run the real `sbx` executable or apply settings to the managed work-machine destination.
Do not change the overlay or enable SBX there.

The model hook gate is provider `sbx`, a non-`none` SBX installation method, and `ai.ollama.enabled`.
`ai.workflow.enabled` gates global tasks only.
Absent overlay decisions must remain a no-op.
Declared SBX values must converge on ordinary apply, with unrelated provider and feature metadata preserved.

Write failing behavior tests, implement the minimum change, and run focused tests and Ruff.
Use approved-index tool versions under the repository guidance if the locked tools cannot run on this machine.
Report exact versions; do not change the lockfile or release-age rules.
Keep commits small and signed.
Use an independent reviewer before handoff.

## Return work

Stop all code writers, push `feat/sbx-rearch-model-routing`, and report its commit range.
Open a draft PR with base `feat/sbx-rearch` for the home coordinator to review.
Update the authoritative claim to `ready-for-review` with the branch and head SHA through the same non-force push protocol.
Keep the owner and run identity in the record.
Do not merge the integration PR or close the overall work.

The report must list changed files, tests and exit codes, tool versions, decisions, unresolved questions, active processes, and checks that require the home machine.
Record no-SBX checks as unrun; do not treat them as passed.
The home coordinator reviews the returned diff, resolves shared-file conflicts, and runs real sandbox checks before integration.

## Continuation prompt

```markdown
Continue task 6 for the SBX rearchitecture in mkobit/dotfiles.
Read notes/sbx-rearch-work-machine.md and the current remote progress note.
This work machine cannot execute SBX. Use native host subagents in isolated worktrees and fake-SBX tests under the explicit offline scope in that handoff.
Claim task 6 on origin/docs/sbx-rearch-handoff with a normal fast-forward push before editing source. Stop if another owner has claimed it.
Create feat/sbx-rearch-model-routing from the latest origin/feat/sbx-rearch.
Implement only the files assigned in the handoff and model-routing brief. Do not repeat completed work, edit home-owned files, change an overlay, install SBX, or mutate live settings.
Use separate implementation and independent review delegates. Preserve all other work. Commit verified units with signatures and push the work branch.
Write notes/sbx-rearch-work-machine-report.md, then set the authoritative claim to ready-for-review with the branch and head SHA. Leave native SBX and live endpoint checks for the home coordinator.
```
