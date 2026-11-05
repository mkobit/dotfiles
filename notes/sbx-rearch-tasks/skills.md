# SBX permissions and skills implementation brief

Worktree: `/home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch`.
Scope: plan tasks 4 and 5.
This brief does not change repository files.
Use the final task-2 schema; do not add another feature-selection schema.
Other agents own setup, model routing, and task execution.
Preserve their changes.

## Ownership

The permissions implementer owns these files:

- `src/chezmoi/.chezmoidata/ai/command_policy/git.toml`.
- `src/chezmoi/.chezmoidata/ai/command_policy/gh.toml`.
- `src/chezmoi/.chezmoidata/ai/command_policy/mise.toml`.
- `src/chezmoi/.chezmoidata/ai/command_policy/sbx.toml`, only if a selected inspection grant is needed.
- `src/chezmoi/.chezmoidata/claude_code.toml` and `src/chezmoi/.chezmoidata/gemini.toml`, only for native file-denial defaults.
- `src/chezmoi/.chezmoidata/codex.toml`, only for native managed host sandbox defaults.
- `src/chezmoi/dot_claude/modify_settings.json`.
- `src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json`.
- `src/chezmoi/dot_codex/modify_private_config.toml`.
- A new pure modifier at `src/chezmoi/dot_codex/modify_private_unattended.config.toml`.
- `tests/integration/test_sbx_command_retirement.py`.
- `tests/integration/test_codex_tui_modify.py`.
- A new focused `tests/integration/test_ai_workflow_permissions.py`.
- `src/chezmoi/AGENTS.md`, only its command-policy description.

The skills implementer owns these files:

- `src/ai/skills/sbx-orchestrator/SKILL.md` and all files under its `references/` directory.
- `src/ai/skills/sbx-sandboxes/SKILL.md`.
- Its references `agents.md`, `permissions.md`, `repository-setup.md`, and `environment-files.md` where workflow authority conflicts occur.
- Other SBX references only when a concrete conflicting statement needs repair.
- `src/ai/skills/architect-scoping/SKILL.md`.
- `src/ai/skills/worker-handoff/SKILL.md`.
- `src/ai/skills/repo-bootstrap/SKILL.md`.
- `src/ai/skills/retro-self-improve/SKILL.md`.
- `src/chezmoi/.chezmoidata/ai/skills/authored.toml`.
- `src/ai/skills/AGENTS.md`, only its SBX authority rules.
- `tests/integration/test_docker_sandboxes_skill.py`.
- A new focused `tests/integration/test_ai_workflow_skills.py`.

Root owns the progress note, decisions, branch, commits, publication, and final review.
Neither implementer owns the global mise task files or task-2 setup files.
Return a list of changed files, exact checks and exits, and unresolved prerequisites.

## Task 4: selected host grants

Reuse `ai.command_policy.commands` and native renderers.
An overlay changes any command to `ask` or `deny` through the same map.
Keep literal command heads in the catalog.
Do not put tool-specific regex or wildcard syntax into catalog keys.

Allow the following GitHub CLI heads needed by the authorized workflow:

```toml
[ai.command_policy.commands]
"gh pr create" = "allow"
"gh pr ready" = "allow"
"gh pr merge" = "allow"
"gh issue create" = "allow"
"gh issue view" = "allow"
"gh issue list" = "allow"
"gh run view" = "allow"
"gh run list" = "allow"
"gh run watch" = "allow"
"gh repo view" = "allow"
```

Keep the existing read-only PR heads.
Do not add comment, mail, auth, secret, or account-key commands.
The user has authorized PR and issue creation for this workflow.
No new message-sending authority follows from this brief.

Use one canonical push command shared with the task implementer:

```toml
[ai.command_policy.commands]
"git push --set-upstream origin HEAD" = "allow"
```

This selected command supports the current feature branch without granting bare `git push`.
Tell the task implementer to use exactly this command.
Keep `git reset`, `git clean`, and force-push commands outside the allow catalog.
Update the existing comment that says all pushes must prompt.
Command-head grants alone cannot prove that a feature branch is active or that appended arguments are safe.
The `pr:ship` task must validate branch, remote, PR identity, and head revision before it pushes or merges.

Allow the four named workflow entry points and repository verification through literal `mise run ...` keys.
Do not grant bare `mise`, bare `bd`, or bare `sbx` as a shortcut.
Keep Beads lifecycle grants in the Beads skill.
Keep SBX execution grants in the SBX skill where the host supports them.
Existing SBX retirement metadata must still remove exact stale grants and retain explicit overlay re-grants.

Preserve computed grants, explicit ensure entries, unrelated live grants, explicit removals, and existing live deny rules.
Add native deny-list merging where required rather than replacing a user's live deny list.
Do not claim that changing an allow key to `ask` removes an earlier live allow entry unless migration/removal logic proves it.

## File boundaries and Codex profile

