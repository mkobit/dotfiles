# Codex config data implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate Codex Vim mode from base chezmoi data while preserving mutable Codex config.

**Architecture:** Add environment-neutral Codex data in `.chezmoidata`.
Patch `~/.codex/config.toml` with a chezmoi modify template that sets only `tui.vim_mode_default`.
Keep tests at deployment-shape level.

**Tech Stack:** Chezmoi templates, TOML, pytest-testinfra.

---

### Task 1: Add Codex config deployment

**Files:**
- Create: `src/chezmoi/.chezmoidata/codex.toml`
- Create: `src/chezmoi/dot_codex/modify_config.toml`
- Modify: `tests/integration/test_codex.py`

- [ ] **Step 1: Write the failing deployment test**

Create `tests/integration/test_codex.py` with:

```python
import pytest


@pytest.mark.integration
def test_codex_config_toml_deployed(host, chezmoi_dest):
    """Verify ~/.codex/config.toml exists after chezmoi apply."""
    config_file = host.file(str(chezmoi_dest / ".codex" / "config.toml"))
    assert config_file.exists, "~/.codex/config.toml does not exist"


@pytest.mark.integration
def test_codex_config_toml_is_valid(host, chezmoi_dest):
    """Verify ~/.codex/config.toml parses as TOML."""
    config_path = chezmoi_dest / ".codex" / "config.toml"
    result = host.run(
        f"python3 -c \"import pathlib, tomllib; tomllib.loads(pathlib.Path({str(config_path)!r}).read_text())\""
    )
    assert result.rc == 0, f"~/.codex/config.toml is invalid TOML.\nstderr: {result.stderr}"
```

- [ ] **Step 2: Run the new test**

Run:

```bash
uv run pytest tests/integration/test_codex.py -q
```

Expected: PASS on machines that already have a live Codex config.
The integration test intentionally checks the destination path and TOML validity, not specific managed values.

- [ ] **Step 3: Add Codex data**

Create `src/chezmoi/.chezmoidata/codex.toml` with:

```toml
[codex.tui]
vim_mode_default = true
```

- [ ] **Step 4: Add the modify template**

Create `src/chezmoi/dot_codex/modify_config.toml` with:

```gotemplate
{{- /* chezmoi:modify-template */ -}}
{{- $config := dict -}}
{{- if .chezmoi.stdin -}}
{{-   $config = fromToml .chezmoi.stdin -}}
{{- end -}}
{{- $config | setValueAtPath "tui.vim_mode_default" .codex.tui.vim_mode_default | toToml -}}
```

- [ ] **Step 5: Verify the modify template with a throwaway destination**

Run:

```bash
mkdir -p /private/tmp/codex-config-dest
chezmoi --source src/chezmoi --destination /private/tmp/codex-config-dest --working-tree "$(pwd)" apply --dry-run --verbose /private/tmp/codex-config-dest/.codex/config.toml
```

Expected: The diff creates `.codex/config.toml` with `[tui]` and `vim_mode_default = true`.

- [ ] **Step 6: Run the new test**

Run:

```bash
uv run pytest tests/integration/test_codex.py -q
```

Expected: PASS.

- [ ] **Step 7: Run focused related tests**

Run:

```bash
uv run pytest tests/integration/test_codex.py tests/integration/test_antigravity.py -q
```

Expected: PASS.

- [ ] **Step 8: Inspect rendered target output**

Run:

```bash
chezmoi execute-template '{{ .codex.tui.vim_mode_default }}'
```

Expected: `true`.

- [ ] **Step 9: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-07-07-codex-config-data-design.md docs/superpowers/plans/2026-07-07-codex-config-data.md src/chezmoi/.chezmoidata/codex.toml src/chezmoi/dot_codex/modify_config.toml tests/integration/test_codex.py
git commit -m "feat: manage Codex vim mode from data"
```
