# Shellcheck for chezmoi-templated shell scripts

## Problem

Chezmoi manages roughly 35 shell scripts and shell-producing templates (`.chezmoiscripts/*`, root-level `run_onchange_after_*`, `modify_*`, scattered `executable_*` hook/tool wrappers — templated and plain alike).
None of them are shellchecked today.
`shellcheck` is already in the binary catalog (`.chezmoidata/bin/shellcheck.toml`) and lands on every machine via `chezmoi apply`, but nothing invokes it.

## Goal

Shellcheck every shell script chezmoi manages — templated or not — as part of the existing test suite, both in CI and locally.

## Non-goals

- No new `src/python` package or CLI tool.
- No exact line-level mapping from a shellcheck finding back to a source `.tmpl` line — trim markers (`{{-`/`-}}`), conditionals, and `range` loops shift and duplicate lines unpredictably, so an exact map isn't achievable.
- No synthetic multi-data-profile rendering to chase full branch coverage. Coverage is whatever the existing CI matrix (`ubuntu-24.04`, `macos-15`) naturally renders.
- No `pytest-xdist` / parallel test execution. Tests are independent by construction (parametrized), but nothing wires up parallel execution now. An asyncio-based parallel runner was raised as a possible future direction — explicitly deferred, not part of this design.

## Scope: what gets discovered

Discovery asks chezmoi itself what it manages, via `chezmoi managed`, rather than walking the filesystem with hand-maintained globs.
Chezmoi already knows which files it deploys and how each one is classified, so asking it directly is correct by construction instead of a filename convention that can silently drift out of sync with the source tree — a root-level-only or `.tmpl`-suffix-only glob has already proven capable of missing real, in-scope files (see below).

Two queries against the chezmoi source root, both filtered to entries whose `sourceAbsolute` exists as a real file on disk:

1. `chezmoi managed --include=scripts --format=json --path-style=all` — every `run_once_`/`run_onchange_`/etc. script chezmoi will execute, anywhere in the source tree.
   This is chezmoi's own `scripts` entry type, not a name-pattern guess, so no further filter is applied beyond the on-disk check: whatever chezmoi classifies as an executable script is in scope, including nested `.chezmoiscripts/` directories elsewhere in the tree (for example `dot_local/share/fonts/.chezmoiscripts/run_onchange_after_install-wsl-windows-fonts.sh.tmpl`, which a root-level-only glob would miss).
2. `chezmoi managed --include=files --format=json --path-style=all`, filtered to entries whose `sourceRelative` basename starts with `modify_` or `executable_` — the *source* basename, not the deployed target's: chezmoi strips these prefixes on deploy (`modify_dot_bashrc.tmpl`'s target is `.bashrc`, not `modify_.bashrc`), so filtering on `absolute`'s basename instead would silently match nothing.
   chezmoi's `files` type is much broader than shell scripts — every deployed skill markdown copy, JSON config, and static asset shows up here too — so a name-prefix filter is still needed to keep candidate count sane.
   Unlike a filesystem glob, this filter matches basenames with or without a `.tmpl` suffix, so a plain, non-templated `executable_*` script is discovered the same way a templated one is (for example `dot_local/bin/tools/executable_chezmoi-git-prompt` and `dot_local/share/ai/hooks/executable_worktree-context.sh`, neither of which is a chezmoi template at all).
   `--include=files` only (not `files,symlinks`) is deliberate: zero symlink-managed entries have a `modify_`/`executable_`-prefixed basename today, so this isn't a live gap — but if a future symlink-attributed script-like entry is ever added, it'd need `files,symlinks` to stay discoverable.

