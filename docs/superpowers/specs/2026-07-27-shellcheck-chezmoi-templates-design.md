# Shellcheck for chezmoi-templated shell scripts

## Problem

Chezmoi renders ~20 Go-template files into deployed shell scripts (`.chezmoiscripts/*.tmpl`, root-level `run_onchange_after_*.tmpl`, `modify_*.tmpl`, scattered `executable_*.tmpl` hook/tool wrappers).
None of them are shellchecked today.
`shellcheck` is already in the binary catalog (`.chezmoidata/bin/shellcheck.toml`) and lands on every machine via `chezmoi apply`, but nothing invokes it.

## Goal

Shellcheck every chezmoi-templated shell script, as part of the existing test suite, both in CI and locally.

## Non-goals

- No new `src/python` package or CLI tool.
- No exact line-level mapping from a shellcheck finding back to a source `.tmpl` line — trim markers (`{{-`/`-}}`), conditionals, and `range` loops shift and duplicate lines unpredictably, so an exact map isn't achievable.
- No synthetic multi-data-profile rendering to chase full branch coverage. Coverage is whatever the existing CI matrix (`ubuntu-24.04`, `macos-15`) naturally renders.
- No `pytest-xdist` / parallel test execution. Tests are independent by construction (parametrized), but nothing wires up parallel execution now. An asyncio-based parallel runner was raised as a possible future direction — explicitly deferred, not part of this design.

## Scope: what gets discovered

Four discovery globs, evaluated against the chezmoi source root (not one recursive scan of every `.tmpl` file in the repo):

1. `src/chezmoi/.chezmoiscripts/*.tmpl`
2. `src/chezmoi/run_onchange_after_*.tmpl` (root level only, non-recursive)
3. `src/chezmoi/modify_*.tmpl`
4. `src/chezmoi/**/executable_*.tmpl` (recursive)

Rationale for four narrow globs instead of one broad scan: a fully recursive `**/*.tmpl` would also try to render zellij layouts, JSON/TOML configs, markdown skills, and other non-shell templates, some of which need data contexts this harness doesn't provide.
The four globs above are chezmoi's own naming conventions for "this becomes a script," so they're a safe, self-documenting signal.

Glob 1 broadens the existing `chezmoiscript_path` fixture in `tests/integration/conftest.py`, which currently only matches `run_onchange_after_*.sh.tmpl` — 5 of the 16 files under `.chezmoiscripts/` — and silently misses the other 11 (`run_once_*`, `run_onchange_install-*`).

Glob 3 relies on an existing repo convention: pure Go-template `modify_` scripts (JSON/TOML transforms with no shell at all) deliberately have no `.tmpl` suffix, per `src/chezmoi/AGENTS.md`'s `chezmoi:modify-template` convention.
Requiring the `.tmpl` suffix therefore excludes them with no hardcoded exclusion list.

## Scope: what's actually checked (render-time, not filename-time)

"In scope" is a per-render decision, not a filename decision.
Many templates gate their entire body behind `{{- if ... -}}` (for example the apt install script only renders on Linux) and can render to empty output on a given machine.

For each discovered template:

1. Render it with `chezmoi execute-template`.
2. If the rendered output's first non-blank line is not `#!/bin/bash`, `#!/bin/sh`, `#!/usr/bin/env bash`, or `#!/usr/bin/env sh` — `pytest.skip`. This covers both conditionally-empty renders and non-shell `modify_` transforms that happen to match a glob without a shebang. Checking the first *non-blank* line (not strictly byte 0) tolerates templates that leave a stray leading blank line after rendering.
3. Otherwise, write the rendered text to a temp file and run `shellcheck -x` against it.

## Shellcheck invocation policy

Pass `-x` (follow sourced files).
Several scripts `source` a shared library at a path known only at render time (for example `source "{{ .chezmoi.sourceDir }}/.chezmoitemplates/shell/logging.sh"`), which shellcheck can't resolve by default (SC1091).
Since the harness already renders with the real `.chezmoi.sourceDir`, `-x` lets shellcheck actually resolve and check the sourced file's content too, rather than just suppressing the warning.

## Architecture

Extend the existing `tests/integration/conftest.py` fixture/parametrization idiom — no new package, no new CI job.

- `conftest.py`: broaden (or add alongside) the `pytest_generate_tests` glob logic to cover the four globs above, producing a parametrized path fixture.
- New `tests/integration/test_shellcheck.py`: one test per discovered template, implementing the render → classify → shellcheck steps above.
- Test ID = the source template's path relative to the chezmoi source root. A failure reads as `test_shellcheck[.chezmoiscripts/run_onchange_install-apt-packages.sh.tmpl]` — file-level attribution for free, since each parametrized test corresponds to exactly one source template. No separate source-mapping logic is needed.

## CI and local usage

- CI: runs automatically inside the existing `integration` job's `uv run pytest tests/integration` step, on both OS matrix legs (`ubuntu-24.04`, `macos-15`). No new workflow job.
- Local: `uv run pytest tests/integration -k shellcheck`, same as any other integration test today — requires the same initialized-chezmoi environment the rest of `tests/integration` already assumes.

## Error handling

- A template that fails to render (a genuine template error, not a conditional empty output) should fail the test loudly, not be treated as a skip — skip is reserved for "rendered, but not a shell script."
- Shellcheck's default severity (all findings, including style/info) is used as-is; no `--severity` floor. If the initial run surfaces a high volume of low-value style findings across the ~20 files, that's a signal to revisit during implementation, not a decision to pre-empt here.

## Known consequence, not a blocker

This will be the first time these ~20 files are shellchecked.
Two have been spot-checked already (the apt install script, the pre-commit hook) and pass clean with `-x`.
The rest are unverified — implementation should expect to find and fix genuine pre-existing issues, not just wire up plumbing.

## Testing

The harness itself needs no separate test suite — each parametrized `test_shellcheck` case *is* the test, and `conftest.py`'s glob logic is simple enough to be covered by the fact that every real script in scope shows up as a test ID (a missing template would show up as an obviously-absent test case during implementation review).
