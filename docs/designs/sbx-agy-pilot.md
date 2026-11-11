# SBX agy release-update pilot

- **Author:** Mike Kobit
- **Status:** Approved
- **Date:** 2026-11-10
- **Input:** [Approved concepts brief](../../concepts_brief.md) at `18cec9ef`

## Overview

Prove that one eligible `agy` release-update issue can be selected from a work queue and completed in an SBX guest through verification, signed commits, a GitHub PR, CI, merge, tracker closure, and a host report.
After setup, the guest selects and claims one unit, assesses its complexity, uses subagents where suitable, completes the unit, and exits without routine host approval.
The host sets the allowed project and scope and starts the next run.

Use the smallest changes needed to prove this path.
Use native SBX features where they meet the need.
Consider SBX and kit upgrades if they remove a setup blocker.
Use the brief's current-state notes and file inventory to assess existing branch changes.
Older plans supply historical context; their task lists do not set the implementation order.

Prefer Beads when the project has it.
Use another existing project tracker where applicable.
Use native queue selection, claim, and replica sync operations rather than a new tracker framework.

Use a private guest clone for each selected unit.
Use a configured Beads replica and native sync for version 1.
Keep a later path to a shared work tracker, such as a host Beads server.
Prefer automatic approval of safe SBX commands across supported agent tools, with one central command definition.

## The problem

The branch has no proven result from guest assignment through merged PR.
The brief records working private-clone Git and GitHub API access in `dotfiles-sbx-delivery`, but signing and project checks remain unproved.
It also records missing mise and Chezmoi tools, an older custom kit that is incompatible with the current native Codex kit, and pending signing-subkey setup.
These are starting observations, not proof of the sandbox's present state.

Until this path is verified, the host must intervene or cannot establish whether the guest completed the unit.
The pilot must produce evidence for the result and preserve enough state to resume after an interruption.

## Goals

- Establish guest readiness before dispatch: isolated Git access, project tools and checks, required skills, scoped GitHub access, and signing with a dedicated GPG subkey.
  Keep the primary private key outside the guest.
- Query the `agy` release source with retry and backoff, and update the agreed release data under explicit acceptance criteria.
- Run the required project checks in the guest and create signed commits for the update.
- Open or resume one PR for the assigned unit, handle CI failures within scope, and merge only after all required CI checks pass and acceptance criteria are met.
- Return evidence of the result to the host and exit.
  For a blocked unit, preserve the work and report the blocker and the action needed.
- Reconcile Git, PR, CI, merge, and tracker state before repeating external actions after an interruption.
- Select one eligible unit from the existing tracker, with Beads preferred.
  Let the guest claim, refresh, update, and close that unit through the authoritative tracker.
- Support a version 1 mode with one active guest and one claimed unit.
  The guest can use subagents inside that sandbox.
- Assess the selected unit's complexity and choose suitable model effort and subagent work before implementation.
- Split implementation into small units with observable exit criteria.
  Record tested SBX and kit versions and compatibility.
- Define safe SBX command approvals once and render them into each supported tool's permission format.
  State which commands and arguments each grant permits.
- Keep tracker access separate from each private Git clone so a later shared tracker can serve multiple guests.

## Non-goals

- Parallel guests, continuous assignment, or factory coordination in the first version.
- A general tracker adapter, new shared tracker service, claim service, or delivery framework without a demonstrated pilot need.
- Support for forges other than GitHub in this pilot.
- Migration or audit of other repositories.
- Execution of every change in the historical branch plans.
- Pi command-policy support or a Pi approval extension.
- Production changes before design approval.

## Open questions

The architecture decisions are resolved.
Bootstrap must supply the actual pilot tracker identity, native sync remote, available models, signing-subkey identity, and eligible `agy` issue before a live run.
These are required setup inputs, not permission to choose a different architecture.

### Author changes to the brief

The author changed the original direct-dispatch pilot to queue selection during drafting.
The guest now owns tracker writes and selects one eligible issue rather than receiving only a fixed issue from the host.
The author also requested complexity assessment, typical use of subagents, and a version 1 mode with one active guest.
These decisions replace the brief's direct-dispatch-first staging; they do not authorize a continuous worker loop or parallel guests in the pilot.
The first delivery proof remains an `agy` release update.
Model selection applies to subagents; the coordinator model stays fixed for the run.
Version 1 uses native replica sync.
Both host and guest can contribute and push Beads state; each project defines how they obtain the latest state.

## Critical user journeys

### Pick up and complete one unit

- **Given:** A ready private guest clone, verified tracker access, an eligible queue scope, signing, tools, skills, and available subagent models.
- **When:** The host starts one guest run and approves its launch.
- **Then:** The guest selects and claims one eligible issue, assigns bounded subagent work, verifies the result, signs and pushes commits, opens a PR, waits for the expected workflow results, merges, closes the issue, reports, and exits.

### Resume an interrupted unit

- **Given:** The saved run record, preserved guest work, and an interrupted or unknown external action.
- **When:** A later host session resumes the same unit after checking that prior writers stopped.
- **Then:** The guest reconciles tracker, Git, PR, CI, and merge state and completes only the remaining actions.

### Use command approvals across tools

- **Given:** The central SBX policy applied to a supported host tool.
- **When:** An agent inspects, creates, removes, launches, or executes in a sandbox.
- **Then:** Selected inspection, creation, and removal commands use automatic approval; launch and execution require approval.
  Pi is outside this policy.

## Technical plan

### Research baseline

The design worktree remains on `feat/sbx-rearch` at `18cec9ef`.
The refreshed `origin/main` is `16d49d4f`.
The brief's inventory still describes the branch changes; it does not establish that all of them are needed for the pilot.

The release update itself needs one file: [`src/chezmoi/.chezmoidata/bin/agy.toml`](../../src/chezmoi/.chezmoidata/bin/agy.toml).
It currently selects `1.5.3` and four platform archives.
The existing [GitHub release template](../../src/chezmoi/.chezmoitemplates/bin/github-releases-entry.tmpl) supplies download, extraction, and checksum handling.
The pilot must check the four archive hashes and the installed version.
The existing [agy smoke test](../../tests/integration/test_antigravity.py) checks the exit code only.

The branch [delivery instructions](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_worker-handoff/exact_references/delivery.md) depend on a `pr:ship` task that the root [mise configuration](../../mise.toml) does not define.
They also require host acceptance before merge.
The pilot must replace that pause with guest verification under the assigned authority.
Native Git and GitHub CLI commands can perform signing, push, PR, CI, and merge operations without a new shipping service.

The [project CI list](../../.agent-workflow.json) names `lint`, but the [workflow](../../.github/workflows/ci.yml) names that check `Lint and type check`.
The selected workflow-result policy below replaces that list for this pilot.
No `.beads` directory was found in this worktree.
An external tracker or host tracker remains unverified.