The on-disk-existence filter is required, not optional, on the `files` query: naively filtering by basename alone also matches roughly 100 entries under `dot_claude/skills/`, `dot_codex/skills/`, `dot_cursor/skills/`, and `dot_gemini/antigravity-cli/skills/` — vendored upstream AI skill scripts materialized at apply time by `.chezmoiexternals/ai-skills.toml.tmpl` and `.chezmoiexternals/ai-authored-skills.toml.tmpl`, never physically present in `src/chezmoi` (confirmed: `dot_claude/skills/` doesn't exist on disk in the source tree, and `git ls-files` finds nothing there).
Shellchecking vendored, pinned-upstream script content is out of scope — this repo doesn't author it and shouldn't fail CI every time an external ref bumps.
Checking `Path(sourceAbsolute).is_file()` excludes all of them with no special-casing of `.chezmoiexternals/` internals; applying the same check to the `scripts` query too is a no-op today (all 20 are real files) but keeps both queries consistent if an external ever materializes a script-type entry.

Each JSON entry carries `sourceRelative` (used for the test ID) and `sourceAbsolute` (used for both the on-disk filter above and the render step below); `absolute` (the deployed target path) is returned too but isn't used by this design.

Both queries run at collection time (`pytest_generate_tests`, mirroring how `chezmoiscript_path` is parametrized today), before any per-test fixture — including `host` — exists.
That means they must follow `_chezmoi_source_path()`'s existing pattern (a raw `subprocess.run` call), not `_chezmoi_command`'s (`host.run`, only available inside a test).
`_chezmoi_argv` itself needs a small extension to support this: today it only ever emits `--config`/`--destination` (from `CHEZMOI_CONFIG`/`CHEZMOI_DEST`) — `--source` is currently hardcoded separately inside `_chezmoi_source_path()`, not parameterized through `_chezmoi_argv` at all.
Discovery needs `--source`/`--config`/`--destination` together, so `_chezmoi_argv` (or an equivalent collection-time helper) needs `--source` support before these queries can be threaded through it — this is a real, small code change, not existing plumbing.
Chezmoi resolves relative to `$HOME` by default, which isn't where CI's checkout lives, so none of these three flags are optional.

The `modify_`/`executable_` name-prefix filter doesn't need to separately exclude pure Go-template `modify_` scripts (JSON/TOML transforms with no shell at all, deliberately given no `.tmpl` suffix per `src/chezmoi/AGENTS.md`'s `chezmoi:modify-template` convention) — those render with no shebang and are skipped by the classification step below, the same as any other non-shell candidate.

## Scope: what's actually checked (render-time, not filename-time)

"In scope" is a per-render decision, not a filename decision.
Many templates gate their entire body behind `{{- if ... -}}` (for example the apt install script only renders on Linux) and can render to empty output on a given machine.

For each discovered entry:

1. Render it with `chezmoi execute-template -f --with-stdin <sourceAbsolute>` (the source path `chezmoi managed` already returned), threaded through the same `--source`/`--config`/`--destination` flags described above.
   Feed empty stdin explicitly (e.g. `subprocess.run(..., input="")`, not a bare inherited stdin) — `--with-stdin` is required, not optional: without it, rendering any file using this repo's `chezmoi:modify-template` convention (`dot_claude/modify_settings.json`, `dot_codex/modify_config.toml`, `dot_gemini/antigravity-cli/modify_settings.json`) hard-errors (`executing "..." at <.chezmoi.stdin>: map has no entry for key "stdin"`), because those templates reference `.chezmoi.stdin` directly. Feeding empty stdin resolves the reference without hanging the test waiting on a real pipe.
   This design originally used `chezmoi cat <target-path>` here instead, on the theory that it's the same code path a real `chezmoi apply` uses. That holds for `scripts`-type and non-`modify_` `executable_*` entries, but is wrong for `modify_`-prefixed ones: `chezmoi cat` on a `modify_` target runs the *entire* modify pipeline — feeding the current destination file's real content into the script and returning its transformed output — not the modify script's own source. Verified: `chezmoi cat ~/.bashrc` (the target of `modify_dot_bashrc.tmpl`) returns ordinary `.bashrc` content with no shebang, which would silently route all 7 of this repo's legacy executable `modify_*.tmpl` scripts (real `#!/bin/sh` logic: `mktemp`, `trap`, `sed`, heredocs) to `pytest.skip` at the classification step below — a false negative indistinguishable from a correctly-skipped non-shell file, reading as a clean run while shellcheck never actually looks at them. `chezmoi execute-template -f <sourceAbsolute>` renders the template's own source instead, sidestepping stdin dispatch entirely, and is confirmed to produce identical output to `chezmoi cat` for every other entry type.
   Bare, unflagged chezmoi calls fail on most files in CI's actual layout regardless of which command is used — `chezmoi source-path` resolves relative to `$HOME`, which in CI is not where `actions/checkout` puts the repo, so `.chezmoidata/*` never loads and any template reading catalog data hard-errors (reproduced: `map has no entry for key "packages"`). This is not optional plumbing, it's required for the render step to work at all outside a real `chezmoi apply`.
   A template that fails to render exits non-zero with the render error on stderr — that's what distinguishes a genuine template error from a conditional empty render (see Error handling): only the latter is a `pytest.skip`.
