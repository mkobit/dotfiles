# Chezmoi test data fixture design

## Context

The base dotfiles repo runs integration tests with `pytest` and `pytest-testinfra`.
The testinfra `host` fixture runs command and filesystem assertions against the applied environment.
CI initializes chezmoi with explicit `--source`, `--destination`, and `--config`, applies the source state, then runs `pytest tests/integration`.

Several tests currently encode feature assumptions directly.
`agy` tests assume the CLI is always on `PATH`.
The chezmoi data already has `agy.installation_method`, but tests do not consume it.

## Goals

Expose rendered chezmoi data to integration tests as a first-class pytest fixture.
Use rendered data for conditional test execution.
Keep enabled and disabled behavior as separate tests where the disabled state has a meaningful assertion.
Add lightweight data contract tests without introducing a schema system.

## Non-goals

Do not parse source TOML or Go templates directly from Python.
Do not introduce a full schema validation framework.
Do not implement `agy` uninstall behavior in this change.
Do not gate all Antigravity assets on `agy.installation_method`.

## Installation method contract

`agy.installation_method = "dotfiles.script"` means chezmoi installs `agy` and tests expect it on `PATH`.
`agy.installation_method = "preinstalled"` means another system installs `agy`, and tests still expect it on `PATH`.
`agy.installation_method = "none"` means chezmoi does not install `agy`, and tests expect it not to be on `PATH`.
`agy.installation_method = "uninstall"` is reserved for future explicit removal behavior.

Antigravity config and assets remain separate from the CLI installation decision for now.
This preserves the current external generation behavior while making CLI expectations data-driven.

## Fixture design

Add a `chezmoi_data` fixture in `tests/integration/conftest.py`.
The fixture runs `chezmoi data --format=json` from the test environment and returns a Python dict.
The fixture should use the initialized context instead of source-file parsing.

Add small helpers for reading installation methods from the data dict.
The helper should support top-level feature keys such as `agy`.
The helper should return `"none"` when a key is absent unless the test explicitly asserts key presence.

## Declarative test gating

Add a custom pytest marker named `chezmoi_installation`.
The marker accepts a feature name and a set of allowed methods.
An autouse fixture reads the marker, reads `chezmoi_data`, and skips the test when the active method is not allowed.

Example:

```python
@pytest.mark.chezmoi_installation("agy", methods={"dotfiles.script", "preinstalled"})
def test_agy_version(host):
    ...
```

Use the same marker for disabled assertions:

```python
@pytest.mark.chezmoi_installation("agy", methods={"none"})
def test_agy_not_on_path(host):
    ...
```

This keeps conditional execution declarative and keeps test bodies free of feature-gate branching.

## Test updates

Add always-run data contract tests for `agy.installation_method`.
The tests should assert the key exists and the value is one of the supported methods.

Split `agy` path behavior into separate enabled and disabled tests.
The enabled test asserts `command -v agy` succeeds for `dotfiles.script` and `preinstalled`.
The disabled test asserts `command -v agy` fails for `none`.

Gate `agy --version` behind `dotfiles.script` and `preinstalled`.
There is no useful disabled equivalent for version execution.

Keep settings and legacy-removal assertions separate from CLI installation.
Changing Antigravity assets to share the `agy.installation_method` gate is outside this change.

## Verification

Run the focused integration tests after the red and green TDD steps.
Run the full integration suite if the focused tests pass and the local environment can support it.
Run formatting and linting for touched Python files.
