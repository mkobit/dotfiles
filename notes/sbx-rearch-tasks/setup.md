# Task 3 setup design

Status: Design only.
No task 3 source edits or guest worker launch occurred.
Task 2 is signed at `7ace1fcb`.
Wait for root to verify fresh creation from the tracked native kit.
Start a new guest session in that verified environment.
Do not resume the task 2 session in a different environment.
Do not install tools or patch guest environment values after creation.

## Settings, policy, and resolver

Add `src/chezmoi/.chezmoiscripts/run_after_06_configure-sbx-workflow.sh.tmpl`.
Render setup only when `ai.sandbox.provider == "sbx"` and the SBX installation method is not `none`.
Use safe `dig` defaults from the accepted schema.
Keep `ai.workflow.enabled` as the global task gate; do not add a second setup opt-in.
Leave the existing `kit_allowed_sources` catalog and setup script unchanged.
Use noninteractive commands, compare before setting, and report unavailable SBX as skipped.

For an explicit `sbx.settings.skills_default_mode`, read `sbx settings get skills.defaultMode`.
Set only a different supported value with `sbx settings set skills.defaultMode VALUE`.
Support `readonly`, `readwrite`, and `off`.
Missing mode performs no setting operation.

For explicit `ai.sandbox.network_policy = "balanced"`, read `sbx policy ls --type network --format json`.
The observed v0.50.1 response is an object with a `rules` array.
Preserve every existing rule, including custom, scoped, kit, and organization rules.
Do not run `policy reset`, `allow`, `deny`, or `rm`.
An unreadable or invalid response prevents initialization and produces a skip report.
When no rules exist, use the native one-time `sbx policy init balanced` operation.
The list response does not expose a separate initialized flag.
An already initialized empty policy therefore cannot be distinguished through the verified list interface.
The one-time init command must refuse an existing policy; report that refusal without reset or retry.
Record this empty-policy limit in tests and the handoff.
Other network policy selections perform no initialization.

For explicit `ai.sandbox.proxy_gh_secret = true`, read `sbx secret ls --global --service github --format json`.
The observed response is `{"secrets": []}`.
With no global GitHub entry, configure `sbx secret set github --command 'gh auth token'`.
Keep native source verification enabled.
Do not call `gh auth token` directly, capture its output, use `--token`, use `--show-error`, or print command resolver output.
If an existing record exposes documented source type and resolver metadata, compare it before a change.
If existing metadata cannot prove the resolver, preserve the entry and report that the desired resolver was not verified.
Do not invent fields from the empty live sample.
Fake fixtures for nonempty records need a primary source or explicit uncertainty in the report.

## Authored skill copies and native import

Use real portable copies already deployed under `{{ .chezmoi.destDir }}/.local/share/agent-plugins/marketplace/plugins/mkobit-dotfiles/skills`.
Select only `ai.skills.authored` entries with state `present` for new import copies.
Keep tool-specific authored selections unchanged.
Do not alter plugin caches, the portable bundle, or other skill directories.

Preferred bounded implementation: Add `src/chezmoi/.chezmoiscripts/run_after_07_sync-sbx-skills.sh.tmpl`.
The hook materializes selected portable files under `{{ .chezmoi.destDir }}/.agents/skills/<name>`.
This is a chezmoi source script executed by normal apply; no external renderer expansion is needed for this design.
Use the existing Python interpreter selector and standard-library filesystem checks.
Reject symlink components and nested symlinks.
Never replace an existing unowned directory or file.
Report a collision and preserve that source.

Maintain a task-owned receipt under `{{ .chezmoi.destDir }}/.local/state/dotfiles/sbx-skills-ownership.json`.
Record skill names, copied relative files, and content digests after successful operations.
Use bounded validated paths and atomic receipt replacement, following existing cleanup patterns.
Update only files whose current identity matches the last receipt.
Remove stale copied files or disabled skill copies only when the receipt proves ownership and their current bytes still match.
Preserve added or changed non-owned files and report the collision.
Remove an empty owned directory only after its owned files are removed.
If provider or sync is disabled, a missing receipt means no setup.
A prior receipt may permit cleanup of only the old owned copies; it must not trigger new import or settings setup.

