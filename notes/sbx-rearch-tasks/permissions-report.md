# Permission implementation verification

Task 4 adds selected GitHub, Git push, and named mise task grants through the existing command catalog.
It preserves unrelated live rules, explicit removals, native denials, and selective SBX grant retirement.
Catalog ask removes an exact old catalog grant unless current per-tool configuration explicitly ensures it.
Catalog deny wins.

Codex keeps compatible modern or legacy sandbox selectors.
The host uses on-request approval and workspace write access.
The separate private unattended profile uses never approval and full access, with target mode `0600`.
It is not selected as the host default.
Matching base input remains byte-for-byte unchanged.

No parent-directory denial that blocks ordinary workspace access was added.
Host rules do not provide complete filesystem isolation.

## Evidence

- Renderer gate: 86 passed, 33 deselected; exit 0.
- Ruff lint and format: passed.
- Independent review: no blocking task 4 defect found.
- Full six-file command: 111 passed, 1 skipped, 2 failed, 5 setup errors; exit 1.
- The full-command failures concern absent guest Claude/AGY target files and missing installation-method data, not hidden or weakened tests.
- No live apply, settings mutation, tool installation, credential change, or active worker remained at handoff.

Full initialized deployment and CI remain required before final integration approval.
Local prompts, logs, hashes, and exact command records are under `.sbx/task-context/permissions/`.

## Existing matching limit

The existing AGY renderer escapes literal heads without choosing regex mode.
No current base catalog head or newly selected head has a regex metacharacter.
An overlay head such as `./check` needs a separate matching correction and native-client test.
Keep that compatibility issue visible for overlay collaboration and final review.
Source: [AGY permission matching](https://antigravity.google/docs/permissions/#supported-cli-actions-and-matching-rules).