2. Classify the rendered output by its first non-blank line (checking the first *non-blank* line, not strictly byte 0, tolerates templates that leave a stray leading blank line after rendering).
   Recognize a shell shebang by tokenizing, not exact string match: strip the leading `#!`, split on whitespace, and accept it if the resolved interpreter token's basename is `bash` or `sh` — direct (`/bin/bash`, `/bin/sh`, or any path ending in `/bash` or `/sh`) or via `env` (`/usr/bin/env bash`, `/usr/bin/env -S bash`, skipping `env`'s own flags to find the interpreter token).
   Anything else — no shebang, or a shebang for a different interpreter — is a `pytest.skip`.
   This covers both conditionally-empty renders and non-shell `modify_`/skill-file transforms that happen to match the discovery filter without a shebang, and it doesn't silently stop matching the moment a script's shebang line grows a flag (`#!/bin/bash -e`) or gains a space (`#! /bin/sh`).
3. Otherwise, write the rendered text to a temp file and run `shellcheck -x` against it.

## Shellcheck invocation policy

Pass `-x` (follow sourced files).
Several scripts `source` a shared library at a path known only at render time (for example `source "{{ .chezmoi.sourceDir }}/.chezmoitemplates/shell/logging.sh"`), which shellcheck can't resolve by default (SC1091).
Since the harness already renders with the real `.chezmoi.sourceDir`, `-x` lets shellcheck actually resolve and check the sourced file's content too, rather than just suppressing the warning.

`-x` only resolves the *direct* form above (11 of 12 call sites).
`run_onchange_install-ollama.sh.tmpl` uses the two-statement indirection `src/chezmoi/AGENTS.md`'s "Sourcing Shared Libraries" section documents as canonical — `CHEZMOI_SOURCE_DIR="{{ .chezmoi.sourceDir }}"` on one line, `source "${CHEZMOI_SOURCE_DIR}/..."` on the next — which `-x` cannot trace even though the value is fully static post-render (reproduced: still SC1091).
Fix: add `# shellcheck source={{ .chezmoi.sourceDir }}/.chezmoitemplates/shell/logging.sh` (a *template expression*, rendering to an absolute path) on the line immediately above the `source "${CHEZMOI_SOURCE_DIR}/..."` call in that script (and any future script using this indirected form) — `source=` is shellcheck's explicit override for exactly this case, a source target it can't statically resolve even under `-x`.
A relative `source=` path (e.g. `.chezmoitemplates/shell/logging.sh`) resolves against shellcheck's own CWD, not the checked file's location or the file's own directory — verified: with a relative directive, `SC1091` still fires from both the repo root and `/tmp` (the CWDs that matter — `conftest.py`'s tests always run from the repo root) and only clears when CWD happens to equal `src/chezmoi` itself. Since the harness writes rendered output to an isolated temp file and shellcheck runs from pytest's CWD (the repo root), a relative directive fails in exactly the environment this design runs in. The rendered-absolute form isn't CWD-sensitive at all (verified clean, `SC1091=0`, from both the repo root and `/tmp`) — it must be the one implemented, not the relative form.
This is the default and only change this design requires; updating the AGENTS.md sourcing convention to the direct form instead is a valid alternative but is a separate, repo-wide documentation decision, not a prerequisite for this feature — don't block implementation on it.

## Architecture

Extend the existing `tests/integration/conftest.py` fixture/parametrization idiom — no new package, no new CI job.

