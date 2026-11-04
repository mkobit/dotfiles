# Task 7 implementation brief

Implement global workflow tasks and repository verification.
Use the accepted schema and installed CLI interfaces below.
Other workers own schema, SBX setup, permissions, and skills.
Do not change their files without coordination.
Root owns commits, signing actions, review, and publication for this migration.
The [task 7 corrections](task7-refinement.md) take precedence where they amend the initial sequence below.
Use its four bounded implementation units; do not enable unfinished commands as successful placeholders.

## Owned files

- Modify `mise.toml`: add repository `check`, `test`, and `verify` tasks.
- Create `.agent-workflow.json` with the explicit nonempty CI check set recorded in the progress note.
- Extend `.sbx/kit/` only for required worker tools that the pinned base does not provide; verify fresh creation after a kit change.
- Modify `src/chezmoi/dot_config/mise/config.toml.tmpl`: emit workflow tasks from a map when `dig "ai" "workflow" "enabled" false .` is true.
- Create `src/chezmoi/dot_local/bin/tools/executable_dotfiles-agent.py`: standard-library Python helper with `argparse` and no runtime dependencies.
- Create `src/chezmoi/dot_config/dotfiles/private_agent-workflow.json.tmpl`: rendered runtime configuration.
- Create `tests/integration/test_agent_workflow.py`: isolated command and state tests.
- Extend `tests/integration/test_mise.py`: task rendering and caller-directory tests.
- Update the root-owned companion note only with a concise handoff supplied to root.

Read `AGENTS.md`, `src/chezmoi/AGENTS.md`, `src/chezmoi/dot_config/mise/AGENTS.md`, and `tests/integration/AGENTS.md` before editing.
The helper is deployed as a chezmoi executable rather than a new uv package.
No workspace registration, dependencies, lockfile changes, or separate scheduler are needed.
Use `python3` and the existing supported Python baseline.
Use only destination variables in rendered paths.

## Configuration contract

`ai.workflow.enabled` is a machine opt-in in `.chezmoi.toml.tmpl`.
Missing means disabled.
Render task capabilities from `ai.workflow.tasks`, a map keyed by task name.
An overlay can add, replace, or disable one task through a scalar `enabled` value.
Task definitions must not require a second enable list.
Coordinate the exact catalog registration with its owner before editing.

Consume `ai.sandbox.provider`, `ai.sandbox.default_clone_mode`, `ai.sandbox.network_policy`, and `ai.sandbox.proxy_gh_secret`.
Read shared skill mode from existing `sbx.settings.skills_default_mode`.
Consume `ai.signing.mode`, `ai.signing.ssh_public_key`, and `ai.signing.gpg_subkey_id`.
Missing signing mode means `host-default`.
An empty SSH public key permits an existing Git signing key only after the guest signing check passes.
Consume `ai.ollama.enabled`, `host_url`, `sandbox_url`, and `default_coder_model` only for supported routing.
Do not change existing `ai.skills.authored` or `ai.command_policy` maps.

The JSON config contains those rendered defaults, harness argument maps, task definitions, and the destination state directory.
Use `toPrettyJson`; do not assemble JSON strings by hand.
An optional repository `.agent-workflow.json` supplies repository-only settings: `base_branch`, `remote`, `sbx_environment`, and `required_checks`.
Absence uses detected remote default branch and `origin`.
`required_checks` is a nonempty list of exact CI check names when configured.
If absent, query required GitHub checks and fail closed when required protections cannot be established.
An empty list never authorizes merge.
Do not put credentials in either config or the state record.

## Public task interface

Provide these commands with useful `--help` output:

```text
mise run agent:architect --agent claude [--sandbox]
mise run agent:work [--bead ID] --agent claude [--clone] [--model MODEL]
mise run agent:work --resume RUN_ID [--review FILE]
mise run pr:ship BEAD_ID
mise run repo:bootstrap [--check-command COMMAND] [--test-command COMMAND] [--dry-run]
```

`agent:architect` and `agent:work` accept `claude`, `codex`, `agy`, and `opencode` only where the selected environment provides them.
Reject an unsupported agent before claiming a bead.
Keep command arguments as lists in Python and use `subprocess` with `shell=False`.
Treat bead IDs, titles, model names, paths, and branch names as data.
Do not put an untrusted title in executable shell text.
Validate IDs used in branch names and state paths.

Set global tasks to the invocation directory, not the global configuration directory.
Mise currently reports `/home/mkobit` as the default directory for an existing global task.
Use the supported mise invocation-directory context, and verify the rendered task through actual mise execution.
If using mise Tera `{{cwd}}`, emit the literal expression through the chezmoi template and prove that it resolves correctly.
Pass the repository directory to the helper explicitly or read the installed mise invocation-directory variable.
Normalize it with `git rev-parse --show-toplevel`.
Test invocation from a nested repository directory.
The implementation must never fall back to the destination home directory.