### Private guest clone

The author selected a private guest clone.
Keep Git metadata, dependencies, and update files inside the guest.
Return changes through signed commits on the assigned branch and the PR.
Reserve each clone for one active writer.
Separate guests can later use separate clones without sharing a writable Git directory.

The committed [environment file](../../.sbx/sbxenv.yaml) still uses a direct mount with `clone: false`; it must be aligned with this decision before the pilot.
The brief records a separate private-clone sandbox with working Git and API access, but that does not prove the complete delivery path.
Preserve unpushed commits, changed files, task state, and logs before any planned sandbox removal or recreation.

Tracker state must remain separate from clone ownership.
The run prompt identifies the project tracker, its remote, and its documented native sync process.
Each replica participates in that process; do not treat an unsynchronized database copy as current queue state.
The guest owns tracker writes.
The host can also contribute design, issue, and other work and push its tracker state.
The one-active-guest limit does not prohibit host tracker work.

### Native features to retain

Use native SBX environment, execution, logs, and skill facilities when the selected versions support the required behavior.
Use `gh pr checks` for CI observations and `gh pr merge --match-head-commit` to bind the merge request to the checked PR head.
Read back the merged PR state; acceptance of a merge request is not proof of merge.
See the [checks command](https://cli.github.com/manual/gh_pr_checks) and [merge command](https://cli.github.com/manual/gh_pr_merge).

Current [SBX release notes](https://docs.docker.com/ai/sandboxes/release-notes/) state that version `0.51.0` uses v3 kits for built-in agents and cannot combine them with v1 or v2 kits.
The repository toolchain kit is v2.
The technical plan must select a compatible kit set and record the tested versions before guest execution.
See [kit version and pin guidance](https://docs.docker.com/ai/sandboxes/customize/use-kits/).

### Guest readiness

Use installed SBX `0.51.0` as the starting version.
No host upgrade is currently needed for the identified features.
Use one pinned native v3 Codex workload and convert the repository toolchain mixin to v3.
Keep the workload's native launch behavior.
Select and record the workload digest, project kit revision, agent version, and model during bootstrap.
Do not use a floating built-in agent reference for the reproducibility proof.
If a version blocks a required capability, investigate an upgrade as a small setup unit before dispatch.
See [tool mixins](https://docs.docker.com/ai/sandboxes/customize/author/tool-mixins/) and [capability support](https://docs.docker.com/ai/sandboxes/customize/author/capabilities/).

Provision the project tools through the tracked kit and the repository's existing installation sources.
Use the selected base's frozen dependency lock and retain minimum release ages.
Verify mise, uv, Chezmoi, Git, GnuPG, GitHub CLI, and archive tools in the guest.
Run the repository verification task and an isolated Chezmoi apply before the release-update unit starts.
Setup failure is a setup unit; it must not expand the catalog-only release update.

Use native readonly shared-skill links beside the guest's project skills.
Verify skill discovery in the selected workload, including linked references.
New shared skills need a container restart to appear; edits to existing shared entries are visible through the links.
Avoid expanding the branch's force-import script or replacing the whole guest skills directory.

Scope the GitHub credential to the sandbox through native SBX service-secret bindings.
Use a credential restricted to this repository and the required Git, PR, and CI operations.
A sandbox binding does not itself restrict a token's repository permissions.
Verify Git fetch, branch push, release queries, PR access, CI logs, and permitted squash merge during setup and the pilot.
Keep host credential resolvers outside guest-writable mounts.
Do not reuse the branch's global GitHub resolver as proof of sandbox scope.

Use the agreed dedicated GPG signing subkey.
The native [git-signing example](https://github.com/docker/sandbox-kit-spec/blob/main/examples/git-signing/git-signing.yaml) uses SSH signing and cannot meet this requirement.
Use manual or assisted export of only the selected secret subkey, controlled transfer with native `sbx cp`, and import into the guest's private GnuPG directory.
Do not put the export or passphrase in Git, image layers, command arguments, logs, or task records.
Check that the primary secret key is absent and that only the selected signing subkey is usable.
Prove non-interactive signing, local signature verification, and signing after restart before dispatch.
Passphrase delivery and unlock behavior must pass this setup proof; do not assume that a cached agent will survive restart.
See [GnuPG subkey export](https://www.gnupg.org/documentation/manuals/gnupg/Operational-GPG-Commands.html).
This setup is not yet proved and does not authorize access to the primary private key.

### Queue selection and release-update flow

```mermaid
flowchart LR
    A[Host scope and saved run record] --> B[Ready private guest clone]
    B --> Q[Read queue and claim one eligible issue]
    Q --> M[Assess complexity and select subagent work]
    M --> C[Query release and verify archives]
    C --> D[Update catalog and run guest checks]
    D --> E[Sign and push assigned branch]
    E --> F[Create or resume PR]
    F --> G[Wait for workflow results]
    G --> H[Squash merge checked head]
    H --> T[Verify merge and close tracker unit]
    T --> I[Report to host]
    I --> J[Exit guest]
```

The host supplies the repository, allowed queue scope, tracker route, base policy, acceptance rules, model availability, and return location.
For the first proof, eligibility is limited to an approved, bounded `agy` release update.
It saves the complete prompt and a durable run record before launch.
Launch needs the selected host tool's execution approval; the guest then runs project commands directly under the assigned authority.
It does not call host SBX commands for each edit or check.

The guest reads the authoritative tracker and lists ready work within the allowed scope.
With Beads, use `bd ready --json` and read full candidate issues with `bd show ID --json`.
Check project instructions, design approval, issue type, dependencies, owner, scope, acceptance criteria, and linked specifications.
Ready status alone does not establish permission to implement.
Skip human-only work, unapproved design work, epics that need division, and units outside the allowed scope.
If there is no eligible unit, report that result and exit.

Choose one eligible issue and claim it atomically with `bd --actor RUN update ID --claim --json`.
If another actor wins, refresh the queue and select again within a bounded attempt count.
Read the same issue again after claim and preserve its identity, acceptance criteria, owner, and claim evidence.
`bd ready --claim` exists, but it claims the first matching ready item before a separate review of that candidate.
Do not use it with an unfiltered queue that contains human work or unapproved epics.
`bd claim` is not a command in the inspected version.

Use the project's documented native sync command before queue reads and after issue writes.
For the inspected Beads version, this can be `bd sync --no-adopt --json` after an explicit remote is configured.
Sync, read ready work, inspect and claim one eligible issue, sync again, then read back its ownership and scope before implementation.
Refresh state before publication, merge, and closure.
The host follows the same project sync process when it contributes tracker changes.
Use native Beads conflict handling and retries.
If sync or claim fails, preserve the current state and report the failure; do not build a custom conflict resolver or force an ownership change.

The guest verifies its repository, assigned branch, base, clean starting state, and exclusive clone ownership.
It queries `google-antigravity/antigravity-cli` through `gh api`, `curl`, or an equivalent client.
Use bounded retries with backoff for transient failures, retain the exact error when retries end, and do not retry permanent permission failures as network errors.
Record the selected release and four expected platform assets.
If the current base already contains that release, report no update needed; do not create a false proof PR.

For an ordinary release, change only the version and four checksums in the `agy` catalog.
Verify all four downloaded archives, their SHA-256 values, expected archive members, and the existing platform mappings.
Use the existing Chezmoi external path to install the guest's platform into an isolated destination, then prove that `agy --version` reports the selected version.
Retain Linux and macOS platform coverage in CI; the guest does not claim to run foreign-platform binaries.
Run the repository verification task and record its exit and head or diff identity.
An archive layout change or unrelated toolchain failure becomes a separate unit or blocker.

Review the diff against the assignment and create signed commits with the selected subkey.
Verify each new commit signature before push.
Push only the assigned feature branch.
Look up a PR by repository, head branch, and base before creating it.
After a timeout, reconcile the remote branch or PR before retrying a write.
Use native Git and GitHub CLI operations; remove the dependency on a missing `pr:ship` helper.

Observe the expected workflow results for the final PR head.
Fix failures caused by the assigned update within its scope, then sign and push the repair and collect fresh results.
For a transient CI failure, inspect the logs before a bounded retry.
Keep unresolved unrelated failures visible and return a blocker rather than expand the unit or omit a check.
Review and verify in the guest without a routine host acceptance pause.
Merge with the repository's permitted squash method and the expected head SHA.
Re-read the PR after merge and record its merged state, merge commit, and branch identities.
An auto-merge request, queued merge, or zero command exit is not completion evidence.

### Progress, resume, and host report

Reuse the existing task-specific host record, guest task-context files, and captured logs.
Keep a discoverable record pointer in the caller's task context.
No new global state store, shipping service, or tracker adapter is needed.
The minimum record contains the assignment, sandbox and clone identity, base, branch, agent session, selected versions, current phase, head, check results, PR URL, merge result, and tracker route when present.
Keep credentials outside it.

Save evidence at setup, launch, verified changes, push, PR creation, CI completion, merge, and return.
Capture guest output on the host so the only progress copy is not in agent memory.
Keep guest checkpoints inside the private clone and preserve them with changed files and unpushed commits before planned removal.
Unexpected guest-storage loss can still lose unpushed work; private-clone isolation is not a backup guarantee.

On resume, load the saved record and reconcile Git, the remote branch, PR, CI, merge state, and tracker state before repeating an external action.
Check that the previous writer and its child checks have stopped before starting a replacement.
If merge already occurred, finish report and tracker closure only.
If a push changed the head, earlier CI evidence is stale.
If ownership, state, or scope cannot be established, preserve the sandbox and return the specific blocker.

The host report states complete, blocked, or interrupted and links the release evidence, changed file, signed head, check results, PR, merge commit, logs, and remaining work.
The guest stops its child processes and exits after reporting.
The host starts the next run; the guest selects no second issue in this run.

### Complexity and subagent work

Read the selected issue's full scope and relevant project instructions before choosing implementation models.
Use issue labels and metadata as evidence, not as a substitute for reading the acceptance criteria.
Record the assessed complexity, selected model and reasoning effort, and the reason.
Do not create a separate classifier service or assume that Beads has a native model-selection field.

Use native guest subagents for bounded implementation and separate review where the harness supports them.
The coordinator owns scope, claims, integration, signing, PR delivery, CI, merge, and closure.
For the catalog update, keep one implementation writer active and stop writers before checks that require a stable tree.
Subagents inside one guest share its filesystem and permissions; they are not separate SBX sandboxes.
Use explicit file ownership and acceptance checks for each subagent.
Do not start nested SBX environments or one extra sandbox per subagent.

The native Codex subagent interface supports model and reasoning choices, subject to installed configuration and model access.
Model availability and guest subagent execution still need a setup proof.
The current branch's architect skill assigns model selection to the host; it must change to support guest assessment.
Do not reuse personal Ollama settings or older host-specific worker limits as the pilot's model policy.
See [native subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).

The author selected subagent model choice with one fixed coordinator model per run.
One sandbox task can divide work among subagents without starting more sandboxes or restarting the coordinator.
Use independent read or review tasks in parallel where suitable.
For work beyond the one-file pilot, concurrent implementers require separate file ownership and a stable integration point before checks.
The coordinator returns a blocker if it cannot assess or manage the selected work.
Use verified model availability rather than a new fixed model catalog for this pilot.
Guest delegation is preferred; if the required model or native delegation is unavailable, preserve the claim and return a capability blocker rather than silently start a second execution framework.

### Central SBX command approvals

Extend the existing [SBX command catalog](../../src/chezmoi/.chezmoidata/ai/command_policy/sbx.toml).
Keep command selections in that catalog and render them into each tool's native format.
Do not maintain separate SBX allowlists in skills and tool settings.
The [source instructions](../../src/chezmoi/AGENTS.md) describe the existing shared policy.

The author selected automatic approval for inspection, creation, and destruction.
Execution must require approval.
Keep `sbx exec`, `sbx env exec`, and agent launch outside automatic approval.
Creation can run kit setup code; this is part of provisioning, so the selected kit and source still need to be established during setup.
Automatic command approval does not itself grant SBX access to secrets or change SBX network policy.

The current catalog allows only `sbx --version`.
It also retires older live grants.
Its current prefix rules do not restrict the target sandbox or the meaning of later arguments.
Do not grant the broad `sbx` prefix.
Secret changes, policy changes, and host file copy are outside the selected automatic approvals.
The exact command list must separate inspection and provisioning from commands that also launch a worker.
The initial inspection set is:

- `sbx --version`, `sbx version`, `sbx --help`, `sbx help`
- `sbx ls`, `sbx list`, `sbx inspect`, `sbx daemon status`
- `sbx env plan`
- `sbx kit inspect`, `sbx kit validate`, `sbx kit verify`, `sbx kit provenance`
- `sbx policy check`, `sbx policy inspect`, `sbx policy log`, `sbx policy ls`
- `sbx mcp inspect`, `sbx mcp ls`, `sbx skills ls`
- `sbx template inspect`, `sbx template ls`, `sbx settings get`, `sbx settings ls`

Settings reads can start the daemon; kit inspection and verification can access a registry.
Use `sbx create` and `sbx env create` for creation, and `sbx rm` and `sbx env rm` for removal.
Use named removal for the pilot; keep bulk `sbx prune` outside this initial selection.
A plain `sbx rm` prefix also permits `--all` and `--force`, and `sbx env rm` permits `--prune-bindings`.
The design must report these argument limits rather than claim that a prefix restricts removal to the assigned sandbox.
Environment creation and removal can run host lifecycle commands; use `--skip-host-commands` for pilot operations unless a reviewed setup requires those commands.
Keep `sbx run` and `sbx env run` under execution approval even though they also offer a detached startup mode.
Do not approve `sbx diagnose` as a whole inspection prefix because it accepts `--upload`.
Do not approve `sbx ports` as a whole inspection prefix because it can change port bindings.

Use the same central decisions for these five managed local tools:

| Tool | Native integration | Required check |
| --- | --- | --- |
| Claude Code | Extend the existing [settings renderer](../../src/chezmoi/dot_claude/modify_settings.json). | Check prefix syntax against the installed version and preserve native denials. |
| Antigravity CLI | Extend the existing [settings renderer](../../src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json). | Use literal command-token rules; check ask and deny precedence. |
| Codex | Add a separate managed `.rules` file from the catalog. | Validate rules with native `codex execpolicy check`; preserve user rule files. |
| OpenCode | Extend the managed V1 `permission.bash` configuration. | Preserve existing key order because the last matching rule wins. |
| Cursor CLI | Add a managed modifier for `.cursor/cli-config.json`. | Prove argument matching on the installed build before enabling grants. |

Sources: [Claude permissions](https://code.claude.com/docs/en/permissions), [Antigravity permissions](https://antigravity.google/docs/permissions/#supported-cli-actions-and-matching-rules), [Codex rules](https://learn.chatgpt.com/docs/agent-configuration/rules), [OpenCode V1 permissions](https://raw.githubusercontent.com/anomalyco/opencode/v1.18.10/packages/web/src/content/docs/permissions.mdx), and [Cursor permissions](https://cursor.com/docs/cli/reference/permissions).

Installed research checks found SBX `0.51.0`, Codex `0.167.0`, OpenCode `1.18.10`, and Cursor `2025.10.01-369e3d0`.
The Pi catalog pins `0.83.0`, but the installed binary reports `0.0.0`; its installed release remains unverified.
Do not apply current OpenCode V2 settings to this V1 installation.
Do not use sorted JSON serialization for OpenCode rules if it changes rule precedence.

An approval expansion does not remove existing native denials or unrelated live grants.
Requiring execution approval also needs explicit ask behavior where a tool would otherwise permit execution.
For tools without an explicit ask rule, use the native confirmation default and prove that no effective broad allow defeats it.
If a live permission or a tool mode defeats the selected boundary, report it and do not claim enforcement in that mode.
Tests must prove this distinction, as well as the selected grants, overlays, preserved denials, and repeated apply.
The existing [retirement tests](../../tests/integration/test_sbx_command_retirement.py) currently require version-only approval and must change with the policy.

### Pi exclusion

Pi normally runs tools without per-call approval.
The author excluded Pi from this policy's scope.
Do not change Pi configuration or add an approval extension for this pilot.
The five-tool policy must not claim that Pi enforces execution approval.
See its [security model](https://raw.githubusercontent.com/earendil-works/pi/v0.83.0/packages/coding-agent/docs/security.md).

### CI authority

The author selected GitHub rules as the preferred source of required checks.
Put the required verification in CI.
Git hooks or agent hooks can provide earlier feedback in a sandbox, but they do not replace CI evidence or GitHub merge rules.
No hook system is required for this pilot.

Read the applicable GitHub rules before dispatch and observe workflow results for the final PR head.
Missing, pending, cancelled, or failed expected checks prevent merge.
The guest must not treat an empty result as success or weaken the check set to finish the unit.
Use `gh pr checks` and GitHub API results rather than a new CI service.

Read-only GitHub queries on 2026-11-10 found no required status checks in the [rules for `main`](https://api.github.com/repos/mkobit/dotfiles/rules/branches/main).
The rules require a PR and linear history, permit squash merge only, and require zero approving reviews.
The legacy required-status-check endpoint returned `404` with `Branch not protected`.
Repository settings also disable merge commits, rebase merges, and auto-merge.
The author chose to retain these settings and enforce workflow completion in the guest.

The branch's `.agent-workflow.json` is a separate list of expected check names.
It is not a GitHub ruleset and currently contains one stale name.
Do not use it as a second policy source unless the author selects that approach.

The author selected workflow results for this pilot and did not authorize adding required checks to GitHub.
Derive the expected jobs from the applicable workflow at the assigned base and record them in the assignment.
The guest enforces this acceptance requirement even though GitHub currently does not enforce it.
Keep manual repository control with the author; do not add a ruleset or an automatic bypass mechanism.
The normal guest path waits for the expected CI results.
If the author changes a unit's acceptance criteria, record the changed scope and the unpassed checks explicitly.

The existing CI workflow produces these seven results for a catalog-only PR:

- `Lint and type check`
- `skill-filter-compat`
- `test (ubuntu-24.04)`
- `test (macos-15)`
- `integration (ubuntu-24.04)`
- `integration (ubuntu-24.04-arm)`
- `integration (macos-15)`

The workflow-comment check is path-filtered and is not expected for a catalog-only release update.
Record the selected source, expected names, final head, and check links in the unit evidence.
Use squash merge with `--match-head-commit` and without administrator bypass.
Verify the guest commit signatures before push; record the server-created squash commit separately from the signed guest head.

### Guest tracker route

Use native Beads replica sync for version 1.
Each project's setup or delegation prompt defines the tracker identity, initial replica setup, explicit remote, sync command, claim command, and close command.
The host and guest can both contribute and push tracker state through that process.
Keep credentials outside the prompt and task record.
Use separate run actors so ownership can be checked after sync.
Use the installed version's documented commands rather than a new tracker adapter or sync service.
See the [Beads storage and sync documentation](https://github.com/gastownhall/beads/blob/v1.3.2/docs/architecture/dolt.md).

Keep one active guest in version 1.
The coordinator's subagents work under its selected issue; they do not independently claim more queue items.
After confirmed merge, re-read the unit and verify that its owner and acceptance criteria still match the selected work before closing it.
Sync the closure and read it back before reporting tracker completion.
If closure or its sync fails, record merge complete and tracker closure pending.
Resume only closure and reporting; do not repeat implementation or create another PR.
Native `bd serve` remains a later option for a shared queue; no host HTTP or SQL service is required for this pilot.

### Local queue evidence

Read-only `bd ready --brief --json --limit 3` calls succeeded with Beads `1.3.2` in [Canopy](/home/mkobit/workspace/mkobit/canopy) and [Storagemaxxing](/home/mkobit/workspace/mkobit/storagemaxxing).
The queries reported 117 and 17 ready issues respectively.
The samples included human work, review work, research epics, design-needed epics, a `high-reasoning` label, and a linked OpenSpec design.
No fixed model identifier or delegation policy was present in the sampled records.
This evidence supports reading scope and project approval rules before claim and complexity assessment.
No issues were claimed, synchronized, or changed during this research.
These repositories are research examples; the pilot does not change their project rules or claim their work.

Use the documented native Beads workflow and installed help for version-specific command syntax.
The design does not require a further source audit of Beads claim or merge behavior.

### Implementation boundaries

Prepare small implementation units from the brief's file inventory and the verified gaps above.
Separate the central command policy and its tool renderers, guest setup, tracker and subagent readiness, delivery instructions, and the release-update proof.
The command-policy work can proceed separately from guest setup; only the selected launch tool is needed to run a proof.
Do not make every historical branch change a prerequisite or merge the broad draft PR merely to test the pilot.
The detailed implementation section will name every changed file and each unit's exit criteria.

The architecture is settled for a private clone, guest queue selection and tracker writes, one active guest in version 1, a fixed coordinator with subagent model choice, workflow-result CI, and five-tool central SBX approvals.
Setup still must prove kit compatibility, tracker access, subagent discovery, scoped credentials, and non-interactive subkey signing.
Those are bounded setup proofs, not claims of completed implementation.

## Alternatives considered

The [brief's alternatives](../../concepts_brief.md#alternatives-weighed) covered dispatch, workspace modes, and reuse of the existing branch.
The author resolved further choices during drafting.
These decisions apply to this pilot; they do not remove later support for other project workflows.

| Alternative | Benefit | Cost or failure condition | Decision |
| --- | --- | --- | --- |
| Direct issue assignment for the first proof | Avoids queue discovery and selection. | Does not prove guest issue selection, claim, and complexity assessment. | Rejected by author for this pilot: the guest must select an eligible queued unit. Direct assignment can remain a later supported entry point. |
| Dedicated full host checkout | Gives the host immediate access to guest edits and keeps usable Git metadata inside the mount. | Requires a separate host checkout and exclusive write ownership; guest changes affect host files directly. | Rejected by author: private guest clones better support separate sandboxes and later parallel runs. |
| Linked host worktree with Git metadata outside the mount | Reuses the current host worktree. | Guest Git cannot resolve metadata outside its mount, so signing and publication cannot be proved on that path. | Not usable for this proof: the selected guest must own usable Git metadata. |
| Atomic first-ready selection with `bd ready --claim` | Selects and claims in one native transaction. | The inspected queues include human work and unapproved epics; ready status alone does not establish eligibility. | Not selected for these unfiltered queues: read candidates and project rules, then claim the chosen eligible issue. A later proven eligibility filter can permit atomic first-ready selection. |
| Host-owned tracker writes | Avoids guest tracker access and service setup. | Guest progress and closure depend on later host writes. | Rejected by author: the guest must read, claim, refresh, update, and close its selected unit. |
| Coordinator model changes after issue selection | Can change the coordinator model for each issue. | Needs a restart or resume handoff, termination evidence, and additional recovery checks. | Rejected by author: keep one coordinator model per run and select models and effort for subagents. |
| Nested SBX for each subagent | Gives each worker a separate sandbox. | Adds setup, state, credential, and integration work before the one-guest path is proved. | Not selected: native subagents can divide bounded work inside the existing guest. Separate guest isolation is a later extension. |
| Add required CI checks to GitHub rules | Lets GitHub enforce the check set. | Changes repository controls and requires a separate settings operation. | Rejected by author for this pilot: retain manual repository control and have the guest wait for applicable workflow results. |
| Use `.agent-workflow.json` as a second required-check policy | Keeps an explicit list in Git. | Duplicates workflow job names and already contains a stale name. | Not selected: derive and record the expected workflow results for the unit; continue to obey any applicable GitHub rules. |
| Use Git or agent hooks instead of CI | Gives earlier local feedback. | Local hooks do not prove the remote workflow result and can differ across guests. | Rejected by author as the main verification path: put the best checks in CI. Hooks remain optional early feedback. |
| Automatically approve guest execution | Removes prompts for host `sbx exec`, `sbx env exec`, and agent launch. | Grants arbitrary execution with each selected sandbox's existing access. | Rejected by author: automatically approve selected inspection, creation, and removal commands; keep launch and execution under approval. |
| Add a Pi approval extension | Could apply the central execution-approval boundary to Pi. | Adds interception code and approval behavior that Pi does not provide natively. | Rejected by author: Pi is outside the current scope. |
| Use native SSH signing | Reuses the native SBX signing example. | That example has no GPG subkey import path and sets SSH signing. | Not usable for the agreed signing requirement: prove dedicated GPG subkey signing without the primary private key. |
| Complete the older broad plans and helper before a release update | Reuses their proposed sequence and interfaces. | Adds a shipping helper, host review pauses, and unrelated model or tracker work before a demonstrated need. | Rejected by author through the brief and technical-plan approval: use native features and small units; retain older plans as historical input. |

## Implementation decisions

### Explicit command prompts

The file-level check found that the current central `ask` action removes an exact managed allow rule.
It does not emit a native ask rule.
The [documented contract](../../src/chezmoi/AGENTS.md) permits tool-specific allow exceptions after that removal.
The approved SBX boundary needs execution to require approval, including when the tool can otherwise allow it.
No current base catalog entry uses `ask`, but overlay behavior and existing tests depend on its present meaning.

The author chose minimal scope and noted that SBX is currently used only on the home machine.
Preserve the existing `ask` contract.
Add a central `prompt` action and use it for the four SBX launch and execution heads.
Map it to native ask rules where supported, or a proved confirmation default where explicit ask is unavailable.
Do not change other command-policy decisions, apply the whole catalog to new tools, or add a multi-machine rollout system.
Keep Pi outside scope and preserve stricter native denials.
No action can force a prompt in a tool mode that disables the tool's approval system.
Report that limit during verification.

### Guest tracker connection

The author selected native replica sync for version 1 and deferred `bd serve`.
Each project owns the instructions for obtaining its latest Beads state on both host and guest.
No host service, SQL migration, custom conflict resolver, or new synchronization framework is part of this implementation.
No replica or queue has been created during design work.

## Reconciliation with the brief

The author approved the following changes during drafting and then approved the complete implementation plan.
No unresolved differences remain.

### Replaced staging decisions

| Brief | Approved draft | Author decision |
| --- | --- | --- |
| "Start with the agreed direct-dispatch pilot; evaluate queue pickup afterward, with Beads optional." | "The guest selects and claims one unit, assesses its complexity, uses subagents where suitable, completes the unit, and exits". | Use queue pickup in the first proof, with guest tracker writes and one active guest in version 1. |
| "Beads is optional." | "Use a configured Beads replica and native sync for version 1." | Prefer Beads for this queue pilot; use native replica sync and project-owned freshness instructions. Tracker-free entry points remain outside this proof. |

### Added interface and dependency scope

The central SBX command policy now covers five host tools and adds an explicit `prompt` action without changing the old `ask` contract.
The author requested central approvals, selected inspection and creation/removal approval, excluded Pi, and chose minimal change.
The guest can choose subagent models while its coordinator stays fixed for a run.
The author selected this division of model control.
Native Beads replica sync supports both host and guest contributions; a shared HTTP or SQL service is deferred.
These are approved additions to the brief's initial pilot scope.

The dedicated GPG subkey requirement, primary-private-key exclusion, `agy` first delivery proof, CI before normal guest merge, native-feature preference, saved resume evidence, and report-and-exit contract remain intact.

## Detailed implementation

Implement the following units after design approval.
Each unit has its own reviewable diff and exit criteria.
Prepare small feature branches from the accepted base rather than shipping all historical changes in draft PR #1014.
Use the existing branch inventory to reuse needed work.
Run independent research or implementation tasks in parallel only when their file ownership does not overlap.

The policy units and guest setup can proceed independently.
The live release unit needs the guest setup, queue, delegation, and delivery units accepted first.
Only the selected host tool's policy is needed to launch that proof; finish the other selected tool integrations as separate units.

### 1. Central SBX policy and existing renderers

| File | Action and reason |
| --- | --- |
| [`src/chezmoi/.chezmoidata/ai/command_policy/sbx.toml`](../../src/chezmoi/.chezmoidata/ai/command_policy/sbx.toml) | Modify: define the approved inspection and create/remove heads once; set `prompt` for `sbx run`, `sbx env run`, `sbx exec`, and `sbx env exec`. Retain exact migration data for old live grants. |
| [`src/chezmoi/dot_claude/modify_settings.json`](../../src/chezmoi/dot_claude/modify_settings.json) | Modify: render the new action as native ask rules, preserve existing denials and unrelated settings, and retain the existing `ask` contract. |
| [`src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json`](../../src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json) | Modify: render literal command-token rules and native asks for `prompt`, with existing installation gating and denial preservation. |
| [`src/chezmoi/AGENTS.md`](../../src/chezmoi/AGENTS.md) | Modify narrowly: document `prompt`, unchanged `ask`, the five supported tools, native precedence limits, and Pi exclusion. |
| [`tests/integration/test_sbx_command_retirement.py`](../../tests/integration/test_sbx_command_retirement.py) | Modify: replace version-only approval with the approved set; retain exact cleanup, overlay, removal, and repeated-apply coverage. |
| [`tests/integration/test_ai_workflow_permissions.py`](../../tests/integration/test_ai_workflow_permissions.py) | Modify: test explicit SBX prompts, preserved asks and denials, unchanged old `ask` behavior, and absence of a broad SBX allow. |
| [`tests/integration/test_sbx_command_policy.py`](../../tests/integration/test_sbx_command_policy.py) | Create: start the cross-tool policy suite with real disposable Chezmoi apply cases for the existing two renderers. Extend this same suite in units 2–4. |
| [`mise.toml`](../../mise.toml) | Modify: add the new policy suite and the existing retirement suite to `test:workflow`; add the environment suite from unit 5 when it exists. |

**Exit criteria:** Selected inspection and create/remove commands are allowed; launch and execution prompt; existing denials win; other catalog decisions retain their behavior.
Real apply in a disposable destination is unchanged on the second run.
Tests exercise a tool-specific broad allow so a rendered ask is tested against the behavior it must override.

### 2. Codex SBX rules

| File | Action and reason |
| --- | --- |
| [`src/chezmoi/dot_codex/rules/dotfiles-sbx.rules.tmpl`](../../src/chezmoi/dot_codex/rules/dotfiles-sbx.rules.tmpl) | Create: render only the central SBX entries into one owned native rules file. Use token prefixes and native allow, prompt, or forbidden decisions. Preserve all user-owned rule files. |
| [`tests/integration/test_sbx_command_policy.py`](../../tests/integration/test_sbx_command_policy.py) | Extend: apply the new target and check allowed heads, prompted execution, denial precedence, and near-match commands. |

**Exit criteria:** Run native `codex execpolicy check --rules RENDERED_FILE -- COMMAND` for the policy cases on the installed Codex version.
Do not replace `default.rules` or change the host's approval or filesystem-sandbox mode.
Only SBX entries from the shared catalog are added to this tool in this unit.

### 3. OpenCode V1 SBX rules

| File | Action and reason |
| --- | --- |
| [`src/chezmoi/dot_config/opencode/modify_opencode.json`](../../src/chezmoi/dot_config/opencode/modify_opencode.json) | Rename to `modify_opencode.json.tmpl` and modify: replace the pure modifier with an executable modifier that preserves existing JSON rule order. Keep plugin and Ollama behavior and add central SBX decisions under V1 `permission.bash`. |
| [`src/chezmoi/dot_config/opencode/modify_opencode.json.tmpl`](../../src/chezmoi/dot_config/opencode/modify_opencode.json.tmpl) | New source path from that rename; set executable mode `100755`. Use the existing Python interpreter resolver rather than add a new runtime dependency. The old source path is deleted, while the deployed target remains `opencode.json`. |
| [`tests/integration/test_opencode_plugins.py`](../../tests/integration/test_opencode_plugins.py) | Modify: update the source path and disposable-source dependencies; retain plugin merge and migration checks. |
| [`tests/integration/test_ollama_routing.py`](../../tests/integration/test_ollama_routing.py) | Modify: update the OpenCode fixture source and interpreter dependencies; prove that model settings do not change permission-rule order. |
| [`tests/integration/test_sbx_command_policy.py`](../../tests/integration/test_sbx_command_policy.py) | Extend: use overlapping live rules whose order differs from alphabetical order; check prompt and denial results and repeated apply. |

Reuse [`src/chezmoi/.chezmoitemplates/python/filter-interpreter`](../../src/chezmoi/.chezmoitemplates/python/filter-interpreter) and [`src/python/skill_filter/resolve-interpreter.sh`](../../src/python/skill_filter/resolve-interpreter.sh) without modifying them.
Copy those dependencies into disposable test sources.

**Exit criteria:** Existing plugin and model tests pass; the relative order and meaning of unrelated live rules survive.
Verify with real Chezmoi modify dispatch that the new executable runs and its source text is not written into the target.
Use the installed V1 policy format; do not migrate OpenCode to V2.

### 4. Cursor CLI SBX rules

| File | Action and reason |
| --- | --- |
| [`src/chezmoi/dot_cursor/modify_private_cli-config.json`](../../src/chezmoi/dot_cursor/modify_private_cli-config.json) | Create: use a pure Chezmoi modifier to preserve live CLI settings and add SBX command-and-argument allow patterns. Remove known managed execution allows so native confirmation can apply. Preserve native denials. |
| [`tests/integration/test_sbx_command_policy.py`](../../tests/integration/test_sbx_command_policy.py) | Extend: check exact commands, arguments, near matches, execution confirmation, preserved settings, and repeated apply. |

**Exit criteria:** Prove argument matching and execution confirmation on the installed Cursor build, using its documented native policy behavior.
Static JSON assertions alone do not establish compatibility.
If that build cannot enforce the selected policy, report the required tool upgrade as a separate unit before claiming Cursor support.
Do not substitute a broad `Shell(sbx)` allow.

### 5. Reproducible private guest environment

| File | Action and reason |
| --- | --- |
| [`.sbx/sbxenv.yaml`](../../.sbx/sbxenv.yaml) | Modify: select a private clone, an immutable native v3 Codex workload reference, and the project mixin. Preserve the workload's native launch behavior. |
| [`.sbx/kit/spec.yaml`](../../.sbx/kit/spec.yaml) | Modify: convert the old v2 mixin to v3 with the toolchain lifecycle and network access needed for the documented checks, release queries, and native Beads remote. |
| [`.sbx/kit/Dockerfile`](../../.sbx/kit/Dockerfile) | Create: package the bootstrap assets in the project mixin so installation does not depend on the old direct-mounted source path. |
| [`.sbx/kit/install.sh`](../../.sbx/kit/install.sh) | Modify: adapt the existing pinned tool installation to the v3 kit lifecycle; provide the project tools, Beads `1.3.2`, GitHub CLI, GnuPG, and archive tools needed by the pilot. Retain minimum release ages and frozen project dependencies. Reuse declared package-manager sources; add no custom binary-download script. |
| [`.sbx/README.md`](../../.sbx/README.md) | Create: document the dotfiles setup, required run inputs, private-clone commands, tested workload pin, native Beads replica setup and sync, scoped credentials, and manual subkey setup. Keep secrets out of this file. |
| [`tests/integration/test_sbx_project_environment.py`](../../tests/integration/test_sbx_project_environment.py) | Create: exercise native offline environment and kit validation and packaged bootstrap references. The real fresh-guest checks remain part of unit 10. |
| [`mise.toml`](../../mise.toml) | Extend the unit 1 change to include the environment suite in `test:workflow`. |

**Exit criteria:** Native validation accepts the environment and compatible v3 kit set.
A fresh guest has its own usable Git metadata, expected repository/base, tools, and frozen dependencies.
Run the repository verification task and isolated Chezmoi apply there.
Record tested versions and the resolved workload digest.
Use SBX `0.51.0` unless a demonstrated blocker requires a separately reviewed upgrade.

The existing `.gitignore` already excludes `.sbx/task-context/` and `.sbx/logs/`; it needs no change.
The generic direct-mounted environment templates and global SBX tool version are outside this unit.

### 6. Bootstrap and skill authority

| File | Action and reason |
| --- | --- |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/AGENTS.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/AGENTS.md) | Modify narrowly: permit the approved private-clone guest-delivery mode without imposing blanket host signing or host tracker writes. |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_repo-bootstrap/SKILL.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_repo-bootstrap/SKILL.md) | Modify: replace the prerequisite for the absent `repo:bootstrap` helper with native project setup and explicit readiness checks. Require the project's latest-state and delegation instructions. |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-sandboxes/SKILL.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-sandboxes/SKILL.md) | Modify: align the selected pilot mode with private-clone Git and guest signing; remove static SBX command grants from skill metadata so the central policy remains the single definition. |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-sandboxes/exact_references/repository-setup.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-sandboxes/exact_references/repository-setup.md) | Modify: document v3 composition, private Git, shared and project skill discovery, native tracker sync, scoped credentials, subagent readiness, and subkey signing proofs. |
| [`tests/integration/test_docker_sandboxes_skill.py`](../../tests/integration/test_docker_sandboxes_skill.py) | Modify incrementally: validate the deployed skill links and the central-policy ownership of grants. Keep unrelated environment-template coverage. |

**Exit criteria:** Scoped instructions agree on the selected mode.
Skills and references resolve in the guest beside native readonly shared skills.
No bootstrap or shipping helper is required merely to begin setup.
Home defaults for direct mounts, SSH signing, or local models are not treated as evidence of the pilot's explicitly selected settings.

### 7. Queue pickup, native sync, and subagent models

| File | Action and reason |
| --- | --- |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_worker-handoff/SKILL.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_worker-handoff/SKILL.md) | Modify: authorize one eligible queue selection, guest claim and tracker writes, complexity assessment, native subagents, delivery, and exit. |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_worker-handoff/exact_references/assignment.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_worker-handoff/exact_references/assignment.md) | Modify: accept project queue scope and sync instructions; record the selected issue, acceptance criteria, claim, branch, models, and same-run resume state. Replace the mandatory frozen host-claim contract for this mode. |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_architect-scoping/SKILL.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_architect-scoping/SKILL.md) | Modify: let the guest assess the selected unit and choose available subagent models and reasoning effort; keep the coordinator fixed and defer work that exceeds the unit. |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/tracker.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/tracker.md) | Modify: document native replica sync for host and guest, eligibility reads, claim and sync, read-back, progress, close and sync, and simple failure reporting. Remove mandatory host-only tracker ownership. |

**Exit criteria:** The project supplies an explicit native remote and latest-state procedure.
The guest can read the queue, inspect eligible issues, claim one, sync, and read back its scope and owner.
Use native Beads behavior for conflicts; do not add another claim protocol or resolver.
The coordinator starts an implementation subagent and a separate reviewer with recorded model choices inside the same guest.
The one-file release update has one active implementation writer.
The host can contribute and sync tracker work without starting another guest or writing the guest's private checkout.

### 8. Launch and host observation

| File | Action and reason |
| --- | --- |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/SKILL.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/SKILL.md) | Modify: align launch authority with one guest, guest queue ownership, and native subagent work. Remove static SBX command grants from skill metadata. |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/host-supervisor.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/host-supervisor.md) | Modify: supply queue scope and setup evidence, save the run record, capture output, and start one guest. Remove host-specific model names and worker-count assumptions from this mode. |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/subagent-task.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/subagent-task.md) | Modify: provide queue authority, native sync instructions, model availability, pilot acceptance, output location, and the one-unit exit contract. |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/worker-launch.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/worker-launch.md) | Modify: use the selected native launcher and private-clone Git, preserve the fixed coordinator model and session, and remove the pilot's `--skip-git-repo-check` assumption. |
| [`tests/integration/test_docker_sandboxes_skill.py`](../../tests/integration/test_docker_sandboxes_skill.py) | Extend: preserve argument quoting, effective sandbox identity, output capture, exit codes, and launch/resume behavior. Allow links to the selected deployed worker skills where needed. |

**Exit criteria:** The host record identifies the run, environment, clone, prompt, model, session, and logs.
Quoted arguments remain literal and failures reach the host with their exit codes.
The host can stop active supervision while the guest completes one unit.
No background assignment loop or nested sandbox launcher is added.

### 9. Native delivery and resume

| File | Action and reason |
| --- | --- |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_worker-handoff/exact_references/delivery.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_worker-handoff/exact_references/delivery.md) | Modify: make this the canonical guest procedure for checks, signed commits, push, PR reuse, expected workflow results, squash merge, tracker closure, report, and exit. Remove the missing `pr:ship` dependency and host acceptance pause. |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/delivery.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/delivery.md) | Modify: link to the canonical procedure and retain only host-specific context instead of a second conflicting delivery contract. |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/recovery.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/recovery.md) | Modify: reconcile the selected issue, native sync, branch, PR, CI, and merge before retries; retain saved logs and same-run ownership. Remove the host review-ready wait and host-only close requirement for this mode. |
| [`src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/nested-execution.md`](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/nested-execution.md) | Modify: use signed pushed commits and the PR as this private clone's return path; record guest tracker closure and preserve any separate edit-only mode. |
| [`.agent-workflow.json`](../../.agent-workflow.json) | Delete: its separate check-name list is stale and is not the selected CI policy source. Record expected jobs from the actual workflow in the unit evidence. |
| [`tests/integration/test_docker_sandboxes_skill.py`](../../tests/integration/test_docker_sandboxes_skill.py) | Extend existing deployed-link and launcher coverage for the canonical procedure; do not add phrase-matching tests as proof of real delivery. |

