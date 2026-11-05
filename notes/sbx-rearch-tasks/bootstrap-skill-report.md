# Bootstrap skill verification

Scope: the `repo-bootstrap` skill, its authored catalog entry, and deployment tests.
The global command and CLI helper remain task 7 work.

The fixed incomplete-input case already passed before this unit.
It remains a control: preserve existing files, require a proven test command, and report onboarding as incomplete.
Fourteen new deployment cases failed before the named skill existed.
The full focused module passed 39 tests in 568.38 seconds.
Ruff, format, frontmatter, and preservation checks passed.
All 520 unrelated baseline files remained unchanged, including the tracked kit, configuration, and lockfiles.
The three final source hashes match manifest SHA256 `d4e3b34f3d2e2bbcc42fe3fdcaba68cf580f795bb84f003ec0f8dba57508ea43`.
Root's final native process check returned exit `0` with no active worker or check process.

One independent reviewer applied the fixed case and reviewed the source diff.
The case preserves custom files, requests missing command evidence, and leaves onboarding incomplete.
The review found no material defect.
No test suite was repeated during review.

The guest used a temporary evidence-local virtual environment with `UV_OFFLINE=1` and the frozen dependency lock.
It copied 62 cached packages without network access or a tracked toolchain change.
This is source-test evidence; it does not establish a new kit reproduction result or required setup path.
Do not repeat the suite solely to move its temporary environment.

Local evidence: `.sbx/task-context/bootstrap-skill/`.
Detailed evidence: `.sbx/task-context/bootstrap-skill/guest-report.md`, its `artifacts/green.log`, and `/tmp/sbx-rearch-bootstrap-review.md`.
No live apply, host setting, tracker, credential, or other repository change is part of this unit.