- `conftest.py`: add a new parametrized fixture alongside the existing `chezmoiscript_path` one (don't broaden it in place) — `chezmoiscript_path` is already consumed by `test_lock_enforcement.py`, and coupling that test's parametrization count to this feature's scope is an unnecessary entanglement between two unrelated checks. The new fixture's parametrization comes from parsing the two `chezmoi managed --format=json` queries above, not from `Path.glob`.
- New `tests/integration/test_shellcheck.py`: one test per discovered entry, implementing the render → classify → shellcheck steps above.
- Test ID = the entry's `sourceRelative` path. A failure reads as `test_shellcheck[.chezmoiscripts/run_onchange_install-apt-packages.sh.tmpl]` — file-level attribution for free, since each parametrized test corresponds to exactly one source entry. No separate source-mapping logic is needed.

## CI and local usage

- CI: runs automatically inside the existing `integration` job's `uv run pytest tests/integration` step, on both OS matrix legs (`ubuntu-24.04`, `macos-15`). No new workflow job.
- Local: `uv run pytest tests/integration -k shellcheck`, same as any other integration test today — requires the same initialized-chezmoi environment the rest of `tests/integration` already assumes.

## Error handling

- A template that fails to render (a genuine template error, not a conditional empty output) should fail the test loudly, not be treated as a skip — skip is reserved for "rendered, but not a shell script."
- Shellcheck's default severity (all findings, including style/info) is used as-is; no `--severity` floor. If the initial run surfaces a high volume of low-value style findings across the ~32 shellcheck-eligible files, that's a signal to revisit during implementation, not a decision to pre-empt here.
- Single-machine rendering can produce spurious findings, not just miss coverage: a data-dependent loop (e.g. a `range` over configured extensions) that happens to iterate zero times on the rendering machine can trigger a real shellcheck finding (e.g. `SC2034` unused variable) for a variable that *is* used once the loop actually iterates elsewhere.
  Confirmed case: `dot_config/mise/tasks/executable_install-gemini-extensions.tmpl` fails `SC2034` on both CI OS legs because this machine's `.gemini.extensions` is empty, so the `range` block that reads `RUN_CMD` never renders.
  Policy: a scoped inline `# shellcheck disable=<code>` directive at the specific line, with a comment stating it's a render artifact and why (for example `# shellcheck disable=SC2034 -- unused when .gemini.extensions is empty on this machine; consumed inside the range loop below`).
  Decide case-by-case, at the finding, never as a blanket disable for a whole file or check class — the two options this design already forbids (a `--severity` floor, synthetic multi-profile rendering) stay forbidden; this is the escape hatch for the specific finding, not a general-purpose override.

## Known consequence, not a blocker

This will be the first time most of these files are shellchecked: 20 scripts-type entries plus 15 real (on-disk) `modify_`/`executable_` files, of which 3 are pure JSON/TOML `modify_` transforms that self-skip at classification — roughly 32 shellcheck-eligible files in total across the CI matrix, not the ~20 the original scope estimate assumed before switching discovery to `chezmoi managed`.
32 is a union count, not a fixed per-run count: OS-gated templates (e.g. the apt install script, Linux-only) render empty and self-skip on whichever CI leg doesn't match, so expect a smaller, matrix-leg-dependent number of scripts actually reaching `shellcheck` on any single `ubuntu-24.04` or `macos-15` run.
Two have been spot-checked already (the apt install script, the pre-commit hook) and pass clean with `-x`.
One confirmed pre-existing issue is documented above (the `RUN_CMD` `SC2034` render artifact in `executable_install-gemini-extensions.tmpl`).
The rest are unverified — implementation should expect to find and fix further genuine pre-existing issues, not just wire up plumbing.

## Testing

The harness itself needs no separate test suite — each parametrized `test_shellcheck` case *is* the test, and `conftest.py`'s discovery logic (two `chezmoi managed` queries, a basename filter, an on-disk-existence filter) is simple enough to be covered by the fact that every real script in scope shows up as a test ID (a missing entry would show up as an obviously-absent test case during implementation review).