**Exit criteria:** No active pilot instruction requires `pr:ship`, routine host review acceptance, or a second check list.
The guest waits for the seven applicable workflow results for its final PR head, then uses permitted squash merge with matching-head protection.
After a successful merge, a closure failure resumes only native sync, closure, and reporting.
No GitHub rule or CI workflow change is required for this unit.

### 10. Setup and verification proof

| File | Action and reason |
| --- | --- |
| [`tests/integration/test_antigravity.py`](../../tests/integration/test_antigravity.py) | Modify: for `github_releases` installation, compare the installed `agy --version` with the selected catalog version from rendered Chezmoi data. Keep the existing operational smoke check for a preinstalled tool. |
| [`notes/sbx-agy-pilot-verification.md`](../../notes/sbx-agy-pilot-verification.md) | Create: record tested versions, kit digest, guest Git and skill evidence, native tracker identity and sync results, subagent model choices, public signing fingerprint, command/check results, and remaining prerequisites. Extend it with the live outcome in unit 11. |

Use manual or assisted setup for the sandbox-scoped forge credential and dedicated GPG subkey.
Add no key-export automation or general credential service.
Keep the primary private key outside the guest.
Verify the intended subkey with a scratch signed commit, signature verification, and signing after restart.
Check native host-to-guest Beads state visibility and guest-to-host visibility through the project's documented sync process using a designated setup or pilot issue.
Do not modify unrelated issues in Canopy or Storagemaxxing as fixtures.

