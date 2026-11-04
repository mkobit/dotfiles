# Worker skill verification

Scope: task 5a, SBX authority and `worker-handoff`.
The later architect, bootstrap, and improvement skills are separate units.

## First checks

The deployment baseline failed 5 tests because `worker-handoff` was absent; 65 existing tests passed.
The first implementation passed 70 focused tests and 42 broader authored-skill fixture tests.
Ruff, format, three frontmatter checks, and 81 local file and heading links passed.
These checks did not prove safe review order or mixed selections.

## Scenario exercise

Use the same five fixed application cases before and after the change.
The readers received source instructions and case facts, but no rubric or prior answers.
The cases are planning exercises; they do not authorize real publication.

| Case | Baseline | First implementation | Repair |
| --- | --- | --- | --- |
| Verified guest delivery | 0: forbids authorized guest Git delivery | 0: permits delivery but can merge before host review | 2 |
| Host claim route | 2 | 2 | 2 |
| CI head change | 2 | 2 | 2 |
| Interrupted session | 2 | 2 | 2 |
| Settings convergence | 2 | 2 | 2 |

Both initial totals are 8 of 10.
The first implementation permits guest delivery, but its review order still fails the authority rule.
The green reader assigns the guest to shipping and merge, then assigns independent review to the host without a preceding review gate.
Do not report the unchanged controls as baseline failures.

Local case identity: SHA256 `56c76116684f0dd2ea8be2984eca0d60305d2c1eb3dbbe0f4f21e8b3eb6af4a9`.
The first source manifest is SHA256 `4bf348ab1c0672b534012d84a38c779c7032aa0edc2193176e6d68482a1f08d3`.
Detailed local records are under `.sbx/task-context/skills/` and `.sbx/task-context/skills-worker/`.

## Independent review

Review reproduced an autonomous merge path before independent host review.
It also reproduced a successful overlay apply with an installed orchestrator and a missing required worker delivery reference.
The reviewer independently ran both focused test modules: 70 passed.

The original guest owns both repairs.
Require root-dispatched acceptance for the final tested head before merge, and invalidate acceptance when that head changes.
Keep required references local to each independently selected skill.
## Repair checks

The mixed-selection regression run failed 6 tests before the repair.
The repair passed 76 focused tests and 42 broader tests, with 16 deselected.
The only later source change was the worker trigger description.
Final Ruff, format, three frontmatter checks, and 86 file and heading links passed after that correction.
An extra focused attempt stopped at quota and has no completed result.
It is not counted as passed.

All 26 final source hashes match manifest SHA256 `7f027a697768b7cb23bb0fddb3ba2218abbedd26985531b4062e53ba54dd89bf`.
No guest writer or child check remained at recovery.

A fresh reader applied the same five cases to the repaired source.
The score is 10 of 10.
Its delivery answer permits guest signing and PR preparation, then requires `review-ready` and root acceptance for the same tested head before merge.
All four controls remain safe.
Local answers: `/tmp/sbx-rearch-skill-green-worker-repair.md`.
Independent source re-review resolved both findings and found no new material defect.
The reviewer also verified all 26 source hashes and checked local references without repeating the completed suites.
Root accepted this unit for a signed checkpoint.