Do not expose approval-bypass flags in host architect commands.
Run an interactive host architect with `claude PROMPT`, `codex PROMPT`, `agy --prompt-interactive PROMPT`, or the installed OpenCode interactive interface.
A sandbox architect uses the repository environment and an interactive harness session.
Inspect installed help before choosing the OpenCode interactive arguments.

## Repository verification

Add these repository tasks to root `mise.toml`:

- `check`: `uv run ruff check .`, `uv run ruff format --check .`, and `uv run ty check`.
- `test`: `uv run pytest src/python` and the workflow's isolated tests.
- `verify`: depends on `check` and `test`, then `uv build --all-packages` if not already covered by a task dependency.

Use existing frozen environment and lock settings.
Do not disable `locked = true`, change `minimumReleaseAge`, or update `uv.lock` for this task.
Keep the full installed-state integration suite separate.
Add a named task for workflow tests if that keeps `test` readable.
Ensure each required command runs once per verify execution.

## Worker launch and ownership

Perform read-only preflight before a claim:

1. Resolve repository root, base commit, branch, configured remote, and dirty state.
2. Check that `mise run verify` exists in repository configuration.
3. Verify the selected harness and SBX environment.
4. Verify direct or clone ownership and the change-return contract.
5. Prove required guest Git, credential proxy, signing, and task availability.
   For the selected host-coordinator tracker route, prove tracker identity and readiness on the host.
6. Save a durable launch record before starting a writer.

Use an existing repository-owned `sbxenv.yaml` or the configured explicit environment path.
Do not replace a repository kit with a generic built-in image that lacks its toolchain.
Do not generate a personal global guest kit.
For a repository without an environment, fail with the exact missing path and setup action.

Installed SBX interfaces:

```text
sbx env plan ENV_PATH --name NAME [--clone]
sbx env run ENV_PATH --name NAME --detach --force [--clone]
sbx env exec --name NAME ENV_PATH -- COMMAND ARG...
sbx exec --workdir GUEST_REPO NAME COMMAND ARG...
sbx create --name NAME [--clone] AGENT_OR_KIT REPO
sbx run --name NAME AGENT_OR_KIT REPO -- HARNESS_ARGS...
```

Use unique, recorded sandbox names.
Do not use `--rm`, automatic rebuild, or automatic cleanup after failure.
Preserve pending launch state to prevent a second writer after a disconnected client.
Only use supported observation or resume controls.
A zero harness exit status does not prove task completion.

Direct mode requires a clean checkout and one active writer in the assigned workspace.
A clean base-branch checkout may start a new assignment.
After the atomic claim, create the validated assigned feature branch before implementation.
Do not require users to create a feature branch before automatic issue selection.
Shipping must reject the base branch.
The root may retain its orchestration branch when explicit ownership and bounded edits are provided.
A linked worktree can expose a `.git` file that points outside the mount.
Reject guest Git in that state unless a verified return contract leaves commits on the host.
Do not create or switch a branch behind an active host writer.

Clone mode must verify the cloned base commit before writes.
The installed `sbx create --help` states that clone commits return through host remote `sandbox-NAME`.
Verify that remote and branch before accepting returned work.
A private clone does not share untracked `.beads` state.
Verify a synchronized tracker route, or provide a complete read-only issue snapshot and keep tracker mutations with one designated owner.
Record which route was selected.
Do not let independent clone trackers claim the same host task.
Do not claim that clone delivery or tracker synchronization works until its test passes.

Automatic selection uses `bd ready --claim --json`.
Explicit selection uses `bd update ID --claim --json` after readiness checks.
Set a distinct `BEADS_ACTOR` for each worker.
The installed Beads claim operation is idempotent for the same actor, so actor reuse does not prove exclusive ownership.
Use one designated claim owner; do not claim both on the host and independently in the guest.
If no work is ready, print a plain message and exit zero without launching a sandbox.
If launch fails after a claim, record the failure and preserve the claim for recovery.
Do not silently reset a possibly active worker's claim.

Installed unattended harness arguments:

```text
claude --dangerously-skip-permissions --print PROMPT
codex exec --dangerously-bypass-approvals-and-sandbox PROMPT
agy --dangerously-skip-permissions --print PROMPT
opencode run --auto PROMPT
```

Installed Codex help does not support `--full-auto`.
Only use bypass arguments after the guest boundary is established.
Do not fall back to running an unattended worker on the host.
AGY is absent from SBX built-in agent names; it needs a repository-owned environment with AGY installed.
Do not hardcode `--provider ollama` into `sbx run`: current installed run help does not list that flag.
Model routing must use the supported interface supplied by the SBX setup worker.

