# Hands-off SBX work units

- **Author:** Mike Kobit
- **Date:** 2026-11-10
- **Status:** Approved handoff brief; seven Goldfish lenses returned findings.

## Overview

Make work easy to dispatch through agent skills into SBX.
After bootstrap, the guest implements one unit, runs checks, signs and pushes commits, opens a PR, handles CI, merges, reports to the host, and stops without routine host approvals.
Bootstrap and API-key setup can be manual or agent-assisted; routine execution should become near-autonomous.
The host decides the next assignment.
Later, reuse these skills for parallel workers and software-factory, blackboard, or orchestrator patterns.

## User journeys

- **Bootstrap:** Prepare a reproducible sandbox, project tools and checks, scoped credentials, and both project and Chezmoi-injected skills through a short walkthrough.
- **Dispatch:** Give a host agent a prompt, issue, or Bead; it launches the guest and can stop supervising.
- **Pick up queued work:** A guest selects one eligible unit through the project's tools, claims it where supported, completes it, reports, and stops.
- **Extend later:** Compose the proven execution path into parallel or continuing work.

## Analysis

Reviewers identified recovery, duplicate-claim, workspace, and merge-evidence gaps; these do not authorize a larger helper or generic tracker framework.
Use native SBX features where sufficient and add automation only for a demonstrated gap.
Expect investigation to establish the working path, with progress tied to exit criteria.
Consider SBX and kit upgrades during bootstrap when they can resolve a blocker; record tested versions and compatibility, and preserve guest work before planned recreation.

## Goals vs. non-goals

- Merge after all required project CI passes and the unit's acceptance criteria are met.
- Support projects without trackers; evaluate Beads, its CLI, and labels where useful.
- Let scope permit design, model choice, and delegation; use small units and acceptance-based progress to control token waste.
- Resolve routine failures with judgment, waits, retries, evidence, and follow-up work; preserve the checks and acceptance criteria.
- Return hard blockers involving major unknowns, uncontrolled growth, rearchitecture, or coupling as preserved work and actionable tasks, issues, comments, or specification questions.
- Preserve enough state to resume after quota stops or crashes without repeating completed actions.
- Start with GitHub; Forgejo, Tangled, and factory coordination are later extensions.

## Alternatives weighed

- **Direct dispatch or queue pickup:** Start with the agreed direct-dispatch pilot; evaluate queue pickup afterward, with Beads optional.
- **Workspace modes:** Verify isolation, guest Git, signing, skills, and change return per project before choosing or migrating modes.
  A direct-mounted full checkout can support Git; a linked host worktree cannot resolve metadata outside its mount.
- **Existing branch:** Reassess its contents against these journeys; historical plans are not a required sequence.

## Key decisions and staging for next steps

**Confirmed:** One assigned unit ends with merge, a host summary, and guest exit.
Beads is optional.
The dedicated GPG signing subkey must not expose the primary private key to guests.

**Agreed first proof:** Dispatch an `agy` release update with explicit acceptance and exit criteria.
It needs release queries through `gh api`, `curl`, or equivalent, with retry and backoff; then verification, signed commits, PR creation, CI handling, merge, and a host summary.
Use this proof to establish scoped SBX access.

**Open design work:** Verify scoped forge credentials, required-check selection, skill delivery, project bootstrap, and signing; define minimal progress and resume state that reconciles external actions before retrying.
Queue claim and recovery rules are needed if queue pickup is selected.
Hard token caps depend on controls exposed by each agent.
Canopy and Storagemaxxing are later candidates for checking existing Beads and OpenSpec use; their local paths remain unverified.

