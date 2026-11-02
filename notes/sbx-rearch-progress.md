# SBX workflow progress

Plan: [Implementation plan](sbx-rearch-plan.md).
Branch: `feat/sbx-rearch`.
Base: `7aa2fb19`.
Workspace: `.worktrees/feat-sbx-rearch`.

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

## Current state

Task 1 is complete.
SBX execution readiness is under inspection.
No implementation code has changed.

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