Add native parent-relative read/write deny rules only after checking current harness syntax.
Keep the rules configurable through the existing Claude and AGY settings data.
Test the rendered native rule values.
A `../` text rule does not prevent equivalent absolute paths, symlink traversal, or shell commands from reading another path.
Codex `workspace-write` limits writes but does not establish repository-only reads.
SBX mount configuration and validated workspace boundaries provide the outer boundary.
Document this limit; do not describe the host rules as complete filesystem isolation.

For Codex host defaults, use supported `sandbox_mode = "workspace-write"` and `approval_policy = "on-request"` values through the existing modifier.
Retain unrelated configuration and the byte-for-byte no-change path.
Do not change host defaults to bypass approval.

Current official Codex documentation uses a separate user-level profile file selected with `--profile unattended`.
It states that Codex 0.134.0 and later no longer reads the legacy `[profiles.unattended]` table.
The installed `codex exec --help` confirms this separate-file behavior.
Use a pure modifier for `.codex/unattended.config.toml` with:

```toml
approval_policy = "never"
sandbox_mode = "danger-full-access"
```

Gate profile deployment on the task-2 workflow decision.
Use this profile only for a harness process inside a verified SBX guest.
Never select it as the host default.
If the guest receives command-line bypass flags instead, keep those flags guest-only and describe how the guest receives its configuration.
Do not assume a host profile file is present inside SBX.