**Implementation baseline:** Shared branch `feat/sbx-rearch` was at `d9b02bbc` before this handoff brief; [draft PR #1014](https://github.com/mkobit/dotfiles/pull/1014) has no proven guest-to-merged-PR result.
Local sandbox `dotfiles-sbx-delivery` has working private-clone Git and GitHub API access, but signing and project checks remain unproved.
Its last checked-out branch was `main`; mise and Chezmoi are missing, the older custom kit is incompatible with the current native Codex kit, and subkey provisioning is pending.
Other repositories have not been audited or changed.

Refresh the branch inventory for handoff:

```sh
git fetch origin
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git diff origin/main...HEAD
```

<details>
<summary>Branch file inventory: 80 files</summary>

Snapshot: feature `d9b02bbc`, fetched `origin/main` `dc6381d7` on 2026-11-10.
This uses `origin/main...HEAD`, which shows branch work since the merge base.
It does not include newer main-only changes, this handoff brief, or local sandbox and credential state.
The descriptions identify purpose; they do not certify that each change should be retained.

`C/` means `src/chezmoi/`.
`S/` means `src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/`.
`A` means added; `M` means modified.
Historical plans and reports are review inputs, not instructions to execute their old checklists.

| Change | File | Rough purpose |
| --- | --- | --- |
| A | [.agent-workflow.json](.agent-workflow.json) | Lists required CI check names. |
| M | [.gitignore](.gitignore) | Tracks the SBX kit and excludes task context and logs. |
| A | [.sbx/kit/install.sh](.sbx/kit/install.sh) | Installs the earlier guest toolchain. |
| A | [.sbx/kit/spec.yaml](.sbx/kit/spec.yaml) | Declares the earlier repository toolchain kit. |
| A | [.sbx/sbxenv.yaml](.sbx/sbxenv.yaml) | Declares the pinned, direct-mounted Codex environment. |
| M | [mise.toml](mise.toml) | Adds repository lint, type, test, and build tasks. |
| A | [notes/sbx-rearch-follow-ups.md](notes/sbx-rearch-follow-ups.md) | Lists manual setup and deferred work. |
| A | [notes/sbx-rearch-plan.md](notes/sbx-rearch-plan.md) | Records the earlier broad implementation checklist. |
| A | [notes/sbx-rearch-progress.md](notes/sbx-rearch-progress.md) | Records historical checkpoints, decisions, and remaining work. |
| A | [notes/sbx-rearch-tasks/architect-skill-report.md](notes/sbx-rearch-tasks/architect-skill-report.md) | Records architect skill validation. |
| A | [notes/sbx-rearch-tasks/bootstrap-skill-report.md](notes/sbx-rearch-tasks/bootstrap-skill-report.md) | Records bootstrap skill validation and limits. |
| A | [notes/sbx-rearch-tasks/ci-parser-contract.md](notes/sbx-rearch-tasks/ci-parser-contract.md) | Proposes CI check parsing and completion rules. |
| A | [notes/sbx-rearch-tasks/configuration.md](notes/sbx-rearch-tasks/configuration.md) | Describes workflow configuration and overlay choices. |
| A | [notes/sbx-rearch-tasks/env-model-contract.md](notes/sbx-rearch-tasks/env-model-contract.md) | Records verified SBX model interface limits. |
| A | [notes/sbx-rearch-tasks/environment-report.md](notes/sbx-rearch-tasks/environment-report.md) | Records earlier guest environment checks. |
| A | [notes/sbx-rearch-tasks/guest-task-contract.md](notes/sbx-rearch-tasks/guest-task-contract.md) | Proposes guest task input and delivery interfaces. |
| A | [notes/sbx-rearch-tasks/interfaces.md](notes/sbx-rearch-tasks/interfaces.md) | Lists shared workflow interfaces. |
| A | [notes/sbx-rearch-tasks/kit-reproduction-report.md](notes/sbx-rearch-tasks/kit-reproduction-report.md) | Records earlier fresh-kit creation checks. |
| A | [notes/sbx-rearch-tasks/macos-ci-fix.md](notes/sbx-rearch-tasks/macos-ci-fix.md) | Records the macOS ancestor-path repair. |
| A | [notes/sbx-rearch-tasks/macos-ci-investigation.md](notes/sbx-rearch-tasks/macos-ci-investigation.md) | Investigates the macOS apply failure. |
| A | [notes/sbx-rearch-tasks/mise-kit-assessment.md](notes/sbx-rearch-tasks/mise-kit-assessment.md) | Assesses the earlier upstream mise kit. |
| A | [notes/sbx-rearch-tasks/model-routing-report.md](notes/sbx-rearch-tasks/model-routing-report.md) | Records model-routing validation. |
| A | [notes/sbx-rearch-tasks/model-routing.md](notes/sbx-rearch-tasks/model-routing.md) | Describes proposed local model routing. |
| A | [notes/sbx-rearch-tasks/permissions-report.md](notes/sbx-rearch-tasks/permissions-report.md) | Records permission changes and checks. |
| A | [notes/sbx-rearch-tasks/repo-verify-report.md](notes/sbx-rearch-tasks/repo-verify-report.md) | Records repository verification and its latency-test limit. |
| A | [notes/sbx-rearch-tasks/schema-report.md](notes/sbx-rearch-tasks/schema-report.md) | Records workflow schema checks. |
| A | [notes/sbx-rearch-tasks/setup-report.md](notes/sbx-rearch-tasks/setup-report.md) | Records SBX setup checks. |
| A | [notes/sbx-rearch-tasks/setup.md](notes/sbx-rearch-tasks/setup.md) | Describes SBX settings, proxy, and skill setup. |
| A | [notes/sbx-rearch-tasks/skills.md](notes/sbx-rearch-tasks/skills.md) | Describes proposed workflow skill roles. |
| A | [notes/sbx-rearch-tasks/task7-refinement.md](notes/sbx-rearch-tasks/task7-refinement.md) | Proposes the larger host claim, review, resume, and delivery helper. |
| A | [notes/sbx-rearch-tasks/tasks.md](notes/sbx-rearch-tasks/tasks.md) | Proposes global task commands and helper behavior. |
| A | [notes/sbx-rearch-tasks/tracker-route.md](notes/sbx-rearch-tasks/tracker-route.md) | Proposes host-managed claims and tracker closure. |
| A | [notes/sbx-rearch-tasks/worker-skill-report.md](notes/sbx-rearch-tasks/worker-skill-report.md) | Records worker skill validation. |
| A | [notes/sbx-rearch-work-machine.md](notes/sbx-rearch-work-machine.md) | Describes cross-machine and offline collaboration. |
| A | [notes/sbx-rearch.md](notes/sbx-rearch.md) | Contains the original broad workflow design. |
| M | [C/.chezmoi.toml.tmpl](src/chezmoi/.chezmoi.toml.tmpl) | Adds personal workflow, sandbox, signing, and model choices. |
| M | [C/.chezmoidata/ai/command_policy/gh.toml](src/chezmoi/.chezmoidata/ai/command_policy/gh.toml) | Revises GitHub workflow command grants. |
| M | [C/.chezmoidata/ai/command_policy/git.toml](src/chezmoi/.chezmoidata/ai/command_policy/git.toml) | Revises Git workflow command grants. |
| M | [C/.chezmoidata/ai/command_policy/mise.toml](src/chezmoi/.chezmoidata/ai/command_policy/mise.toml) | Adds proposed workflow task grants. |
| A | [C/.chezmoidata/ai/workflow.toml](src/chezmoi/.chezmoidata/ai/workflow.toml) | Defines workflow capability metadata and safe defaults. |
| M | [C/.chezmoidata/codex.toml](src/chezmoi/.chezmoidata/codex.toml) | Adds Codex workflow modifier controls. |
| M | [C/.chezmoiignore.tmpl](src/chezmoi/.chezmoiignore.tmpl) | Gates unattended Codex and Pi files by feature choices. |
| A | [C/.chezmoiscripts/run_after_06_configure-sbx-workflow.sh.tmpl](src/chezmoi/.chezmoiscripts/run_after_06_configure-sbx-workflow.sh.tmpl) | Configures global SBX settings, policy, and GitHub resolver. |
| A | [C/.chezmoiscripts/run_after_07_sync-sbx-skills.sh.tmpl](src/chezmoi/.chezmoiscripts/run_after_07_sync-sbx-skills.sh.tmpl) | Copies selected skills and imports the bundle into SBX. |
| A | [C/.chezmoiscripts/run_after_08_configure-local-models.sh.tmpl](src/chezmoi/.chezmoiscripts/run_after_08_configure-local-models.sh.tmpl) | Configures global SBX local-model routing. |
| M | [C/AGENTS.md](src/chezmoi/AGENTS.md) | Documents workflow permission and deployment rules. |
| M | [C/dot_claude/modify_settings.json](src/chezmoi/dot_claude/modify_settings.json) | Updates Claude command and file permission handling. |
| M | [C/dot_codex/modify_private_config.toml](src/chezmoi/dot_codex/modify_private_config.toml) | Preserves base Codex settings while selecting workspace permissions. |
| A | [C/dot_codex/modify_private_unattended.config.toml](src/chezmoi/dot_codex/modify_private_unattended.config.toml) | Generates the separate unattended Codex profile. |
| M | [C/dot_config/opencode/modify_opencode.json](src/chezmoi/dot_config/opencode/modify_opencode.json) | Adds optional Ollama routing to OpenCode. |
| M | [C/dot_gemini/antigravity-cli/modify_settings.json](src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json) | Updates Antigravity command and file permission handling. |
| M | [S/AGENTS.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/AGENTS.md) | Changes shared sandbox skill and delivery guidance. |
| A | [S/exact_architect-scoping/SKILL.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_architect-scoping/SKILL.md) | Adds planning, scope, and task decomposition guidance. |
| A | [S/exact_repo-bootstrap/SKILL.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_repo-bootstrap/SKILL.md) | Adds repository workflow adoption guidance. |
| M | [S/exact_sbx-orchestrator/SKILL.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/SKILL.md) | Changes delegated sandbox execution guidance. |
| A | [S/exact_sbx-orchestrator/exact_references/delivery.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/delivery.md) | Documents guest verification, signing, PR, CI, and merge steps. |
| M | [S/exact_sbx-orchestrator/exact_references/host-supervisor.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/host-supervisor.md) | Changes the host supervisor contract. |
| M | [S/exact_sbx-orchestrator/exact_references/nested-execution.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/nested-execution.md) | Changes workspace ownership and autonomous delivery rules. |
| M | [S/exact_sbx-orchestrator/exact_references/recovery.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/recovery.md) | Changes durable context and recovery guidance. |
| M | [S/exact_sbx-orchestrator/exact_references/subagent-task.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/subagent-task.md) | Changes guest task prompts and authority. |
| A | [S/exact_sbx-orchestrator/exact_references/tracker.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/tracker.md) | Adds host-managed tracker claim and close guidance. |
| M | [S/exact_sbx-orchestrator/exact_references/worker-launch.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-orchestrator/exact_references/worker-launch.md) | Changes guest launch and task-context guidance. |
| M | [S/exact_sbx-sandboxes/SKILL.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-sandboxes/SKILL.md) | Connects sandbox use to the revised delivery guidance. |
| M | [S/exact_sbx-sandboxes/exact_references/agents.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-sandboxes/exact_references/agents.md) | Updates agent execution guidance. |
| M | [S/exact_sbx-sandboxes/exact_references/permissions.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-sandboxes/exact_references/permissions.md) | Updates sandbox task authority guidance. |
| M | [S/exact_sbx-sandboxes/exact_references/repository-setup.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_sbx-sandboxes/exact_references/repository-setup.md) | Updates repository and guest readiness guidance. |
| A | [S/exact_worker-handoff/SKILL.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_worker-handoff/SKILL.md) | Adds the guest work-unit execution skill. |
| A | [S/exact_worker-handoff/exact_references/assignment.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_worker-handoff/exact_references/assignment.md) | Defines guest assignment guidance. |
| A | [S/exact_worker-handoff/exact_references/delivery.md](src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_worker-handoff/exact_references/delivery.md) | Defines guest verification and delivery guidance. |
| A | [C/dot_pi/agent/modify_private_models.json](src/chezmoi/dot_pi/agent/modify_private_models.json) | Adds optional Pi model-provider configuration. |
| A | [C/dot_pi/agent/modify_private_settings.json](src/chezmoi/dot_pi/agent/modify_private_settings.json) | Selects the optional Pi model route. |
| M | [tests/integration/test_ai_environment_fixtures.py](tests/integration/test_ai_environment_fixtures.py) | Aligns isolated AI fixtures with native plugin discovery. |
| A | [tests/integration/test_ai_workflow_permissions.py](tests/integration/test_ai_workflow_permissions.py) | Tests workflow permissions and setting preservation. |
| A | [tests/integration/test_ai_workflow_skills.py](tests/integration/test_ai_workflow_skills.py) | Tests skill deployment, selection, links, and cleanup. |
| M | [tests/integration/test_codex_tui_modify.py](tests/integration/test_codex_tui_modify.py) | Updates Codex modifier regression coverage. |
| M | [tests/integration/test_docker_sandboxes_skill.py](tests/integration/test_docker_sandboxes_skill.py) | Updates sandbox skill regression coverage. |
| A | [tests/integration/test_ollama_routing.py](tests/integration/test_ollama_routing.py) | Tests local-model routes and repeated apply. |
| A | [tests/integration/test_sbx_skill_sync.py](tests/integration/test_sbx_skill_sync.py) | Tests skill import ownership, collisions, retries, and cleanup. |
| A | [tests/integration/test_sbx_workflow.py](tests/integration/test_sbx_workflow.py) | Tests workflow schema, defaults, and overlay choices. |
| A | [tests/integration/test_sbx_workflow_setup.py](tests/integration/test_sbx_workflow_setup.py) | Tests SBX setup calls, settings, policy, and proxy handling. |

</details>
