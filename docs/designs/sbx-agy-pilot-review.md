# SBX agy pilot review record

**Target:** [SBX agy release-update pilot](sbx-agy-pilot.md).
**Branch:** `feat/sbx-rearch`.
**Review date:** 2026-11-11.
**Original reviewed revision:** `f71153608cc83ba78acda7d85a648310f5dc7756` (`f7115360`).
**Result:** All five findings are resolved in the design.
Design acceptance does not prove implementation or runtime operation.

## Initial review

Ten fresh reviewers completed all five stages without checkpoint pauses.
No reviewer failed or needed a retry.
The review found three Major findings, two Nits, and no Blockers.
The architecture reviews required no change to the selected pilot architecture.

| Stage | Reviewer roles | Findings |
| --- | --- | --- |
| Initial zoom out | Architecture, inventive catalyst | None |
| Comprehension | Naive reader | None |
| Critic review | Design, structure, style | One Major, one Nit |
| Intermediate zoom out | Architecture | No additional findings |
| Implementation readiness | Readiness, codebase details, style | Two Major, one Nit |

## Resolutions

The user supplied the decisions for these design changes.
All five findings were accepted for correction.
No finding was contested, escalated, or declined.

| Finding | Severity | Accepted design resolution |
| --- | --- | --- |
| A1: Undefined OpenCode permission merge | Major | Defer OpenCode and retain four policy tools: Claude Code, Antigravity, Codex, and Cursor. |
| A2: Native validation when SBX is absent | Major | Add macOS installation through Chezmoi init and require CLI checks and native offline validation in enabled CI jobs. A missing CLI fails those jobs. |
| A3: Unsupported author attribution | Major | Remove the attribution from alternatives and retain the technical reasons. |
| A4: Historical baseline written as current state | Nit | Mark the research commits and observations as historical. |
| A5: Unclear fresh-guest acceptance sequence | Nit | Assign basic guest proof to unit 5 and final signing, restart, tracker, model, and subagent proof to unit 10. |

The additional approved scope is a bounded cleanup plan in unit 12.
It names nine obsolete plan and assignment files for later removal.
It also specifies updates to the brief, progress note, follow-up note, and verification record.
Unique evidence must remain available, and retained links and references must be checked before removal.
No file was deleted during this design revision.

The macOS resolution uses the [Docker installation guide](https://docs.docker.com/ai/sandboxes/install/) and [official Homebrew cask](https://raw.githubusercontent.com/docker/homebrew-tap/main/Casks/sbx.rb) as its source basis.
The design separates the macOS cask version from the Linux `0.51.0` pin.
Its CI plan uses the [offline validator](https://docs.docker.com/reference/cli/sbx/kit/validate/) and the [GitHub-hosted runner limits](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).
Hosted CI must prove installation, CLI operation, and offline kit validation; a capable host must prove guest startup and delivery.

## Targeted re-audit and limits

Three fresh reviewers checked the changed sections for codebase details, structure, and style.
They reported no remaining findings in those sections.
This was one targeted re-audit, not a second full five-stage review.
Each original and re-audit reviewer used `fork_turns: none` to exclude parent-turn history.
Host instruction-file exclusion remains unverified.
The original raw reports remain local records of the reviewed revision.

No implementation, runtime test, CI run, installation, or configuration apply was performed during this review and revision.
No production file, key, tracker issue, sandbox, or remote repository was changed.
Signing, native replica sync, runtime policy enforcement, and live delivery still need implementation evidence.

## Next work

The design and this review record form the design commit on `feat/sbx-rearch`.
Follow the approved specification in separate small branches from the accepted base.
Historical plans are not implementation authority.
The first bounded unit is central SBX policy and the existing renderers.
Design acceptance gives no automatic permission to access keys, change trackers, or launch guests.
