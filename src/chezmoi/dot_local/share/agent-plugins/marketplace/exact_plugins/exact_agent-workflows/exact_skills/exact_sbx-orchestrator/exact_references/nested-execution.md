# Change return and handoff

## Workspace ownership

The guest works only in its assigned workspace. Do not launch nested sandboxes. For normal edit/check mode, define patch or artifact transport before launch, including binary files, untracked files, and deletions. The host verifies the base and conflicts, reviews changes, and owns delivery and tracker updates.

For an explicitly assigned pilot, use a private clone with valid Git metadata. Signed pushed commits and the PR are the change return path. Record the branch, PR, final head, merge, and guest tracker closure in the host record. Follow [delivery](delivery.md).

## Required final handoff

Report completion and acceptance evidence, changed files, exact checks and exit codes, failures and skips, blockers, active processes, session identity, logs, workspace and base, and recovery pointers. Report unrun checks and preserve failed results. Do not claim completion from process exit alone.

## Task delivery

For normal edit/check mode, the host reviews the returned patch and performs authorized delivery and tracker changes. For explicitly assigned pilot delivery, the guest follows the [canonical procedure](../../worker-handoff/references/delivery.md) without a routine host acceptance pause. Preserve evidence before any authorized cleanup.
