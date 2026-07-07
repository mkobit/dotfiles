# Chezmoi test data fixture implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add rendered chezmoi data as a pytest fixture and use it for declarative integration test gating.

**Architecture:** Keep reusable data helpers in `tests/integration/chezmoi_test_data.py`.
Keep pytest fixture wiring and marker enforcement in `tests/integration/conftest.py`.
Keep behavior assertions in focused test files so enabled and disabled states are separate tests.

**Tech stack:** Python 3.14, `pytest`, `pytest-testinfra`, `chezmoi data --format=json`.

---

## File structure

- Create `tests/integration/chezmoi_test_data.py`.
  This file owns pure helper functions for reading `installation_method` values from rendered chezmoi data.
- Create `tests/integration/test_chezmoi_data.py`.
  This file owns always-run data contract tests and direct helper tests.
- Modify `tests/integration/conftest.py`.
  This file owns the `chezmoi_data` fixture and `chezmoi_installation` marker enforcement.
- Modify `tests/integration/test_cli_tools.py`.
  This file owns shell `PATH` assertions for CLI tools, including enabled and disabled `agy` path behavior.
- Modify `tests/integration/test_antigravity.py`.
  This file owns Antigravity-specific assertions, including gated `agy --version` execution and ungated config checks.

## Task 1: Add pure installation method helpers

**Files:**
- Create: `tests/integration/chezmoi_test_data.py`
- Create: `tests/integration/test_chezmoi_data.py`

- [ ] **Step 1: Write failing helper tests**

Create `tests/integration/test_chezmoi_data.py` with this content:

```python
import pytest

from chezmoi_test_data import SUPPORTED_INSTALLATION_METHODS, installation_method


def test_installation_method_reads_top_level_feature():
    data = {"agy": {"installation_method": "preinstalled"}}

    assert installation_method(data, "agy") == "preinstalled"


def test_installation_method_defaults_missing_feature_to_none():
    assert installation_method({}, "agy") == "none"


def test_installation_method_defaults_missing_method_to_none():
    assert installation_method({"agy": {}}, "agy") == "none"


def test_supported_installation_methods_include_agy_contract():
    assert SUPPORTED_INSTALLATION_METHODS == frozenset({"dotfiles.script", "preinstalled", "none", "uninstall"})


@pytest.mark.integration
def test_chezmoi_data_contains_agy_installation_method(chezmoi_data):
    assert "agy" in chezmoi_data
    assert installation_method(chezmoi_data, "agy") in SUPPORTED_INSTALLATION_METHODS
```

- [ ] **Step 2: Run helper tests to verify they fail**

Run:

```bash
uv run pytest tests/integration/test_chezmoi_data.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'chezmoi_test_data'
```

- [ ] **Step 3: Add the helper module**

Create `tests/integration/chezmoi_test_data.py` with this content:

```python
from collections.abc import Mapping
from typing import Any

SUPPORTED_INSTALLATION_METHODS = frozenset({"dotfiles.script", "preinstalled", "none", "uninstall"})


def installation_method(data: Mapping[str, Any], feature: str) -> str:
    feature_data = data.get(feature)
    if not isinstance(feature_data, Mapping):
        return "none"

    method = feature_data.get("installation_method", "none")
    if not isinstance(method, str):
        return "none"

    return method
```

- [ ] **Step 4: Run helper tests to verify the helper portion passes and the fixture portion fails**

Run:

```bash
uv run pytest tests/integration/test_chezmoi_data.py -q
```

Expected:

```text
fixture 'chezmoi_data' not found
```

- [ ] **Step 5: Commit helper tests and helper module**

Run:

```bash
git add tests/integration/chezmoi_test_data.py tests/integration/test_chezmoi_data.py
git commit -m "Add chezmoi data helper tests"
```

## Task 2: Add the `chezmoi_data` fixture and marker enforcement

**Files:**
- Modify: `tests/integration/conftest.py`
- Test: `tests/integration/test_chezmoi_data.py`

- [ ] **Step 1: Replace `tests/integration/conftest.py`**

Replace the full file with this content:

