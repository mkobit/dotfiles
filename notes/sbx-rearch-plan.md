# SBX workflow implementation plan

**Goal:** Implement the workflow in [the design note](sbx-rearch.md) in dotfiles first.
**Architecture:** Keep the existing map-based catalogs and overlay control plane.
Run full worker sessions inside repository-owned SBX environments.
Keep host coordination separate from guest execution.
**Tools:** Chezmoi, mise, Python, SBX, Beads, and GitHub CLI.

## Constraints

- Make changes on `feat/sbx-rearch` in `.worktrees/feat-sbx-rearch`.
- Commit each verified unit with a signature.
- Use existing `ai.command_policy.commands` and `ai.skills.authored` maps.
- Put personal opt-ins in `.chezmoi.toml.tmpl`; missing overlay decisions must disable side effects.
- Use `chezmoi.destDir` for target paths.
- Preserve unrelated live configuration and existing custom SBX policy.
- Codify any manual SBX setting mutation in Chezmoi; ordinary apply must correct drift in declared managed values.
- Keep private keys and raw tokens out of prompts, logs, and tracked files.
- Use mise for task and verification entry points.
- Do not change other repositories during this implementation.
- Sandboxes must be essentially fully reproducible from scratch through tracked kits; separate kit repositories are follow-up work.

## Review focus

- An overlay omits or disables a feature: apply must do no feature setup.
- A global task starts in a nested directory: retain the caller repository.
- A worker stops or loses connection: retain ownership, logs, and recovery data.
- A PR head changes or checks are missing: do not merge stale or unverified code.
- Signing, model routing, or authentication is unavailable: report the prerequisite; do not weaken checks.

## Tasks

- [x] 1. Audit current catalogs, source paths, CLI support, and verification.
- [x] 2. Add schema and personal choices with tests for absent, disabled, and overridden decisions.
- [x] 3. Add secret proxy, policy preservation, settings convergence, and skill import with fake CLI tests.
  Guest signing execution and preflight belong to task 7.
- [x] 4. Update permissions through the shared catalog and native modifiers; test live-setting preservation.
- [ ] 5. Update SBX skills and add architect, worker, bootstrap, and improvement skills; test deployment and references.
- [x] 6. Add Ollama routes through native configuration; test disabled and repeated apply behavior.
- [ ] 7. Add global architect, worker, PR, and bootstrap tasks plus repository verify tasks; test command arguments, claim races, branch safety, and CI handling.
- [ ] 8. Run integrated checks, independent review, scoped deployment, and a test-repository handoff.
- [ ] 9. Submit a PR, inspect GitHub checks, repair failures, and record the adoption guide and manual follow-up work.

Each implementation task starts with a failing behavior test where appropriate, then adds the minimum change, runs focused checks, receives independent review, and ends with a signed commit.
Root owns branch management, integration, credentials, and final checks.
Delegates own bounded files and reports; they must preserve other agents' changes.

## Partial task checkpoints

Task 5:

- [x] Update SBX authority and add `worker-handoff`.
- [x] Add `architect-scoping`.
- [x] Add `repo-bootstrap`.
- [ ] Add `retro-self-improve`.

Task 7:

- [x] Add repository verification tasks and explicit required CI names.
- [ ] Add global workflow commands, runtime configuration, and guest task assets.
- [ ] Implement the helper, host claims, review and resume, shipping, and verified host close.

The repository verification declarations are checked in; a complete local verification pass remains open.
See [the recorded timing-test limit](sbx-rearch-tasks/repo-verify-report.md).
All seven GitHub checks passed for source checkpoint `df34665d` in [CI run 41945194862](https://github.com/mkobit/dotfiles/actions/runs/41945194862).

## Interface checks

| Tasks | Shared interface | Resolution |
| --- | --- | --- |
| 2, 3, 6, 7 | Feature selection and model/signing values | Establish data paths in task 2 before consumers change. |
| 3, 5 | Skill import and deployment | Import the owned portable bundle; do not rewrite plugin caches. |
| 4, 5 | Worker authority | Update conflicting host-only instructions with the new guest contract. |
| 5, 7 | Task names and workflow | Use `agent:architect`, `agent:work`, `pr:ship`, and `repo:bootstrap`. |
| 7, 8 | Verification and CI | Verify the pushed PR head and require known checks before merge. |

Task 1 agrees with the source audit.
Tasks 2–6 must preserve native modifier and map semantics.
Task 7 must use actual installed CLI syntax instead of the illustrative scripts.
Tasks 8–9 must report unrun checks and manual prerequisites.
