---
name: architect-scoping
description: Use when architecture or scoping work must turn accepted requirements into bounded execution units with acceptance criteria and dependencies.
---

# Architect scoping

Coordinate implementation through complete issue units; do not implement features during scoping.

## Establish scope

Read the repository instructions and the authoritative documents for accepted axioms, requirements, and UX acceptance criteria.
Use accepted decisions without requesting approval again.
Gather only missing questions that can change scope, acceptance, ownership, or dependencies, and ask them together.
Continue independent scoping while answers are pending, but mark affected units as incomplete.
Record resolved decisions in the existing authoritative documents and link each unit to its requirements.

## Prepare execution units

Split work into bounded units with a verifiable result and explicit file ownership.
Each unit must state its objective, scope limits, requirement links, acceptance criteria, owned files, prerequisites, checks, and handoff evidence.
Specify the evidence needed to confirm completion, including changed files, check results, and remaining blockers.
Separate work with conflicting file ownership or make its order explicit.
Link each dependency in this direction: `dependent --blocked-by prerequisite`.
Keep independent units independent; do not add dependencies only to impose a sequence.

Use `tier:fast` for routine work, `tier:standard` for ordinary implementation complexity, and `tier:deep` for difficult tradeoffs or substantial uncertainty.
These labels indicate increasing complexity; the host selects models and confirms their availability.

## Hand off to the tracker owner

If you are the designated authorized host tracker owner, create accepted units in the existing tracker and record returned issue IDs and dependency links.
Do not require guest tracker access, a guest database, or a guest claim.
Read installed tool help before including CLI syntax; use issue descriptions and dependency relationships when syntax is unverified.
If you are a delegated or guest scoper, return complete prepared units, dependency links, unresolved questions, and evidence locations to that owner.
Leave affected units incomplete when material inputs are missing.
