# AI checks

Run commands from the repository root.
Use separate paths under `.scratch/` for temporary files and pytest output.

```sh
mkdir -p .scratch
ai_test_run=$(mktemp -d "$PWD/.scratch/ai-test.XXXXXXXX")
mkdir "$ai_test_run/tmp"
export TMPDIR="$ai_test_run/tmp"
```

## Skill metadata

Run the metadata check for the base configuration:

```sh
mise run check:skill-metadata
```

The task uses the PyYAML requirement pinned in [mise.toml](../../mise.toml), which is separate from `uv.lock`.
To check a different source and rendered configuration, set `PYYAML_SPEC` to that requirement.
Set `AI_CHEZMOI_SOURCE`, `AI_CHEZMOI_CONFIG`, and `AI_CHEZMOI_DESTINATION` to the intended chezmoi paths.
Set `AI_SOURCE_ROOT` to the source directory that contains the plugin folders.

```sh
chezmoi --source "$AI_CHEZMOI_SOURCE" --config "$AI_CHEZMOI_CONFIG" --destination "$AI_CHEZMOI_DESTINATION" data --format json |
  uv run --frozen --with "$PYYAML_SPEC" python scripts/check_skill_metadata.py --source-root "$AI_SOURCE_ROOT" --host codex --config -
```

Run the check for each configuration that needs coverage.

## Focused checks

```sh
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen ty check
uv run --frozen pytest -p no:cacheprovider -m 'not integration' --basetemp "$ai_test_run/pytest" tests/integration/test_ai_plugin_folders.py tests/integration/test_ai_skills.py tests/integration/test_ai_environment_fixtures.py src/python/skill_filter/tests/
```

The pytest marker excludes integration tests that inspect deployed targets.
To check that Antigravity receives the authored plugins, use a fresh `--basetemp` path:

```sh
uv run --frozen pytest --basetemp "$ai_test_run/pytest-agy" tests/integration/test_agy_desired_plugins.py
```

## Overlay validation

Build the overlay with its assembly process and run `chezmoi init` with a temporary destination and separate config, cache, and state paths under `.scratch/`.
Run `chezmoi apply --exclude scripts` against that destination to avoid registering temporary paths with host CLIs.
Use `chezmoi diff` to preview changes to the real destination before applying them.