The worker prompt gives the full issue snapshot, owned paths, acceptance criteria, branch, required checks, and durable evidence path.
It loads `worker-handoff`, runs implementation and repair in the guest, and uses `mise run verify` and `mise run pr:ship`.
It records unrelated findings without changing unrelated files.
Limit CI repair to two attempts.
Preserve incomplete work and collect human questions in one place.

## Durable record

Use the configured destination state directory, with a repository hash and unique task directory.
Write `record.json`, `prompt.txt`, and `worker.log` before launch.
Use atomic JSON replacement.
Record schema version, task ID, complete scope, acceptance criteria, repository, initial commit and dirty state, branch, clone mode, sandbox, harness, model, effort, actor, launch arguments, phase, exit codes, PR URL/head SHA, pending questions, remaining work, and evidence paths.
Print the record path so the parent can save a pointer in `notes/`.
Keep logs and raw command output out of versioned notes.
Do not store tokens, environment dumps, or private keys.
Update the record on launch, verification, failure, PR return, and confirmed completion.
On interruption, preserve the record and environment.

## Signing prerequisites

Host configuration currently has a GPG signing key and no explicit `gpg.format`.
Do not select the first `ssh-add -L` key.
Do not generate, export, upload, or replace keys.
Use the configured public signing identity and SBX's supported signing route.
In the guest, check effective `user.name`, `user.email`, `commit.gpgsign`, `gpg.format`, and `user.signingkey` without printing secret material.
Prove signing with a disposable Git object or disposable repository before claiming work.
Use the installed platform's supported signing command.
Record whether the signing check ran and passed.
A missing key or a pinentry requirement is an unmet prerequisite; retain it in the companion note.

## PR delivery gate

`pr:ship` performs the following sequence:

1. Resolve Git root and require a clean named feature branch.
2. Reject the detected default branch, detached HEAD, wrong remote, and dirty files.
3. Read local HEAD and require evidence that `mise run verify` passed for that exact commit, or run verification now.
4. Require the selected commit to be signed and fail if signing evidence is absent.
5. Push the explicit feature ref without force.
6. Find the existing PR or create one with structured body text via `--body-file`.
7. Require the PR base, head branch, repository, and `headRefOid` to match expected values.
8. Establish a nonempty required-check set from explicit repository configuration or GitHub required checks.
9. Wait with a bounded limit for all required checks on that PR head to complete successfully.
10. Re-read the head and require the same SHA.
11. Merge with `gh pr merge PR --squash --match-head-commit SHA`.
12. Query `gh pr view PR --json state,headRefOid,url` and require `state == MERGED` with the expected head.
13. Return `merge-confirmed-close-pending`; the host independently confirms identity and closes through its saved tracker route.

Use installed `gh pr checks PR --json name,bucket,state,link` for machine output.
Use `gh pr checks PR --required` where required protections provide the set.
Treat no results, denied API access, failed/skipped/cancelled/pending/unknown results, missing required names, and a changed head as failure.
A required GitHub check is successful only when its state meets the configured successful result contract.
Do not infer success from an empty list.
Never use `--admin`.
A merge queue can leave the PR open after the merge command succeeds; do not close the bead until merge is confirmed.
Keep the local branch and sandbox after return.
Do not switch to `main`, pull, or delete an active worktree branch.
Use an explicit run ID for `gh run view RUN_ID --log-failed`.
Return an actionable failure and the PR URL for repair.

## Repository setup

`repo:bootstrap` operates only on the caller's Git repository.
Support dry-run output before mutation.
Preserve existing `AGENTS.md`, `mise.toml`, SBX configuration, and `.beads`.
Create missing task commands only when supplied explicitly or established from the repository's actual build configuration.
Do not create successful placeholder checks.
When language/runtime detection is not sufficient, report exact missing check/test commands and leave setup incomplete.
Use `bd init --proxied-server --non-interactive --skip-agents --skip-hooks` only when initialization is needed.
Do not force or migrate an existing tracker silently.
Record Beads proxied-server mode as experimental, and verify required installed dependencies before initialization.
Generate missing concise agent instructions with actual commands and the worker handoff rules.
Do not edit another repository during this migration; test on a temporary repository.

## Test plan

Use temporary Git repositories and command stubs for `bd`, `sbx`, harnesses, `gh`, and `mise`.
Exercise public helper commands rather than mirroring private implementation functions.
Record stub calls as JSON so argument boundaries can be asserted.
Keep tests offline and independent of real GitHub writes, credentials, signing agents, or sandbox creation.

Required cases:

