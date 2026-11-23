---
name: black-box-testing
description: Use when writing or expanding automated tests from public API contracts, types, and invariant tables without mirroring private implementation branches.
---

# Black-box testing

Authors contract-driven tests in epistemic isolation from private implementation bodies.

## Core mandate

Test observable business constraints through public contracts using hand-derived literal expectations, table-driven parameterization, and iterable or collection inspectors.
Exercise real units and collaborators by default, mocking only slow or external boundaries.
Never mirror internal control flow or assert on a mock itself.

## Dispatch threshold

Spawn a fresh-context subagent when testing a new contract, new module, or multi-branch business invariant.
Edit inline only when appending rows to an existing parameterized test table where the contract signature and assertion structure are already established.

## Subagent isolation and failure-handling protocol

The parent extracts public signatures (`path#L<start>-L<end>`) and sends a **Contract Handoff Payload** containing extracted signatures, the **Contract & Invariant Table**, allowed read slices, and forbidden implementation ranges (or `none (pre-implementation stub)` for contract-first tests).
The subagent runs tests with concise traceback flags, fixes compile or import errors using only allowed read slices, never reads forbidden ranges or weakens assertions when a contract assertion fails, applies a mental mutation check, runs the project's test suite, and returns an **Isolation & Coverage Audit**.

## References

- [handoff-and-isolation.md](references/handoff-and-isolation.md) — Contract Handoff Payload template, read-slice rules, failure-handling protocol, and Isolation & Coverage Audit schema.
- [data-tables-and-inspectors.md](references/data-tables-and-inspectors.md) — Multi-language data tables, collection inspectors, boundary-only mocking, and mutation checks.