Sources: [OpenAI configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference), [OpenAI profile migration](https://learn.chatgpt.com/docs/config-file/config-advanced), and [OpenAI container execution guidance](https://learn.chatgpt.com/docs/agent-approvals-security).
The schema endpoint still contains legacy profile-map fields; runtime help and the explicit migration guide establish the current profile-file behavior.

## Task 5: authority and references

Keep the host coordinator responsible for scope, task division, environment selection, recovery, independent review, credential setup, and final judgment.
Permit an assigned guest worker to claim its assigned issue, create or use its assigned feature branch, implement, test, sign, push, and run `mise run pr:ship` after these prerequisites pass:

1. The guest has usable Git metadata for the assigned repository and base revision.
2. The guest has exclusive write ownership of its workspace.
3. Signing works with the configured public key or subkey.
4. The configured GitHub proxy supports the needed Git and CLI operations.
5. The guest can reach the authoritative Beads route, or the task supplies an explicit alternative claim/state route.
6. The repository has a real `mise run verify` gate and a defined required-CI-check source.

Do not weaken signing, copy raw tokens, copy a live Beads database, or mount extra host metadata to hide a failed prerequisite.
An edit-only delegated task can still use host delivery when its explicit contract says so.
The autonomous worker path must not silently fall back to host execution.

Repair each conflicting instruction in `nested-execution.md`, `host-supervisor.md`, `subagent-task.md`, `worker-launch.md`, and `recovery.md`.
Current conflicts include host-only branch operations, read-only tracker context, no guest commits, host-only signing/pushes, and host-only issue transitions.
Repair the same conflicts in SBX sandboxes `SKILL.md`, `agents.md`, `repository-setup.md`, and `src/ai/skills/AGENTS.md`.
Keep direct mounts and private clones explicit.
A mounted linked worktree can have inaccessible Git metadata; check before launch.
A private clone needs a documented branch/PR return path and Beads synchronization contract.
Do not require a second host patch application after successful guest branch publication.
Preserve logs, checkpoints, identity, limits, and exclusive-ownership checks during recovery.

## Four new skills

Keep each skill short and put detailed CLI contracts in references only when needed.
Read `write-agent-context` and the skill-authoring guidance before authoring.
Use existing `ai.skills.authored.<name> = "present"` selection.
Do not introduce enabled/disabled arrays or another deployment path.

| Skill | Required behavior |
| --- | --- |
| `architect-scoping` | Read repository context, gather material questions together, record decisions, and create bounded acceptance criteria with dependency-linked Beads. Use labels `tier:fast`, `tier:standard`, and `tier:deep` for increasing task complexity. Record model selection as a host decision; labels do not assert a specific model is available. |
| `worker-handoff` | Read the assigned issue, atomically claim once, retain the assigned repository/branch, implement only its scope, create follow-up issues for other work, verify, sign, then call the repository shipping task. |
| `repo-bootstrap` | Inspect the repository language and existing tasks. Preserve existing files. Establish real `check`, `test`, and `verify` commands, repository-owned SBX prerequisites, and Beads initialization only through the explicit bootstrap task. Never replace real tests with no-op tasks. |
| `retro-self-improve` | Record a proven failure cause and a small corrective action. Use repository memory for local facts. File a dotfiles follow-up for shared changes; do not cross into another checkout to implement it. |

Installed Beads 1.3.2 help proves dependency direction:

```bash
bd dep add dependent-id --blocked-by prerequisite-id
bd update assigned-id --claim
bd close assigned-id --reason "Merged through the verified PR"
```

`--claim` is atomic and sets `in_progress` plus the assignee.
Use a distinct worker actor identity when concurrent workers share a tracker; a claim by the same actor is idempotent and does not prove exclusive workspace ownership.
Do not claim on the host and then claim again as another guest actor.
For product ambiguity, record all questions in the issue and return incomplete status.
Use a supported blocked state after checking repository status configuration.
Keep unfinished issues open after quota failure, failed verification, or lost sessions.

Workers must run `mise run verify`, make a signed commit, and verify the signature before shipping.
Use `mise run pr:ship` as the shared forge interface.
The shipping task must require checks for the pushed head and confirm the head again before merge.
After a CI failure, use the exact run's failed logs, repair locally, verify, and retry at most twice.
An empty or missing required-check set must not pass.
Close the Bead only after confirmed merge; retain the PR URL, revision, checks, and remaining manual work.

Beads source: [official command documentation](https://github.com/gastownhall/beads/tree/main/docs).
Local evidence: installed `bd dep add --help`, `bd update --help`, and `bd close --help` from version 1.3.2.

## Tests and acceptance

Write behavior tests before changing renderers.
Use real `chezmoi execute-template --with-stdin` and disposable source/target trees.
Use fake CLIs for launch and permission-sensitive behavior.
Do not perform account changes or real publication from tests.

Permissions acceptance:

- Exact selected grants render for Claude and AGY; broad `sbx`, `git push`, and account commands remain absent.
- Overlay `ask`/`deny`, explicit removal, live unrelated entries, and live deny rules behave as documented.
- Retired grants remain selective and repeated rendering is stable.
- Codex host defaults preserve unrelated fields and the exact no-change path.
- The unattended profile is a separate file with supported keys and is absent when disabled.
- Parent-relative rules render, and documentation states their limits.

Skills acceptance:

- All four new skills deploy through the existing owned bundle and disappear when selected `absent`.
- Host-specific selections still work.
- All Markdown links resolve.
- Existing fake-launch checks retain arguments, worker exit codes, logs, and effective sandbox identity.
- The new handoff instructions include claim ownership, real Git metadata, signing, CI head identity, blocked work, and recovery.
- No unconditional host-only Git/signing/publishing rule remains in the modified SBX instruction tree.
- New tests assert observable deployment and launch behavior; avoid tests that only mirror sentence wording.

Run focused integration tests through the repository's mise verification entry point when available.
Run Ruff check/format for changed Python tests and ShellCheck for changed executable examples as appropriate.
Root will run integrated checks, deploy the managed source, and review the result before each signed commit.

## Recorded concerns

No product question needs a new approval round for this scope.
The selected push spelling is an implementation decision that the task implementer must share.
Native AGY file-deny syntax still needs current documentation verification during implementation.
Current shared command-head matching cannot enforce all argument safety rules; do not make stronger claims.
Successful proxy setup alone does not prove every `gh` command works in a guest; retain the end-to-end prerequisite check.
Account signing-key registration and unavailable credential actions remain manual follow-up work.

## Updated tracker and convergence contracts

Use [the host-coordinator tracker route](tracker-route.md) for this implementation.
The host atomically claims and supplies a complete frozen snapshot and actor.
The guest reads that snapshot and must not claim again or require a guest Beads database.
The guest can complete authorized Git and PR work; the host independently confirms the merge and unchanged requirements before authoritative close.
Record unrelated work and blocked questions for the designated tracker owner.
Do not repeat implementation after a confirmed merge when only host close remains pending.

Any manual SBX setting adjustment must have a corresponding Chezmoi source change.
Ordinary apply must correct changes to declared managed values.
Keep missing overlay decisions as a no-op and preserve unmanaged state.

## Codex configuration compatibility

The current [OpenAI configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) confirms separate profile files and both legacy sandbox selectors and named permission profiles.
It forbids combining `default_permissions` with `sandbox_mode` or `sandbox_workspace_write`.
Keep the host and unattended profile on a compatible selector scheme.
Do not add legacy sandbox keys to a valid live configuration that already selects `default_permissions`.
Preserve unrelated settings and named permission definitions.
Test a valid existing modern selector, a valid legacy configuration, and their unattended profile layers.
Use `on-request` on the host and `never` only in the explicit guest profile.
The guest launcher can continue to use supported command-line overrides; it must not assume a host profile file is mounted.

## Configured permission precedence

For catalog `ask`, remove an old exact catalog grant unless the current per-tool configuration explicitly ensures it.
An explicit per-tool ensure remains a tool-specific exception to catalog `ask`.
Catalog `deny` wins and excludes the matching allow from rendered output.
Preserve unrelated ensures, explicit removals, and existing native deny rules.
Do not relax a pre-existing native deny merely because the catalog changes to `allow` or `ask`.
Document that a broad unmanaged allow can still grant a command.

For modern Codex inputs, the managed host selector becomes `:workspace` and named permission definitions remain intact.
Legacy inputs keep a compatible `workspace-write` scheme.
The explicit unattended profile must use the matching selector scheme and must not become the host default.
