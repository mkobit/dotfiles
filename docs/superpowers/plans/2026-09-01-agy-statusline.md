# Agy statusline implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore a responsive agy statusline while keeping the command safely below agy's fixed one-second deadline.

**Architecture:** Route the installed `statusline` command through a standard-library dispatcher that recognizes agy before importing the existing Typer application. Keep agy payload decoding, formatting, debug capture, and bounded cached Git fallback in a separate standard-library module.

**Tech Stack:** Python 3.14 standard library, `asyncio` subprocesses, `pytest`, `uv`, and chezmoi JSON modify templates.

See the approved [design](../specs/2026-09-01-agy-statusline-design.md) and the [reference statusline](https://github.com/praialabs/sbx-kits/blob/main/agents/agy/files/home/.gemini/antigravity-cli/statusline.sh).

## Global constraints

- Keep the public command exactly `statusline antigravity render`.
- Do not import Typer, Rich, Whenever, or any other third-party package on the agy route.
- Render synchronously unless payload VCS data is absent and its two-second cache is unavailable.
- Bound the one optional Git subprocess to 75 ms.
- Render context remaining from `remaining_percentage`, or `100 - used_percentage` when it is absent.
- Do not poll, sleep, perform network I/O, or log to normal statusline output.
- Manage `statusLine` only when agy is enabled and continue removing `title`.
- Keep base work on `docs/agy-statusline-design` or a successor branch, and leave PR creation and merging to the user.

## File structure

- Create `src/python/termstatus/termstatus/entrypoint.py` for dependency-gated console dispatch.
- Create `src/python/termstatus/termstatus/agy.py` for the standard-library renderer and VCS cache.
- Create `src/python/termstatus/tests/test_agy.py` for agy-specific unit and process tests.
- Modify `src/python/termstatus/pyproject.toml` to point `statusline` at the new entrypoint.
- Modify `src/python/termstatus/termstatus/main.py` and `src/python/termstatus/tests/test_main.py` to remove the unreachable-in-time agy fast path and its in-process timing tests.
- Modify `src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json` and `tests/integration/test_antigravity.py` to manage and verify the setting.

### Task 1: Isolate the agy entrypoint

**Files:**

- Create: `src/python/termstatus/termstatus/entrypoint.py`.
- Modify: `src/python/termstatus/pyproject.toml:12`.
- Modify: `src/python/termstatus/termstatus/main.py:35-158`.
- Modify: `src/python/termstatus/tests/test_main.py:204-233`.
- Test: `src/python/termstatus/tests/test_agy.py`.

**Interfaces:**

- Consumes: `sys.argv` and `termstatus.agy.render_from_stdin`.
- Produces: `termstatus.entrypoint.main() -> None` as the installed console target.

- [ ] **Step 1: Write failing cold-process route tests.**

```python
def test_entrypoint_does_not_import_typer_for_agy_render() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import sys; import termstatus.entrypoint; print('typer' in sys.modules)"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == "False\n"


def test_console_script_renders_from_a_fresh_process() -> None:
    command = [str(Path(sys.executable).with_name("statusline")), "antigravity", "render"]
    result = subprocess.run(command, input='{"agent_state":"working"}', capture_output=True, check=False, text=True)
    assert result.returncode == 0
    assert "working" in result.stdout
```

- [ ] **Step 2: Run the tests to verify the new route is absent.**

Run: `uv run pytest src/python/termstatus/tests/test_agy.py -q`.

Expected: FAIL because `termstatus.entrypoint` does not exist.

- [ ] **Step 3: Add a standard-library dispatcher and change the console target.**

```python
# src/python/termstatus/termstatus/entrypoint.py
import sys


def main() -> None:
    command = sys.argv[1:3]
    if command == ["antigravity", "render"]:
        from termstatus.agy import render_from_stdin

        render_from_stdin()
        return
    if command == ["antigravity", "title"]:
        from termstatus.agy import title_from_stdin

        title_from_stdin()
        return
    from termstatus.main import main as typer_main

    typer_main()
```

```toml
# src/python/termstatus/pyproject.toml
[project.scripts]
statusline = "termstatus.entrypoint:main"
```

Remove `antigravity_app`, `fast_antigravity_render`, `fast_antigravity_title`, and their Typer decorators from `termstatus.main`.

Leave all non-agy commands on `termstatus.main.cli()`.

- [ ] **Step 4: Replace in-process timing tests with a real deadline guard.**

Delete `test_antigravity_fast_path_timing` and `test_antigravity_fast_path_multi_run_benchmark` from `tests/test_main.py`.

Add this assertion to the fresh-process test.

```python
durations = []
for _ in range(5):
    started = time.perf_counter()
    result = subprocess.run(command, input=payload, capture_output=True, check=False, text=True, timeout=1)
    durations.append(time.perf_counter() - started)
    assert result.returncode == 0
assert max(durations) < 0.75
```

- [ ] **Step 5: Run focused tests and commit the isolated route.**

Run: `uv run pytest src/python/termstatus/tests/test_agy.py src/python/termstatus/tests/test_main.py -q`.

Expected: PASS.

```bash
git add src/python/termstatus/pyproject.toml src/python/termstatus/termstatus/entrypoint.py src/python/termstatus/termstatus/main.py src/python/termstatus/tests/test_agy.py src/python/termstatus/tests/test_main.py
git commit -m "refactor(termstatus): isolate agy entrypoint"
```

### Task 2: Render the complete payload using only the standard library

**Files:**

- Create: `src/python/termstatus/termstatus/agy.py`.
- Modify: `src/python/termstatus/tests/test_agy.py`.

**Interfaces:**

- Consumes: one JSON object from standard input and an optional `VcsState`.
- Produces: `decode_payload`, `render_statusline`, `render_from_stdin`, and `title_from_stdin`.
- Produces: `AgyPayload` and `VcsState` dataclasses for Task 3.

- [ ] **Step 1: Write failing pure-renderer tests.**

```python
FULL_PAYLOAD = {
    "agent_state": "working",
    "cwd": "/work/repo",
    "model": {"display_name": "Gemini 3 (high)", "effort": "high"},
    "context_window": {"used_percentage": 18},
    "cost": {"estimated": 0.01},
    "terminal_width": 120,
    "quota": {
        "gemini-5h": {"remaining_fraction": 0.50, "reset_in_seconds": 1800},
        "gemini-weekly": {"remaining_fraction": 0.10, "reset_in_seconds": 7200},
        "3p-5h": {"remaining_fraction": 0.75, "reset_in_seconds": 1800},
        "3p-weekly": {"remaining_fraction": 0.50, "reset_in_seconds": 7200},
    },
    "sandbox": {"enabled": True, "allow_network": False},
}


def test_decode_payload_prefers_remaining_context() -> None:
    assert decode_payload({"context_window": {"remaining_percentage": 62, "used_percentage": 99}}).remaining_context == 62


def test_decode_payload_derives_remaining_context() -> None:
    assert decode_payload({"context_window": {"used_percentage": 17.6}}).remaining_context == 82


def test_wide_render_shows_the_canonical_statusline_information() -> None:
    line = strip_ansi(render_statusline(decode_payload(FULL_PAYLOAD), VcsState("main", True, True)))
    assert "82% ctx" in line and "$0.01" in line
    assert "g:" in line and "3p:" in line
    assert "repo" in line and "main*" in line
    assert "Gemini" in line and "high" in line and "sandbox" in line
```

- [ ] **Step 2: Run the renderer tests and verify they fail.**

Run: `uv run pytest src/python/termstatus/tests/test_agy.py -q`.

Expected: FAIL because the agy decoder and renderer do not exist.

- [ ] **Step 3: Implement decoder, formatting helpers, and responsive assembly.**

```python
@dataclass(frozen=True)
class VcsState:
    branch: str | None
    dirty: bool
    is_repo: bool


@dataclass(frozen=True)
class Quota:
    remaining: int
    reset_in_seconds: int


@dataclass(frozen=True)
class SandboxState:
    enabled: bool
    allow_network: bool


@dataclass(frozen=True)
class AgyPayload:
    state: str
    remaining_context: int
    cwd: str | None
    model: str | None
    effort: str | None
    cost: float | None
    terminal_width: int
    quotas: dict[str, Quota]
    vcs: VcsState | None
    sandbox: SandboxState | None


def decode_payload(raw: Mapping[str, object]) -> AgyPayload:
    context = mapping(raw.get("context_window"))
    remaining = percent(context.get("remaining_percentage"))
    if remaining is None:
        remaining = 100 - (percent(context.get("used_percentage")) or 0)
    return AgyPayload(
        state=normalized_text(raw.get("agent_state")) or "idle",
        remaining_context=max(0, min(100, remaining)),
        cwd=normalized_text(raw.get("cwd")),
        model=normalized_text(mapping(raw.get("model")).get("display_name")),
        effort=first_text(mapping(raw.get("model")).get("effort"), mapping(raw.get("model")).get("reasoning_effort"), raw.get("effort")),
        cost=cost_value(raw.get("cost")),
        terminal_width=max(1, integer(raw.get("terminal_width")) or 80),
        quotas=decode_quotas(mapping(raw.get("quota"))),
        vcs=decode_vcs(mapping(raw.get("vcs"))),
        sandbox=decode_sandbox(mapping(raw.get("sandbox"))),
    )
```

Implement pure helpers for context, cost, quota meter, duration, limiting timer, state, sandbox, workspace, VCS, model, and effort.

Use `○`, `◔`, `◑`, `◕`, and `●` at 15, 40, 65, and 85 percent remaining thresholds.

Use red below 20 remaining context, yellow from 20 through 40, and green above 40.

Format nonpositive costs as dim `$0.00`, costs below `$0.001` as dim `<$0.001`, costs below `$0.0095` to three decimal places, and other costs to two decimal places.

Suppress a reset timer when both quota buckets are at least 85 percent remaining.

When weekly quota is at most 20 percent remaining, select its timer first.

Otherwise select the lower remaining bucket, with a five-hour tie-breaker.

Show the Gemini timer at width 90 or above, or when cost is absent, and show the 3p timer at width 110 or above.

Show both quota families at width 100 or above, Gemini only from 80 through 99, and none below 80.

Show sandbox and effort at width 110 or above.

At width below 75, show model on the right if present, otherwise VCS branch.

Strip a trailing parenthesized effort suffix from the model display name.

```python
def display_width(value: str) -> int:
    plain = ANSI_SGR.sub("", value)
    return sum(0 if unicodedata.combining(char) else 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1 for char in plain)


def render_statusline(payload: AgyPayload, vcs: VcsState | None) -> str:
    left = left_segments(payload)
    right = right_segments(payload, vcs)
    padding = payload.terminal_width - display_width(left) - display_width(right)
    return f"{left}{' ' * padding}{right}" if padding > 1 else join_segments([left, right])
```

- [ ] **Step 4: Add edge-case and fidelity tests.**

```python
@pytest.mark.parametrize(("remaining", "glyph"), [(0, "○"), (25, "◔"), (50, "◑"), (75, "◕"), (100, "●")])
def test_format_meter_uses_reference_thresholds(remaining: int, glyph: str) -> None:
    assert glyph in format_meter(remaining)


def test_limiting_timer_prioritizes_a_critical_weekly_quota() -> None:
    assert limiting_timer(Quota(50, 1800), Quota(10, 7_200)) == "wk:2h"


def test_display_width_ignores_ansi_sequences() -> None:
    assert display_width("\033[32m●\033[0m") == 1
```

Add malformed-JSON, missing-field, narrow-width, debug-capture, state-colour, and `title_from_stdin` cases.

When `AGY_STATUSLINE_DEBUG` is `1` or `true`, write the unparsed payload to `/tmp/agy-statusline-debug.json`.

Otherwise use the environment value as the debug destination.

Ignore a debug-write failure after preserving normal rendering.

- [ ] **Step 5: Run renderer tests and commit the renderer.**

Run: `uv run pytest src/python/termstatus/tests/test_agy.py -q`.

Expected: PASS except for VCS cache tests introduced in Task 3.

```bash
git add src/python/termstatus/termstatus/agy.py src/python/termstatus/tests/test_agy.py
git commit -m "feat(termstatus): render agy statusline"
```

### Task 3: Add one cached, timeout-bounded Git fallback

**Files:**

- Modify: `src/python/termstatus/termstatus/agy.py`.
- Modify: `src/python/termstatus/tests/test_agy.py`.

**Interfaces:**

- Consumes: a payload without `vcs.branch` and optional `XDG_CACHE_HOME`.
- Produces: `async def resolve_vcs(payload: AgyPayload) -> VcsState | None`.
- Produces: a SHA-256-keyed cache record in `$XDG_CACHE_HOME/termstatus/agy-vcs/`.

- [ ] **Step 1: Write failing cache and timeout tests.**

```python
@pytest.mark.asyncio
async def test_resolve_vcs_uses_fresh_cache_without_launching_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    write_vcs_cache("/work/repo", VcsState("main", True, True), now=time.time())
    with patch("termstatus.agy.asyncio.create_subprocess_exec") as create_process:
        assert await resolve_vcs(decode_payload({"cwd": "/work/repo"})) == VcsState("main", True, True)
        create_process.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_vcs_kills_git_after_75_ms() -> None:
    process = AsyncMock()
    process.communicate.side_effect = TimeoutError
    with patch("termstatus.agy.asyncio.create_subprocess_exec", return_value=process):
        assert await resolve_vcs(decode_payload({"cwd": "/work/repo"})) is None
    process.kill.assert_called_once()
```

- [ ] **Step 2: Run the tests and verify the fallback is absent.**

Run: `uv run pytest src/python/termstatus/tests/test_agy.py -q`.

Expected: FAIL because VCS cache resolution does not exist.

- [ ] **Step 3: Implement the cache and one-command probe.**

```python
VCS_CACHE_TTL_SECONDS = 2.0
GIT_TIMEOUT_SECONDS = 0.075


async def probe_git(cwd: str) -> VcsState | None:
    process = await asyncio.create_subprocess_exec(
        "git", "-C", cwd, "status", "--porcelain=v1", "--branch", "-uno",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=GIT_TIMEOUT_SECONDS)
    except TimeoutError:
        process.kill()
        await process.communicate()
        return None
    if process.returncode != 0:
        return VcsState(branch=None, dirty=False, is_repo=False)
    return parse_git_status(stdout.decode(errors="replace"))
```

Use an epoch `expires_at` value, which stays meaningful across the short-lived agy processes.

Atomically replace the JSON cache file after a complete result, including a non-repository result.

Never cache a timeout or malformed cache record.

Call `asyncio.run(resolve_vcs(payload))` only when payload VCS lacks a branch.

- [ ] **Step 4: Cover parsing and failure degradation.**

```python
def test_parse_git_status_marks_dirty_when_porcelain_has_changes() -> None:
    assert parse_git_status(b"## feature/demo...origin/feature/demo\n M file.py\n") == VcsState("feature/demo", True, True)


@pytest.mark.asyncio
async def test_payload_branch_bypasses_cache_and_git() -> None:
    payload = decode_payload({"cwd": "/work/repo", "vcs": {"branch": "payload", "dirty": False}})
    with patch("termstatus.agy.probe_git") as probe:
        assert await resolve_vcs(payload) == VcsState("payload", False, True)
        probe.assert_not_called()
```

Add cases for expired cache, malformed cache JSON, nonzero Git exit, and cached non-repository state.

- [ ] **Step 5: Run all termstatus tests and commit the fallback.**

Run: `uv run pytest src/python/termstatus/tests -q`.

Expected: PASS.

```bash
git add src/python/termstatus/termstatus/agy.py src/python/termstatus/tests/test_agy.py
git commit -m "feat(termstatus): cache bounded agy Git fallback"
```

### Task 4: Enable and test the generated agy setting

**Files:**

- Modify: `src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json:63-64`.
- Modify: `tests/integration/test_antigravity.py`.

**Interfaces:**

- Consumes: existing agy settings JSON and `agy.installation_method`.
- Produces: a `statusLine` object for enabled agy installations.

- [ ] **Step 1: Write the failing managed-settings test.**

```python
def test_antigravity_statusline_is_configured(host, chezmoi_dest) -> None:
    path = chezmoi_dest / ".gemini" / "antigravity-cli" / "settings.json"
    result = host.run(
        f"python3 -c \"import json, pathlib; print(json.loads(pathlib.Path({str(path)!r}).read_text())['statusLine']['command'])\""
    )
    assert result.rc == 0, result.stderr
    assert result.stdout.strip() == "statusline antigravity render"
```

- [ ] **Step 2: Run the targeted test and verify it fails.**

Run: `uv run pytest tests/integration/test_antigravity.py -k statusline -q`.

Expected: FAIL because the template removes `statusLine`.

- [ ] **Step 3: Set the statusline and continue removing the title.**

```gotemplate
{{- $config = mergeOverwrite $config $settings -}}
{{- $config = set $config "statusLine" (dict "type" "command" "command" "statusline antigravity render" "enabled" true) -}}
{{- $config = omit $config "title" -}}
```

Keep this inside the existing enabled-agy guard.

- [ ] **Step 4: Preview the template and run the settings test.**

Run: `chezmoi --source src/chezmoi execute-template -f --with-stdin src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json`.

Expected: Valid JSON with `statusLine` and without `title`.

Run: `uv run pytest tests/integration/test_antigravity.py -q`.

Expected: PASS.

- [ ] **Step 5: Run final checks and commit the configured statusline.**

Run: `uv run ruff check src/python/termstatus tests/integration/test_antigravity.py`.

Expected: PASS.

Run: `uv run pytest src/python/termstatus/tests tests/integration/test_antigravity.py -q`.

Expected: PASS.

```bash
git add src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json tests/integration/test_antigravity.py
git commit -m "feat(chezmoi): enable agy statusline"
```

### Task 5: Validate on Ubuntu before handoff

**Files:**

- No source changes unless validation exposes a defect.

**Interfaces:**

- Consumes: an Ubuntu installation of the feature branch and representative agy payloads.
- Produces: evidence that command output and settings meet agy's deadline.

- [ ] **Step 1: Apply the managed agy settings.**

Run: `chezmoi apply ~/.gemini/antigravity-cli/settings.json`.

Expected: The configuration contains `statusline antigravity render`.

- [ ] **Step 2: Exercise payload rendering and Git fallback.**

Run: `printf '%s' '{"agent_state":"working","terminal_width":120,"model":{"display_name":"Gemini 3 (high)"},"context_window":{"used_percentage":18}}' | statusline antigravity render`.

Expected: A coloured line with `82% ctx`, `working`, and `Gemini 3`.

Run the same command with a `cwd` in a Git repository and then with `cwd` set to `/tmp`.

Expected: The first line includes branch state and the second safely omits it.


- [ ] **Step 3: Measure five cold starts.**

Run: `for run in 1 2 3 4 5; do /usr/bin/time -f '%e' sh -c "printf '%s' '{\\\"terminal_width\\\":120}' | statusline antigravity render >/dev/null"; done`.

Expected: Every observed run is below one second and p95 is at or below 300 ms.

- [ ] **Step 4: Record evidence and leave PR workflow to the user.**

Record the test output, settings preview, Git and non-Git results, and the timing result in the handoff.

Do not create or merge a pull request.