**Exit criteria:** A fresh guest passes repository checks and isolated apply; the selected release tool version test is meaningful; signing, native replica sync, and subagent work function in the chosen environment.
Unmet prerequisites remain explicit blockers to the live proof.
Mock or document tests do not count as guest evidence.

### 11. One live agy release update

| File | Action and reason |
| --- | --- |
| [`src/chezmoi/.chezmoidata/bin/agy.toml`](../../src/chezmoi/.chezmoidata/bin/agy.toml) | Modify in the guest's selected unit: update only the accepted release version and four platform checksums for an ordinary release. |
| [`notes/sbx-agy-pilot-verification.md`](../../notes/sbx-agy-pilot-verification.md) | Extend on the host after the guest returns: link the issue, selected release and assets, signed head, checks, PR, squash commit, tracker closure, host visibility after sync, and guest exit evidence. Keep this evidence update separate from the one-file release PR. |

The guest reads fresh Beads state, selects the eligible pilot issue, claims and syncs it, assesses complexity, and delegates the catalog change and separate review.
It verifies all four archives and checksums, installs its platform through the existing Chezmoi external, confirms the selected version, and runs project verification.
It signs, pushes, opens or resumes the PR, handles scoped CI repairs, waits for applicable workflow results, and merges the checked head.
It closes and syncs the issue, returns the host report, and exits.
The host syncs its tracker and verifies that the guest's state is visible.