After copies are ready and sync is explicitly enabled, use the native `sbx skills import --force`.
Root confirms that native all-root synchronization is authorized.
It scans all supported host roots and can replace existing shared-store skills.
Do not add a separate engine or require ownership of all existing import candidates.
Use the owned source fingerprint and import receipt to avoid unnecessary import when the owned payload is unchanged.
An unavailable SBX service leaves a pending import and reports a skip; a later normal apply retries it.
Do not mark a failed import as complete in the receipt.

Native removal exists: `sbx skills rm --force NAME`.
Automatic removal requires a prior successful owned import receipt and current store identity evidence.
Do not infer current store ownership from a name or stale receipt alone.
If native metadata cannot prove identity, keep the store entry and report its exact stale name for manual review.
The import command replaces obsolete files within a skill; it does not claim to prune skills whose source directory disappeared.
Store pruning remains a recorded limitation until safe current identity evidence is verified.

## Signing interface for task 7

Task 3 adds no signing file and does not mutate Git settings.
Task 7 consumes `ai.signing.mode`, `ai.signing.ssh_public_key`, and `ai.signing.gpg_subkey_id` directly.
Missing mode is `host-default`.
SSH mode requires an explicit public key or a successful guest signing test with the existing configured key.
GPG mode requires an explicit signing subkey and successful guest signing proof.
No first-key selection, key creation, private-key export, or host global Git change is authorized.
Signing execution and preflight belong to the global helper in task 7.

## Exact proposed files

- New `src/chezmoi/.chezmoiscripts/run_after_06_configure-sbx-workflow.sh.tmpl`.
- New `src/chezmoi/.chezmoiscripts/run_after_07_sync-sbx-skills.sh.tmpl`.
- New `tests/integration/test_sbx_workflow_setup.py`.
- New `tests/integration/test_sbx_skill_sync.py`.

The existing authored external renderer and cleanup script need no changes under the preferred hook design.
Root also permits their expansion if implementation evidence shows that it is necessary.
Such expansion must preserve current host deployment maps and tool-specific selections.
No command policy, authored skill catalog, skill source, model modifier, dependency, or lockfile change is in this unit.

## Required test evidence

Start with failing executable behavior tests, then implement and repair in the new guest session.
Use fake SBX plus real chezmoi rendering with isolated destination, config, cache, and state.
Cover missing and disabled decisions, overlay overrides, compare-before-set, unavailable CLI/service, policy preservation, resolver no-op/unknown metadata, repeated apply, source collisions, changed owned files, nested links, source updates, authored removal, pending failed imports, and shared-store removal refusal without identity evidence.
Run focused new tests plus existing SBX and workflow schema tests.
Run focused Ruff lint and format checks.
Record exact commands, exits, passed/skipped counts, native limitations, and unrun live checks.

## Verified CLI facts

Host CLI: `sbx version v0.50.1 ddb0268d7124b9cf98955d0b08ffd71a0dfcebe4`.
All help and read-only metadata commands exited 0.

`sbx skills import --help` has only `--dry-run` and `--force` operation flags.
It has no source or per-skill selection option.
Root precedence is `.agents/skills`, `.claude/skills`, `.config/opencode/skills`, `.copilot/skills`, `.cursor/skills`, then `.factory/skills`.
The first copy wins.
Top-level directory symlinks are followed; internal symlinks are skipped.
Import completely replaces an existing skill and removes its obsolete files.

`sbx skills add --help` accepts a Git URL or GitHub repository shorthand and an optional repeatable `--skill` selector.
It does not document a local directory or direct shared-store sync source.
Do not substitute a speculative local `add` workflow.

`sbx secret set --help` documents host command resolvers and `--no-verify`; keep verification enabled.
Resolver execution uses a fresh host temporary directory outside writable mounts.
`gh auth token` uses the installed host CLI and needs no repository-relative helper.

Sources: installed `sbx` v0.50.1 command help; `src/ai/AGENTS.md`; `src/chezmoi/.chezmoiexternals/ai-authored-skills.toml.tmpl`; existing authored cleanup scripts.
