# Overlay collaboration

Use `mkobit/dotfiles:feat/sbx-rearch` as the shared, long-lived feature branch.
Keep the plan, progress, decisions, questions, verification, and manual follow-up work in `notes/` on that branch.
Continue review through [draft PR #1014](https://github.com/mkobit/dotfiles/pull/1014).
Keep the shared feature branch and draft PR open while base and overlay collaboration continues.

## Shared context

- [Plan](sbx-rearch-plan.md)
- [Progress and decisions](sbx-rearch-progress.md)
- [Manual follow-up work](sbx-rearch-follow-ups.md)
- [Task briefs and reports](sbx-rearch-tasks/)

An overlay session can read the [current shared progress](https://github.com/mkobit/dotfiles/blob/feat/sbx-rearch/notes/sbx-rearch-progress.md) through approved read-only GitHub access when no base checkout is available.
Use the base repository's feature branch for base changes.
Keep assigned overlay-specific changes in the overlay repository and record the related base commit.
Do not copy base implementation files into the overlay to share context.

## Work-machine execution

Real SBX execution is unavailable on the work machine.
Use native host subagents for assigned implementation, testing, repair, and independent review in isolated worktrees.
Use real Chezmoi rendering with isolated destinations and fake SBX executables.
Do not install SBX, enable it in the overlay, change host policy, or mutate live settings for these tests.
Keep real sandbox, signing, credential-proxy, and model-endpoint checks pending for a machine that supports them.

Respect the overlay's control plane and safe defaults.
Missing sandbox decisions must make no changes.
Any intended SBX setting mutation must be represented in Chezmoi source and tested for convergence on ordinary apply.
Use approved-index tool versions under the repository guidance if locked tools cannot run; record exact versions without changing the lockfile or release-age rules.

## Collaboration rules

Read the latest shared progress before starting a unit.
Record who owns the unit and its files in the shared progress note before parallel edits.
Preserve other sessions' work and do not repeat completed or active tasks.
Commit small verified units with configured signing and keep the progress and evidence current.

Integrate remote changes at a stopped-worker checkpoint.
Use ordinary fast-forward pushes; if the remote has changed, fetch, review, and reconcile unpublished work before retrying.
Do not force-push or rewrite published history.
Dispatch an independent reviewer for each unit and retain unresolved findings in the notes.
The separate cross-machine handoff and Git claim procedure is superseded by this shared-branch workflow.

## Overlay-session prompt

```markdown
Collaborate on the existing SBX rearchitecture through mkobit/dotfiles:feat/sbx-rearch and draft PR #1014.
Read the current plan, progress, decisions, task briefs, and follow-up notes from that shared branch. If the base checkout is unavailable, read https://github.com/mkobit/dotfiles/blob/feat/sbx-rearch/notes/sbx-rearch-progress.md through approved read-only GitHub access.
This work machine cannot run SBX. Use native host subagents in isolated worktrees, real Chezmoi rendering with temporary destinations, and fake-SBX tests for assigned offline work. Do not install or enable SBX or change live settings here.
Coordinate unit and file ownership in the shared progress note. Preserve active work and do not repeat completed tasks. Keep base changes on the shared base feature branch and assigned overlay changes in the overlay repository.
Commit small verified units with signatures, use independent reviewers, and update the shared notes with commands, results, exact tool versions, decisions, questions, and unrun runtime checks. Integrate remote changes only after local writers stop. Use normal fast-forward pushes and preserve published history.
Continue through the current incomplete plan. Keep real SBX and live endpoint verification pending for a capable machine, and retain all manual follow-up work in notes/.
```