```python
import json
from collections.abc import Iterable
from pathlib import Path

import pytest

from chezmoi_test_data import installation_method


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as a system integration test.")
    config.addinivalue_line(
        "markers",
        "chezmoi_installation(feature, methods): run only when feature installation_method is in methods.",
    )


@pytest.fixture(autouse=True)
def skip_unmatched_chezmoi_installation(request):
    marker = request.node.get_closest_marker("chezmoi_installation")
    if marker is None:
        return

    if len(marker.args) != 1 or not isinstance(marker.args[0], str):
        raise ValueError("chezmoi_installation marker requires exactly one feature name argument")

    methods = marker.kwargs.get("methods")
    if not isinstance(methods, Iterable) or isinstance(methods, str):
        raise ValueError("chezmoi_installation marker requires a methods set")

    feature = marker.args[0]
    allowed_methods = frozenset(methods)
    active_method = installation_method(request.getfixturevalue("chezmoi_data"), feature)

    if active_method not in allowed_methods:
        allowed = ", ".join(sorted(allowed_methods))
        pytest.skip(f"{feature}.installation_method is {active_method!r}; expected one of: {allowed}")


@pytest.fixture()
def chezmoi_data(host):
    """Return rendered chezmoi data from the initialized test environment."""
    result = host.run("chezmoi data --format=json")
    assert result.rc == 0, f"chezmoi data failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"
    return json.loads(result.stdout)


@pytest.fixture()
def chezmoi_source_root():
    """Return the absolute path to the chezmoi source directory (src/chezmoi)."""
    return Path(__file__).parent.parent.parent / "src" / "chezmoi"


@pytest.fixture()
def chezmoi_dest(host):
    """Return the absolute path to the chezmoi destination (usually $HOME)."""
    result = host.run("chezmoi target-path")
    if result.rc == 0:
        return Path(result.stdout.strip())
    return Path(host.user().home)


def pytest_generate_tests(metafunc):
    """Dynamically parameterize tests that require layout_name."""
    if "layout_name" in metafunc.fixturenames:
        source_root = Path(__file__).parent.parent.parent / "src" / "chezmoi"
        layout_dir = source_root / "dot_config" / "zellij" / "layouts"

        layouts = []
        if layout_dir.exists():
            layouts = [p.name.removesuffix(".kdl.tmpl") for p in layout_dir.glob("*.kdl.tmpl")]

        metafunc.parametrize("layout_name", layouts)
```

- [ ] **Step 2: Run data tests to verify they pass**

Run:

```bash
uv run pytest tests/integration/test_chezmoi_data.py -q
```

Expected:

```text
5 passed
```

- [ ] **Step 3: Run ruff on touched test support files**

Run:

```bash
uv run ruff check tests/integration/conftest.py tests/integration/chezmoi_test_data.py tests/integration/test_chezmoi_data.py
```

Expected:

```text
All checks passed!
```

- [ ] **Step 4: Commit fixture and marker support**

Run:

```bash
git add tests/integration/conftest.py tests/integration/chezmoi_test_data.py tests/integration/test_chezmoi_data.py
git commit -m "Add rendered chezmoi data fixture"
```

## Task 3: Gate `agy` CLI path tests declaratively

**Files:**
- Modify: `tests/integration/test_cli_tools.py`
- Test: `tests/integration/test_cli_tools.py`

- [ ] **Step 1: Verify the current disabled-state bug in an `agy = none` environment**

Run this in an environment where `chezmoi data --format=json` reports `"agy": {"installation_method": "none"}`:

```bash
uv run pytest tests/integration/test_cli_tools.py::test_agy_available -q
```

Expected:

```text
FAILED tests/integration/test_cli_tools.py::test_agy_available
```

- [ ] **Step 2: Replace `tests/integration/test_cli_tools.py`**

Replace the full file with this content:

```python
import pytest


@pytest.mark.integration
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
@pytest.mark.parametrize("binary", ["fzf", "rg", "eza", "bat", "zoxide", "btop", "pi"])
def test_cli_tool_available(host, binary, shell_cmd):
    """Verify each CLI binary is on PATH in bash and zsh."""
    if binary == "btop" and host.system_info.type == "darwin":
        pytest.skip("btop is not managed via chezmoi on macOS (no static binary available from upstream)")
    result = host.run(f"{shell_cmd} 'command -v {binary}'")
    assert result.rc == 0, f"'{binary}' not found via {shell_cmd!r}.\nstderr: {result.stderr}"


@pytest.mark.integration
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
def test_opencode_available(host, shell_cmd):
    """Verify opencode is on PATH in bash and zsh, if supported by the OS."""
    if host.system_info.type == "darwin":
        pytest.skip("opencode is currently disabled on macOS")
    result = host.run(f"{shell_cmd} 'command -v opencode'")
    assert result.rc == 0, f"'opencode' not found via {shell_cmd!r}.\nstderr: {result.stderr}"


@pytest.mark.integration
def test_opencode_help(host):
    """Verify opencode --help runs successfully on supported platforms."""
    if host.system_info.type == "darwin":
        pytest.skip("opencode is currently disabled on macOS")
    result = host.run("opencode --help")
    assert result.rc == 0, f"'opencode --help' failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"


@pytest.mark.integration
@pytest.mark.chezmoi_installation("agy", methods={"dotfiles.script", "preinstalled"})
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
def test_agy_available(host, shell_cmd):
    """Verify agy is on PATH in bash and zsh when enabled."""
    result = host.run(f"{shell_cmd} 'command -v agy'")
    assert result.rc == 0, f"'agy' not found via {shell_cmd!r}.\nstderr: {result.stderr}"


@pytest.mark.integration
@pytest.mark.chezmoi_installation("agy", methods={"none"})
@pytest.mark.parametrize("shell_cmd", ["bash -l -c", "zsh -l -c"])
def test_agy_not_available(host, shell_cmd):
    """Verify agy is not on PATH in bash and zsh when disabled."""
    result = host.run(f"{shell_cmd} 'command -v agy'")
    assert result.rc != 0, f"'agy' was found via {shell_cmd!r} despite agy.installation_method = 'none'"
```

