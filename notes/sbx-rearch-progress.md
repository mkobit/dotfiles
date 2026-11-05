# SBX workflow progress

Plan: [Implementation plan](sbx-rearch-plan.md).
Branch: `feat/sbx-rearch`.
Base: `7aa2fb19`.
Workspace: `.worktrees/feat-sbx-rearch`.

## Resume here

Use `feat/sbx-rearch` as the shared long-lived base feature branch.
[Draft PR #1014](https://github.com/mkobit/dotfiles/pull/1014) contains the published checkpoints.
Tasks 1–3 have reviewed implementation commits.
The macOS ancestor-alias repair and task 4 passed all seven CI checks at `d54ded96`.
Task 4 is complete after initialized Linux amd64/arm64 and macOS deployment checks.
Task 5a is signed and published at `6711c42f` after fresh scenario evaluation and independent re-review.
Its scope is the SBX skill authority references, `worker-handoff`, its catalog entry, and related tests.
The repaired version passed 76 focused tests and 42 broader deployment tests before a description-only correction.
Final static checks passed after that correction; the extra full test attempt stopped at quota and is incomplete.
The fixed application cases score 10 of 10, and both independent findings are resolved.
Local record: `.sbx/task-context/skills-worker/`.
Task 6 model routing is signed at `e43691a9`; all seven CI checks passed in run `41777701533`.
The architect skill passed 25 deployment tests, final static checks, a fresh application case, and independent review.
The repository verification tasks and required-check configuration are included in this departure checkpoint.
Their full local run has one unresolved existing timing failure; its narrower retry and the blocked build passed.
See [the verification limit](sbx-rearch-tasks/repo-verify-report.md) before claiming a full pass.
The previous coding guests stopped before source recovery.
The `repo-bootstrap` skill is included in this checkpoint after 39 deployment tests, static checks, and independent review.
See [the bootstrap report](sbx-rearch-tasks/bootstrap-skill-report.md) for the temporary test-environment limit.
The global bootstrap command and other task 7 code remain pending.
No next implementation unit is assigned on this machine.
The overlay work machine can use native subagents and fake-SBX tests for coordinated offline work.
Real sandbox and live endpoint checks require a capable machine.
See [the collaboration guide](sbx-rearch-work-machine.md).
One skill, global workflow commands and helper, deployment, and final verification remain.

### Continue from the work machine

Pull `feat/sbx-rearch` and read this section first.
Five of nine main plan items are complete; the workflow helper is the largest remaining item.
The remaining skill is `retro-self-improve`.
Then implement task 7's global commands and helper in the bounded units from [the corrected contract](sbx-rearch-tasks/task7-refinement.md).
Those source units are open for work-machine assignment after recording file ownership here.
Use native host subagents, temporary Chezmoi destinations, and fake SBX tests as authorized in [the collaboration guide](sbx-rearch-work-machine.md).
Keep real SBX, signing/proxy, clone transport, local-model lifecycle, and live endpoint checks for a capable machine.
Respect [the native model interface limit](sbx-rearch-tasks/env-model-contract.md); no environment model flags are supported.
Update the explicit verification test list for the now-available model tests and later helper tests.
Keep the shared branch and draft PR open.
For this checkpoint, the user requested quota conservation with 18% of the weekly quota left.
Keep the next offline units on the work machine and reserve native verification for this machine.

## Decisions

- Use the design note as the authorized implementation scope.
- Keep map-based command and authored-skill catalogs; the proposed arrays duplicate existing overlay controls.
- Verify CLI examples before implementation: installed Codex has no `--full-auto`; Beads close uses `--reason`.
- Use atomic Beads claims and preserve the caller directory in global mise tasks.
- Keep a tracked checklist because this repository has no `.beads/`.
- Do not generate signing keys, export private keys, or change account credentials during apply.
- A guest that must commit needs usable Git metadata; a mounted linked worktree does not provide this automatically.

## Evidence

- Three read-only delegates audited configuration, SBX, and task support.
- SBX version: `0.50.1`.
- The current root checkout is `main`; implementation has a separate feature worktree.
- Worktree creation required platform approval because Git metadata is read-only in the sandbox.

## Human questions

No product question is pending after the first audit.
Record any new questions here and present them together when they block implementation.

## Baseline checks

- `mise exec -- uv run --frozen pytest tests/integration/test_sbx.py tests/integration/test_sbx_command_retirement.py tests/integration/test_mise.py -q`: 45 passed in 35.61 seconds on base `7aa2fb19`.
- The first test attempt could not write the uv cache; the approved host retry passed.
- Approved `sbx diagnose`: 16 passed, 0 failed, 2 expected skips.
- Earlier SBX database errors came from restricted host access; the daemon did not need repair.
- The plan review found no blocking product question.
- Shared interfaces: `ai.workflow.enabled`, `ai.sandbox`, `ai.signing`, `ai.ollama`, and existing `sbx.settings.skills_default_mode`.
- Required-check configuration must be explicit or obtained from branch requirements; missing checks must prevent automatic merge.

- `gh api repos/mkobit/dotfiles/branches/main/protection/required_status_checks` returned HTTP 404, `Branch not protected`.
- Automatic PR merge therefore needs a tracked, nonempty required-check list for dotfiles.

## Task 2 launch

- Host supervisor: `implement_config`.
- Guest environment: `.sbx/sbxenv.yaml`, effective name `dotfiles-sbx-rearch`.
- Guest workspace: the feature worktree, direct mounted.
- Guest Codex: `/home/agent/.local/bin/codex`, version `0.165.0`.
- Selected model: `gpt-6.1-sol`; reasoning effort: `high`.
- Batch limit: one guest coding worker; allowance and reset data: unknown.
- Scope: workflow catalog, personal opt-ins, and schema tests only.
- Guest commits are disabled for this migration task; root signs reviewed commits on the host.
- Prompt, baseline, and launch evidence: `.sbx/task-context/config/` (local runtime records).
- Guest toolchain setup is in progress; missing mise and Chezmoi currently prevent tests.

## Environment checks

- Repository kit validation, guest shell syntax, and tool probes passed.
- Guest tools: mise `2026.10.23`, uv `0.12.10`, Chezmoi `2.74.0`, Python `3.14.7`.
- Guest dependencies use `/home/agent/.local/share/dotfiles/venv`; host `.venv` is not shared.
- The first task launch exited 125 on a Docker login-store lock before a writer started.
- The supervisor proved that no old writer remained, then retried successfully.
- Active guest session: `01a19a1c-3bfe-7741-b855-3c24c3d307e7`.
- Environment files are under independent review before commit.

## Required CI checks

GitHub jobs for run `41378483668` establish these exact names:

- `lint`
- `skill-filter-compat`
- `test (ubuntu-24.04)`
- `test (macos-15)`
- `integration (ubuntu-24.04)`
- `integration (ubuntu-24.04-arm)`
- `integration (macos-15)`

Use this nonempty set for dotfiles PR delivery.
Source: [CI jobs](https://github.com/mkobit/dotfiles/actions/runs/41378483668).

## Kit orchestration correction

The user requires tool installation through the repository kit.
The first guest was created before the toolchain definition was complete, then prepared with manual setup commands.
That sequence does not prove repeatable kit creation.
The tracked kit now declares setup, but a fresh creation test is required before later worker launches.
`audit_sbx` owns this test with a separate environment name, `dotfiles-sbx-rearch-kitcheck`.
Preserve the first guest and its logs.
Do not use manual post-create installs or environment patches for the new proof.

Task 2 schema changes have passed 22 focused tests and are under independent review.
Task 3 remains paused until schema review and fresh kit creation pass.

## Reproducibility requirement

The user requires sandboxes to be essentially fully reproducible from scratch.
A tracked repository kit must supply the complete toolchain and runtime configuration through native creation.
No manual post-create install, environment patch, or previous guest state may be required.
Separate kit repositories are permitted as a later follow-up, not part of this change.
Record mutable upstream inputs and pin them through supported kit mechanisms where available.

## Fresh creation test

- Native kit setup ran automatically in 34.3 seconds.
- Creation warned that the guest Docker daemon did not start.
- The first normal `sbx env exec` exited 125 with the same error.
- Fresh runtime and test acceptance have not passed.
- No manual guest repair or environment patch is permitted as the fix.
- Investigation is limited to supported SBX diagnostics and tracked kit/base configuration.
- The default built-in base image is mutable; supported digest pinning is under inspection.

## Skill import interface

SBX `0.50.1` imports from fixed host skill roots and has no source-path option.
Keep plugin caches unchanged.
Use owned materialized copies under `.agents/skills` for the selected authored skills.
Reuse existing deployment ownership records where possible.
The design authorizes native `sbx skills import --force`, including its all-root precedence and replacement behavior.
Automatic removal must be limited to copies and store entries with proven dotfiles ownership.

## Runtime investigation

Host SBX diagnostics passed: 16 passed, 0 failed.
SBX cannot copy logs from the failed guest because `sbx cp` also requires guest runtime startup.
The kit PATH omitted the standard system command directories.
The tracked PATH is corrected; a separate native creation test uses `dotfiles-sbx-rearch-kitcheck-path`.
This is a test of a tracked correction, not a manual repair of the failed guest.
A zero exit from environment creation alone must not count as worker readiness.

## Mise kit candidate

The user recommends [sbx/mise-kit](https://hub.docker.com/r/sbx/mise-kit).
A read-only delegate will check its source, immutable pin, composition, and release-age behavior.
Prefer native kit composition over the npm bootstrap if fresh creation remains reproducible.
Do not create a separate kit repository or change another repository for this assessment.

## Fresh kit acceptance

The final digest-pinned definition passed native creation from scratch.
Environment: `dotfiles-sbx-rearch-kitcheck-pinned`.
Automatic tracked setup completed in 43.2 seconds.
Inherited settings, Python `3.14.7`, and guest-only dependency paths passed assertions.
The normal frozen repository test command passed 22 tests in 33.82 seconds.
No post-create installation, runtime export, or `--env` patch was used.
Evidence: [Kit reproduction report](sbx-rearch-tasks/kit-reproduction-report.md).
Task 3 can now use this verified environment.

## Recovery on 2026-11-02

The user requested continuation.
Both active delegates stopped at a usage limit.
The task 3 guest log records session `01a19a59-08f4-7d31-a82a-bb6b8a13450d`; no task 3 source edits exist.
Preserve that session, confirm old-writer termination, then resume in the same verified guest.
The current time check is `2026-11-02 12:25 UTC`, after the reported reset times.
Do not rebuild the environment or repeat completed schema work.

## First PR verification

All seven checks passed for checkpoint `bea458d1` in [CI run 41384373588](https://github.com/mkobit/dotfiles/actions/runs/41384373588).
This includes lint, Python 3.8 compatibility, tests on Linux and macOS, and integration on Linux amd64, Linux arm64, and macOS.
Later source changes still require their own verification.

## Mise kit decision

Keep the fresh-tested kit for the current implementation.
The native mise mixin is a pinned adoption candidate with an older mise release and guest-wide trust configuration.
Record adoption checks in the follow-up note before use in other repositories.

## SBX settings convergence

The user requires any manual SBX setting change to be codified in Chezmoi source.
Normal apply must restore declared managed values after drift.
Settings hooks must read live state, preserve unrelated fields, and set changed managed values only.
Tests must cover drift correction, a repeated no-op apply, and retry after an unavailable service.
No host SBX setting mutation has been reported in the research or kit setup work.
Keep missing overlay decisions as a no-op and preserve existing custom policy.

## Tracker route decision

Use host-owned claim, immutable acceptance snapshot, and host close for both direct and clone workers.
The guest receives complete task context and does not need a Beads database or tracker credentials.
The host independently confirms the merged PR and unchanged material requirements before close.
Keep a shared tracker service as follow-up work.
A clean main checkout can launch work after exclusive ownership is established; create the assigned feature branch after claim.
Shipping still rejects main and detached HEAD.
See [the route contract](sbx-rearch-tasks/tracker-route.md).

## Task 3 review

The four-file setup implementation passed 116 tests, Ruff, and rendered Bash checks.
Independent review found two P2 defects before commit:

- File replacement can complete before receipt persistence; interruption then blocks later normal apply.
- Source executable-mode changes do not update the copy or its import fingerprint.

The original guest will add regression tests and repair both defects in the same verified environment.
Keep unrelated user changes protected.
No task 3 source commit is complete yet.

## Work-machine execution

Use `feat/sbx-rearch` for shared base work and the [overlay collaboration guide](sbx-rearch-work-machine.md) to resume.
Use native host delegates, isolated Chezmoi rendering, and fake SBX on the work machine.
Keep real sandbox checks on a capable machine.
The earlier `docs/sbx-rearch-handoff` and claim procedure are superseded.

## Task 3 completion

Both review defects are repaired: durable pending identities recover interrupted copies, and mode changes affect copies and imports.
Final source hashes match the 137-test report.
Independent scoped review found no remaining important defect.
Root ShellCheck `0.11.0` passed both rendered hooks; the native skills-mode output matches the convergence parser.
See [the setup report](sbx-rearch-tasks/setup-report.md).
The remote work-machine handoff is published on `docs/sbx-rearch-handoff` at `24972e2a`.

## Shared-branch clarification

The user prefers collaboration through a long-lived feature branch, with shared context available from the overlay.
The earlier separate cross-machine handoff and Git claim workflow was more complex than needed and is superseded.
Keep context and ordinary unit/file ownership updates on `feat/sbx-rearch`.
The overlay session can contribute offline implementation and review without real SBX execution.
Use normal Git collaboration and retain independent reviewers.

## Host path-rule decision

Do not add a parent-directory deny rule that also denies the current workspace.
The AGY directory matcher can include the workspace when its parent is denied.
Use verified native workspace rules and document their limits; keep the real worker filesystem boundary in SBX.
The permission worker must verify Claude matching separately before adding a corresponding rule.
Source: [AGY matching rules](https://antigravity.google/docs/permissions/#supported-cli-actions-and-matching-rules).

## Permission implementation decisions

Keep explicit per-tool ensure entries as exceptions to common catalog `ask`.
Catalog `deny` wins; preserve unrelated native entries and pre-existing deny rules.
The managed modern Codex host selector is `:workspace`, while named definitions remain intact.
Legacy settings use compatible `workspace-write` fields.
The explicit guest profile matches the host selector scheme and does not change the host default to full access.

## macOS CI repair

[CI run 41652944917](https://github.com/mkobit/dotfiles/actions/runs/41652944917) passed Linux amd64/arm64 integration, unit tests, lint, and Python 3.8 compatibility.
macOS apply failed before pytest in all six attempts because the sync hook rejected the system `/tmp` alias above the declared destination boundary.
An isolated execution of the exact hook reproduced the failure.
The repair must accept legitimate ancestor aliases above destDir while retaining checks at destDir and below it.
See [the investigation](sbx-rearch-tasks/macos-ci-investigation.md).

Task 4 renderer tests passed: 86 passed, 33 deselected.
The full focused command reported missing guest deployment prerequisites: 111 passed, 1 skipped, 2 failed, and 5 setup errors.
Tests and markers remain unchanged; initialized deployment and CI checks remain required.

## macOS repair verification

The one-line parent-resolution repair passed all 142 focused tests and independent review.
The target root and managed descendants still reject symlinks.
Root ShellCheck `0.11.0` passed the current rendered hook.
The source hashes match the tested report.
Native macOS CI remains required after publication.
See [the repair report](sbx-rearch-tasks/macos-ci-fix.md).

## Permission review checkpoint

Independent review found no blocking defect in the task 4 implementation.
All 16 reported source hashes match the current files.
The available renderer gate passed 86 tests; full initialized deployment remains pending.
The existing AGY literal-head escaping limit is recorded for overlay collaboration and final review.
See [the permission report](sbx-rearch-tasks/permissions-report.md).

## Published implementation checkpoints

The macOS path repair is signed at `ce0f456d`.
The reviewed permission implementation is signed at `6cf67c08`.
Both need full initialized CI confirmation after publication.
The next source unit is the worker skill and shared SBX authority contract.

## Worker skill review

Task 5a passed its first test checks, but the scenario exercise and independent review leave two defects before commit.
Autonomous delivery must obtain root-dispatched independent review for the final tested head before merge.
The guest can prepare its commit and PR, report `review-ready`, and wait for that result within the same assigned unit.
A changed head invalidates the review result.
Supported mixed skill selections must keep required local references available.
The original guest owns both repairs and regression tests.

[CI run 41753535575](https://github.com/mkobit/dotfiles/actions/runs/41753535575) stopped at Ruff Markdown code-block formatting in the macOS investigation note.
The quote correction is included in the next checkpoint; the initialized matrix has not run for this checkpoint.

Task 7 guest task delivery has a [verified interface report](sbx-rearch-tasks/guest-task-contract.md).
Its static shim and explicit runtime assets still need implementation and fresh-kit integration checks.
The [task 7 corrections](sbx-rearch-tasks/task7-refinement.md) define exact-head review pause/resume, remote base resolution, and CI registration checks.
No new product question is required for those contracts.

## Recovery and CI confirmation

The user requested resumption after the quota stop.
At `2026-11-04 04:25 UTC`, the supervisor proved that no task 5a writer or child check remained.
All 26 final source hashes match manifest `7f027a697768b7cb23bb0fddb3ba2218abbedd26985531b4062e53ba54dd89bf`.
The extra focused test attempt has no completed result; completed repair checks remain valid except for the documented trigger-description delta.

All seven required checks passed for `d54ded96` in [CI run 41757852465](https://github.com/mkobit/dotfiles/actions/runs/41757852465).
This confirms the macOS ancestor-alias repair and initialized permission deployment on Linux amd64, Linux arm64, and macOS.
Later uncommitted skill and model changes are not covered by that CI result.

## Worker skill acceptance

The repaired worker and SBX authority contract passed all five fixed application cases, scoring 10 of 10.
Independent re-review resolved both earlier findings and found no new material defect.
The reviewer verified all 26 final source hashes and checked the local references.
See [the worker skill report](sbx-rearch-tasks/worker-skill-report.md).
Runtime shipping, signing/proxy execution, and real tracker close remain task 7 and integration work.

## Previous parallel execution ownership

Capacity is two guest coding workers, each with its own workspace and environment.
Each workspace has one writer.
Root retains review, integration, signing, and publication on the shared `feat/sbx-rearch` branch.

| Unit | Owner | Workspace and environment | Owned source |
| --- | --- | --- | --- |
| Model routing, review accepted | `implement_model_routing` | Original guest stopped | OpenCode/Pi modifiers, Pi ignore gate, hook `08`, routing tests |
| Repository verification, source returned | `implement_workflow_tasks` | `.worktrees/feat-sbx-rearch-verify`; `dotfiles-sbx-rearch-verify` | `mise.toml`, `.agent-workflow.json` |
| Architect skill, review accepted | `implement_architect_skill` | Original guest stopped | New skill, authored entry, focused skill tests |

The verification worktree starts at `6711c42f` on local execution branch `feat/sbx-rearch-verify`.
Root will inspect its returned diff and commit the accepted unit on the shared branch.
No worker may change signing identities, credentials, host settings, or other repositories.

## Model routing acceptance

Task 6 passed 57 focused tests, eight adjacent tests, and static checks, with two existing overlay-only skips.
Independent review found no correction needed and verified invalid-JSON target preservation.
Root verified the source hashes and ran ShellCheck `0.11.0` successfully.
See [the route report](sbx-rearch-tasks/model-routing-report.md).
Live endpoint, apply, and later source CI checks remain separate integration work.
