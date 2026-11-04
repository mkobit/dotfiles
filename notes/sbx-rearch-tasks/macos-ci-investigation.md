# macOS CI investigation

Status: Confirmed Task 3 path-validation defect.
No repository file, guest, live setting, or tool installation was changed.
The investigation used the supplied CI log, current source, and an in-memory comparison of the exact hook program.

## Failed step and exact evidence

Run: `41652944917`, source commit `bbc2e758`.
Job: `integration (macos-15)`.
Failed step: `Run chezmoi apply`.
No pytest test failed; apply stopped before the integration test step.
The supplied [CI log](/tmp/sbx-rearch-ci-macos-41652944917.log) contains the failed-step evidence.

At `2026-11-03T14:25:23.3402330Z`, attempt 1 reports:

```text
sbx-skills: refusing symlink path: /tmp
chezmoi: .chezmoiscripts/07_sync-sbx-skills.sh: exit status 1
```

The same error occurs on attempts 2 through 6.
Attempt 6 reports it at `2026-11-03T14:36:46.1933860Z`.
The step exits 1 at `2026-11-03T14:36:46.3210190Z`.
Homebrew and global mise install/lock/prune completed before the first hook error.
The six-attempt retry loop explains the job duration; it does not change this deterministic failure.

## Confirmed cause

The workflow sets `CHEZMOI_DEST=/tmp/chezmoi-test` in [CI destination](/home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch/.github/workflows/ci.yml:32).
The macOS log also shows the same physical target as `/private/tmp/chezmoi-test` during mise locking.
Task 3's `checked()` in [Sync path checks](/home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch/src/chezmoi/.chezmoiscripts/run_after_07_sync-sbx-skills.sh.tmpl:61) starts at the filesystem root and rejects every existing symlink component, including ancestors above the supplied destination.
Its `lstat()` test rejects macOS's `/tmp` alias before reaching any managed path.

This occurs even with sync disabled and no prior ownership receipt.
Personal init selects provider `none` and SBX installation method `none` on Darwin.
The sync hook still renders to permit safe cleanup of old owned copies.
`main()` at line 337 checks `exists(state_file)` before returning from the disabled/no-receipt case.
`exists()` calls `checked()`, which rejects `/tmp`.
The top-level error handler exits 1.
Thus the no-op path itself prevents ordinary macOS apply.

Linux uses the same `/tmp/chezmoi-test` spelling, but ordinary Linux `/tmp` is a directory.
The supplied Linux success result is consistent with this one differing path property.
No network error or task receipt failure is present in this failed step.

Confidence: High.
The exact error, source call path, OS alias evidence, six repeated attempts, and isolated one-variable reproduction agree.

## Smallest read-only reproduction

The probe extracts the current embedded Python body without editing it.
It runs that exact body with a nonexistent destination, `enabled=false`, and no selected skills.
The probe changes only the in-memory `Path.lstat('/tmp')` result using `unittest.mock`.
No directory or receipt is created, and no SBX command is called.

```text
ordinary Linux /tmp : exit 0 ; stderr: (empty)
macOS /tmp alias : exit 1 ; stderr: sbx-skills: refusing symlink path: /tmp
Repository and filesystem unchanged; no guest or live service called.
```

Core reproduction:

```python
body = source.split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
# Supply sys.argv = ['sync-hook', '/tmp/sbx-ci-investigation-41652944917-nonexistent', 'false', '[]'].
# Patch only Path.lstat('/tmp').st_mode from stat.S_IFDIR to stat.S_IFLNK.
exec(compile(body, "current-sync-hook", "exec"), {})
```

This validates the failure mechanism on Linux without a macOS guest or filesystem changes.
It does not replace a native macOS verification run after the eventual repair.

## Smallest fix and regression recommendation

Keep the supplied destination as the trust boundary.
Resolve trusted parent aliases above that boundary once, or start descendant validation at a verified destination boundary.
Continue to reject a symlinked destination itself and symlinks inside managed source/copy/receipt paths.
Do not use blanket `resolve()` on each target path, because that would hide managed-path symlinks from validation.
Do not bypass the disabled cleanup path; it must still clean only receipt-owned copies when a receipt exists.

Add an isolated test with an alias in an ancestor above destDir, equivalent to `/tmp -> /private/tmp`.
Cover disabled sync without a receipt (exit 0 and no mutation), enabled sync (copy/import succeeds), and disabled cleanup with a prior receipt.
Keep the existing managed-source, `.agents`, receipt-parent, file, and nested-symlink rejection cases.
Then run the focused sync/setup suites and native macOS apply/test job.

No further CI data is required to identify this cause.
The repair and its regression test are not implemented by this read-only task.

## Scope and source evidence

The new sync hook was introduced by `bbc2e758` (`feat(sbx): converge workflow settings and owned skills`).
Current investigation worktree HEAD is `6995493f`; another active permissions worker owns the dirty policy/config files.
Those edits were preserved and no second guest was started.

Relevant local sources:

- [Sync path checks](/home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch/src/chezmoi/.chezmoiscripts/run_after_07_sync-sbx-skills.sh.tmpl:61) — ancestor validation.
- [Disabled receipt check](/home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch/src/chezmoi/.chezmoiscripts/run_after_07_sync-sbx-skills.sh.tmpl:337) — disabled receipt check.
- [Destination and error handler](/home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch/src/chezmoi/.chezmoiscripts/run_after_07_sync-sbx-skills.sh.tmpl:386) — supplied destination and error handler.
- [Darwin provider decision](/home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch/src/chezmoi/.chezmoi.toml.tmpl:15) and [installation decision](/home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch/src/chezmoi/.chezmoi.toml.tmpl:135) — Darwin opt-out decisions.
- [CI destination](/home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch/.github/workflows/ci.yml:32) — CI destination.
- [Existing symlink tests](/home/mkobit/.local/share/chezmoi/.worktrees/feat-sbx-rearch/tests/integration/test_sbx_skill_sync.py:222) — existing checks cover managed descendants, not the external OS ancestor alias.
