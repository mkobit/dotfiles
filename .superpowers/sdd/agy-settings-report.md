# Agy settings cleanup report

## Scope

Changed only `src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json` and `tests/integration/test_antigravity.py`.

The disabled template path now removes stale `statusLine` and `title` keys from existing JSON.

The enabled path remains configured with the exact `statusline antigravity render` command.

## RED evidence

Command: `uv run pytest tests/integration/test_antigravity.py -m integration -k 'statusline_template_removes_stale_settings_when_disabled'`.

Result before the template change: failed because `statusLine` remained in the rendered JSON, with stale `title` also present.

## Rendered JSON checks

Enabled input containing stale `title` and `statusLine` rendered `statusLine.type = "command"`, `statusLine.command = "statusline antigravity render"`, and `statusLine.enabled = true`, with no `title` field.

Disabled input containing stale `title` and `statusLine` rendered `{}`.

## Verification

`uv run pytest tests/integration/test_antigravity.py -m integration -k 'statusline_template'` — 2 passed.

`UV_CACHE_DIR=$(mktemp -d) uv run ruff check tests/integration/test_antigravity.py` — all checks passed.

`UV_CACHE_DIR=$(mktemp -d) uv run ruff format --check tests/integration/test_antigravity.py` — 1 file already formatted.

Direct `chezmoi execute-template` renders for `preinstalled` and `none` matched the enabled and disabled checks above.

## Commit

Implementation commit: `458b728` (`fix agy disabled settings cleanup`).

## Concerns

No known concerns.