- [ ] **Step 3: Run focused CLI tests**

Run:

```bash
uv run pytest tests/integration/test_cli_tools.py -q
```

Expected in an `agy = none` environment:

```text
2 skipped
```

The exact pass count depends on platform-specific skips for `btop` and `opencode`.
The enabled `agy` tests should skip and the disabled `agy` tests should pass.

- [ ] **Step 4: Commit CLI test gating**

Run:

```bash
git add tests/integration/test_cli_tools.py
git commit -m "Gate agy path tests on chezmoi data"
```

## Task 4: Gate Antigravity version execution and keep config checks ungated

**Files:**
- Modify: `tests/integration/test_antigravity.py`
- Test: `tests/integration/test_antigravity.py`

- [ ] **Step 1: Verify the current disabled-state bug in an `agy = none` environment**

Run this in an environment where `chezmoi data --format=json` reports `"agy": {"installation_method": "none"}`:

```bash
uv run pytest tests/integration/test_antigravity.py::test_antigravity_version -q
```

Expected:

```text
FAILED tests/integration/test_antigravity.py::test_antigravity_version
```

- [ ] **Step 2: Replace `tests/integration/test_antigravity.py`**

Replace the full file with this content:

```python
import pytest


@pytest.mark.integration
@pytest.mark.chezmoi_installation("agy", methods={"dotfiles.script", "preinstalled"})
def test_antigravity_version(host):
    """Verify that the agy CLI is operational when enabled."""
    result = host.run("agy --version")
    assert result.rc == 0, f"'agy --version' failed.\nstderr: {result.stderr}\nstdout: {result.stdout}"


@pytest.mark.integration
def test_antigravity_settings_deployed(host, chezmoi_dest):
    """Verify ~/.gemini/antigravity-cli/settings.json exists after chezmoi apply."""
    settings_file = host.file(str(chezmoi_dest / ".gemini" / "antigravity-cli" / "settings.json"))
    assert settings_file.exists, "~/.gemini/antigravity-cli/settings.json does not exist"


@pytest.mark.integration
def test_legacy_gemini_settings_removed(host, chezmoi_dest):
    """Verify ~/.gemini/settings.json does not exist after chezmoi apply."""
    legacy_file = host.file(str(chezmoi_dest / ".gemini" / "settings.json"))
    assert not legacy_file.exists, "~/.gemini/settings.json still exists"
```

- [ ] **Step 3: Run focused Antigravity tests**

Run:

```bash
uv run pytest tests/integration/test_antigravity.py -q
```

Expected in an `agy = none` environment:

```text
1 skipped
```

The version test should skip.
The settings and legacy-removal tests should still run.

- [ ] **Step 4: Commit Antigravity test gating**

Run:

```bash
git add tests/integration/test_antigravity.py
git commit -m "Gate agy version test on chezmoi data"
```

## Task 5: Run final verification

**Files:**
- Verify: `tests/integration/conftest.py`
- Verify: `tests/integration/chezmoi_test_data.py`
- Verify: `tests/integration/test_chezmoi_data.py`
- Verify: `tests/integration/test_cli_tools.py`
- Verify: `tests/integration/test_antigravity.py`

- [ ] **Step 1: Run formatting**

Run:

```bash
uv run ruff format --check tests/integration/conftest.py tests/integration/chezmoi_test_data.py tests/integration/test_chezmoi_data.py tests/integration/test_cli_tools.py tests/integration/test_antigravity.py
```

Expected:

```text
5 files already formatted
```

- [ ] **Step 2: Run linting**

Run:

```bash
uv run ruff check tests/integration/conftest.py tests/integration/chezmoi_test_data.py tests/integration/test_chezmoi_data.py tests/integration/test_cli_tools.py tests/integration/test_antigravity.py
```

Expected:

```text
All checks passed!
```

- [ ] **Step 3: Run focused integration tests**

Run:

```bash
uv run pytest tests/integration/test_chezmoi_data.py tests/integration/test_cli_tools.py tests/integration/test_antigravity.py -q
```

Expected:

```text
no failures
```

Platform-specific skips are acceptable.
The `agy` enabled tests should skip when `agy.installation_method` is `none`.
The `agy` disabled tests should pass when `agy.installation_method` is `none`.

- [ ] **Step 4: Run the full integration suite when the local environment can support it**

Run:

```bash
uv run pytest tests/integration -q
```

Expected:

```text
no failures
```

Platform-specific skips are acceptable.
If the local environment lacks a fully applied chezmoi destination, record that limitation and rely on the focused tests that can run.

- [ ] **Step 5: Confirm final git status**

Run:

```bash
git status --short
```

Expected:

```text
clean working tree
```