- Render disabled workflow, missing workflow keys, base-enabled workflow, and an overlay that replaces or disables one task.
- Run an actual rendered mise task from a nested repository path; assert its resolved root.
- Preserve argument boundaries for spaces, quotes, newlines, backticks, and command substitution in issue titles and paths.
- Reject unsupported agents and missing prerequisites before a claim.
- Use atomic ready claims and unique actors.
- Do not launch when ready work is empty or a claim fails.
- Preserve state after a launch or harness failure.
- Prevent duplicate direct writers and reject inaccessible linked-worktree Git metadata.
- Build direct and clone argument lists, validate clone base and return remote, and reject a missing tracker route.
- Reject a host fallback and unsupported Codex or model-routing flags.
- Reject main/default branch, detached HEAD, dirty tree, wrong PR head/base/repository, or unsigned commit.
- Fail closed on no checks, missing names, API failure, pending, failed, cancelled, skipped, or unknown checks.
- Reject a head change during the wait.
- Supply `--match-head-commit` and close a bead only after confirmed merge.
- Keep the bead open when merge is queued or rejected.
- Preserve existing setup files, make a second setup idempotent, and make dry-run mutation-free.
- Make every error name the failed prerequisite and the corrective action.

Suggested commands:

```bash
mise exec -- uv run pytest tests/integration/test_agent_workflow.py tests/integration/test_mise.py -m 'not integration' -q
mise exec -- uv run ruff check src/chezmoi/dot_local/bin/tools/executable_dotfiles-agent.py tests/integration/test_agent_workflow.py tests/integration/test_mise.py
mise exec -- uv run ruff format --check src/chezmoi/dot_local/bin/tools/executable_dotfiles-agent.py tests/integration/test_agent_workflow.py tests/integration/test_mise.py
mise exec -- uv run ty check
mise tasks validate
mise run verify
```

Also render runtime JSON with chezmoi into a temporary destination and parse it with Python.
Check global tasks with `mise tasks ls --json` and actual task execution using the isolated rendered global config.
Use CI for the full apply and integration matrix.
Report exact checks, exit codes, unavailable prerequisites, changed files, and the durable evidence path to root.

## Sources

The local command interface was checked with `mise run --help`, `mise tasks --help`, `bd` 1.3.1 command help, `sbx run --help`, `sbx create --help`, `sbx env run --help`, `sbx env exec --help`, `codex exec --help`, `claude --help`, `agy --help`, `opencode run --help`, `gh pr checks --help`, and `gh pr merge --help`.

- [Mise task execution](https://mise.jdx.dev/tasks/running-tasks.html).
- [GitHub checks](https://cli.github.com/manual/gh_pr_checks).
- [GitHub merge](https://cli.github.com/manual/gh_pr_merge).
- [Beads v1.3.1 source](https://github.com/gastownhall/beads/tree/v1.3.1).

## Integration decisions

Task 6 supplies custom native SBX provider ID `ollama-configured`; host Pi/OpenCode use provider ID `ollama`.
Native SBX routing supports local built-in Claude Code, Codex, and OpenCode, with the required feature flags.
Reject unsupported model-route and harness combinations before claiming work.
The authoritative host/guest Beads route needs a verified transport contract; do not treat shared filenames as shared server access.
A separate read-only architecture report will define that interface before implementation.

## Authoritative tracker contract

Use [the host-owned route](tracker-route.md) for direct and clone modes in this implementation.
The host claims with one saved actor and freezes the complete acceptance snapshot.
The guest receives that snapshot and must not initialize, copy, or claim a separate tracker.
Guest Beads is not required for this route.
After guest delivery, the host independently verifies merge identity and unchanged material requirements, then closes through the saved tracker directory.
A failed close leaves a recoverable pending-close state; it must not repeat implementation or open another PR.
Keep shared network tracker services as follow-up work.

## Review and resume contract

Before merge, require independent root-dispatched review acceptance for the exact tested head and frozen assignment.
The guest can prepare its commit and PR, then pause at `review-ready` without completing or replacing its assigned unit.
The host saves review evidence outside guest-controlled state and uses `agent:work --resume RUN_ID --review FILE`.
The resume path must retain the run, actor, claim, environment, workspace, branch, PR, and snapshot.
A changed head invalidates review, local verification, and CI evidence.
Do not merge without acceptance and do not ask the user to approve routine review.
See the correction report for result fields, phases, no-writer checks, and close-only recovery.

Resolve the configured remote base SHA before claim; a stale local ref or the caller's feature HEAD is insufficient.
Direct autonomous work needs a clean exclusive checkout at that SHA.
Clone work must prove the expected base object, task availability, and return route before claim.
Keep this migration's shared feature branch in its explicit edit-only route.

Bind CI results to the expected commit SHA and wait for registration within a bounded deadline.
Empty or stale results cannot pass, and PR check summaries alone do not prove the result SHA.
Keep existing draft PRs draft and retain the local feature branch after delivery.

## Guest task interface

Use the [guest task interface report](guest-task-contract.md) for the tracked static `pr:ship` task and runtime file transport.
Host-global task configuration is not present in the guest by default.
Preserve the guest global tool settings and verify the discovered task source before launch.