**Exit criteria:** One ordinary catalog-only release PR is merged after the expected CI results and the guest's acceptance checks pass.
The guest commit signatures, merge identity, tracker closure, host visibility, and guest exit are recorded.
An already-current release, empty eligible queue, setup blocker, or failed run is reported honestly and does not satisfy the merged-release proof.

### Verification and limits

For policy and modifier units, run the focused suites in disposable Chezmoi destinations and verify repeated apply.
For source changes, preview with `chezmoi diff` and use scoped `chezmoi apply` from the correct source worktree to deploy the approved targets.
Never edit the deployed configuration directly.
Native runtime policy checks must supplement template assertions where a tool supports them.
Do not claim enforcement in force or bypass modes, or when an unmanaged broad allow defeats native confirmation.

Run `mise run test:workflow` for the accepted file set and `mise run verify` before each code-bearing unit is submitted.
Run the actual guest and workflow checks for the live release unit.
Use the frozen lockfile; report any approved local tool-version substitution under the repository's existing check policy.
The existing CI integration command already collects the integration tests, so `.github/workflows/ci.yml` needs no change.

Use one saved-run interruption to verify that resume reuses the same selected issue, branch, and PR.
Use an interrupted or pending closure to verify that resume does not repeat implementation after merge.
These are focused lifecycle checks; do not create a general failure-injection or conflict-recovery framework.
Preserve the guest and logs after a failure.
Remove a sandbox only after work and evidence are preserved under the selected removal authority.

No production file, key, tracker issue, or sandbox has been changed by this design draft.

*Drafted with EGM*
