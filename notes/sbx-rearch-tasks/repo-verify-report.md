# Repository verification checkpoint

Adds real `check`, `test:workflow`, `test`, and `verify` tasks plus seven explicit required CI names in `.agent-workflow.json`.
Each task sets `UV_FROZEN=1`.
The build depends on successful checks and tests.
Lockfiles, tool versions, and release-age controls are unchanged.

Fifteen command-stub cases passed through actual Mise execution, including command counts, order, frozen resolution, and failure handling.
Dry-run and policy checks passed.
The full real run passed lint, format, types, workflow tests, and 454 package tests.
One existing termstatus timing test failed: P99 measured `929.58 ms` against `<200 ms`.
That failure blocked the build as required.

After recovery with no old writer and guest load `0.00`, the single failed-case retry passed in `2.34 s`.
It selected the package's pytest configuration rather than the original repository configuration, so the pass does not establish the cause.
The previously blocked build then passed through `mise run --skip-deps verify`, producing all eight packages.
No threshold, unrelated source, or test exclusion was changed.
One complete verification run with the repository configuration remains required.

Independent source review found no material defect in the task graph or check names.
Source hashes: `mise.toml` is `a6f55bb6abd29aa8cc6e6c96e0d6756ebd3ba346b3eb6089215a11a742babba3`; `.agent-workflow.json` is `b0ee6c74a4b760dae448ce5f188b569313d0706addba0f51604bf18ef1874f5f`.
Local evidence is in `.worktrees/feat-sbx-rearch-verify/.sbx/task-context/repo-verify/`.
The shared branch receives the reviewed two-file snapshot; the execution worktree remains preserved.

The task list starts from `6711c42f`.
Add the now-existing `test_ollama_routing.py` to `test:workflow` in the next bounded task update, then add helper tests when implemented.
Global workflow commands and their helper are still pending.
