# Schema verification

Task 2 adds `ai.workflow`, `ai.sandbox`, `ai.signing`, and `ai.ollama` capability maps.
Personal choices remain in the init template.
The existing skill and command maps remain unchanged.
Skills mode uses `sbx.settings.skills_default_mode`.
No executable setup or live deployment is part of this checkpoint.

## Checks

- Focused pytest before implementation: 5 failed and 17 passed; failures identified missing schema values.
- Focused pytest after implementation: 22 passed, 0 skipped.
- Ruff lint and format checks: passed.
- Isolated real Chezmoi init render and data load: passed.
- Host diff check: passed.
- Independent source review: approved; no important findings.

Command: `mise exec -- uv run pytest tests/integration/test_sbx_workflow.py tests/integration/test_sbx.py -q`.
The guest used Python `3.14.7` and an isolated virtual environment.
Full CI, apply, signing, and model checks remain pending.

## Source changes

- `src/chezmoi/.chezmoidata/ai/workflow.toml`
- `src/chezmoi/.chezmoi.toml.tmpl`
- `tests/integration/test_sbx_workflow.py`

The original guest required manual setup.
A fresh kit creation test must pass before later worker launches.
