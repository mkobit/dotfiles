---
name: test-invariants
description: Use when business constraints, edge cases, or observable outcomes are ambiguous, underspecified, high-risk, or requested for review before writing tests.
---

# Test invariants

Aligns domain invariants with the user in one interactive turn before writing contract tests.

## When to use

Use this skill before writing tests for underspecified, stateful, or high-risk domain behavior, or when the user asks to review test cases first.

## Workflow

1. Inspect only public signatures, data types, and domain documentation for the target unit, supporting both pre-implementation signature stubs and existing modules.
2. Draft a four-column **Contract & Invariant Table** (`| Case / input | Expected observable outcome | Collection / state inspector | Excluded tautology or internal detail |`).
   Every row must name the real production break it catches and state hand-derived literal outcomes rather than change detectors.
3. Present the draft table to the user in a single confirmation turn for approval or inline edits instead of asking open-ended blank-slate questions.
4. Pass the approved table directly to the `black-box-testing` skill.

See [invariant-checklist-and-examples.md](references/invariant-checklist-and-examples.md) for the discovery checklist, "name the break" gate, and table examples.
