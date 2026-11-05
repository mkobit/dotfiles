# Setup implementation verification

Task 3 adds ordinary-apply hooks for SBX settings and owned authored-skill copies.
Setup uses explicit sandbox provider and installation decisions.
The global workflow task flag does not gate setup.

## Verified behavior

- Restore declared skills mode after an external change and retry failed reads or writes on the next apply.
- Preserve existing policy and unknown credential metadata.
- Register the selected GitHub command resolver without reading or printing its token.
- Copy real portable authored files without changing plugin caches or unrelated files.
- Preserve user content and mode changes.
- Save pending file identity before replacement so interrupted new and updated copies recover on the next apply.
- Include ordinary file mode bits in ownership and import fingerprints.
- Keep failed imports pending for a later apply.

## Evidence

- Final suite: 137 passed, 0 skipped in 123.80 seconds.
- Focused review regressions: 21 passed.
- Ruff lint and format checks: passed.
- Real Chezmoi rendering and Bash syntax checks: passed.
- Root ShellCheck `0.11.0`: passed for both enabled hooks with global workflow disabled.
- Native read-only `sbx settings get skills.defaultMode`: returned the expected plain value `readonly`.
- Independent review found two P2 defects; the scoped repair review confirmed both addressed and found no new important defect.
- No worker or check process remained active at handoff.
- No live settings, credentials, keys, or plugin caches changed during tests.

Final suite command:

```sh
mise exec -- uv run --frozen pytest tests/integration/test_sbx_workflow_setup.py tests/integration/test_sbx_skill_sync.py tests/integration/test_sbx_workflow.py tests/integration/test_sbx.py -q
```

Guest tools: Python `3.14.7`, pytest `9.1.1`, Ruff `0.17.0`, uv `0.12.10`, mise `2026.10.23`, and Chezmoi `2.74.0`.
The verified kit supplied the tools and environment without manual setup.
Detailed prompts, reports, and logs remain under `.sbx/task-context/config-task3/` on the home worktree.

## Remaining limits

The native policy list does not distinguish an initialized empty policy; refused one-time initialization is reported without reset.
Existing GitHub entries with unverified metadata remain unchanged and are reported.
Store deletion needs current identity evidence; stale names are retained and reported if that proof is unavailable.
Unreleased version 1 receipts are rejected unchanged for manual review because their file mode ownership is unknown.
Broad CI and live deployment remain final integration gates.
Signing execution belongs to task 7 and model routing to task 6.
