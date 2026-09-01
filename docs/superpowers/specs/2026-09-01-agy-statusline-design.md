# Agy statusline design

## Goal

Restore the personal-base agy statusline through `termstatus` without risking agy's fixed one-second statusline-command deadline.

Keep the existing public command, `statusline antigravity render`.

Show context remaining rather than context consumed.

Keep terminal titles disabled because this change concerns only the status line.

## Scope

This change modifies the personal base repository only.

It updates the chezmoi source for agy settings and the `termstatus` project.

It does not modify the Stripe overlay or any deployed `~/.gemini` file.

The current command entrypoint is [main.py](https://github.com/mkobit/dotfiles/blob/main/src/python/termstatus/termstatus/main.py) and the generated agy settings transform is [modify_settings.json](https://github.com/mkobit/dotfiles/blob/main/src/chezmoi/dot_gemini/antigravity-cli/modify_settings.json).

## Reference behavior

The [reference shell statusline](https://github.com/praialabs/sbx-kits/blob/main/agents/agy/files/home/.gemini/antigravity-cli/statusline.sh) consumes one JSON payload and emits one ANSI-coloured line.

It supplies agent state, model and effort, VCS state, context use, quota meters and reset timers, cost, and a width-responsive layout.

It falls back to Git when agy omits VCS information.

It has no timer loop, cache, coroutine, or configurable command timeout.

The host CLI owns refresh frequency and payload freshness.

## Chosen approach

Retain `termstatus` as the command namespace and ownership boundary.

Move agy dispatch ahead of every third-party import by pointing the console script at a minimal stdlib-only entrypoint.

The entrypoint imports only `sys` until it identifies an agy command.

`statusline antigravity render` then imports a stdlib-only agy renderer.

All existing non-agy subcommands continue into the Typer application through a lazy import.

This preserves one familiar command while ensuring agy does not load Typer, Rich, Whenever, or unrelated render modules.

Pure payload extraction and output rendering remain synchronous.

Use `asyncio.create_subprocess_exec` only for the optional Git fallback, with a strict 75 ms timeout.

Persist a short-TTL VCS cache keyed by the payload working directory to avoid launching Git on repeated repaints.

Cache branch, dirty state, and negative non-repository results for two seconds.

Use the payload VCS data whenever agy supplies it, without invoking Git.

This is preferred to a payload-only renderer, which would lose branch and dirty state with current agy payloads, and to a persistent helper daemon, which adds more lifecycle complexity than a personal statusline warrants.

## Payload and display

Normalize malformed or missing JSON to an empty payload and always produce a safe line or no output.

Use `context_window.remaining_percentage` when present.

Otherwise calculate remaining context as `100 - used_percentage`, clamped to `0..100`.

Display the following information when available.

| Concept | Agy data | Display |
| --- | --- | --- |
| Agent state | `agent_state` | Stable, padded coloured state label |
| Context | `context_window.remaining_percentage` or `used_percentage` | Remaining percentage, coloured green through red as capacity declines |
| Cost | `cost.estimated`, `cost.total`, or numeric `cost` | Optional compact currency value |
| Quotas | `quota[gemini-5h]`, `quota[gemini-weekly]`, `quota[3p-5h]`, `quota[3p-weekly]` | Remaining-capacity meters and one meaningful reset timer |
| Model | `model.display_name` | Model, with known noisy suffixes removed |
| Effort | `model.effort`, `model.reasoning_effort`, or `effort` | Optional model qualifier |
| Workspace | `cwd` | Directory basename |
| Version control | `vcs.branch`, `vcs.dirty`, or cached fallback | Branch with a dirty marker |
| Sandbox | `sandbox.enabled` and `sandbox.allow_network` | Compact permissions state |

At widths of 100 columns or more, show all quota families.

At widths from 80 through 99 columns, show Gemini quotas only.

Below 80 columns, omit quota meters.

At 110 columns or more, include the secondary quota-reset detail and effort.

Below 75 columns, collapse the right side to the most valuable identity information, prioritizing model and branch.

ANSI codes must not count toward padding or alignment.

Unicode meter glyphs must be measured by terminal-cell width rather than Python string length.

`AGY_STATUSLINE_DEBUG` remains an optional debug escape hatch that writes the received payload to its named file.

Debug writing never prevents normal output.

## Runtime budget

Agy has a fixed 1,000 ms statusline-process deadline and no discovered setting to extend it.

Target a cold p95 of 250–300 ms on Ubuntu.

The renderer must still emit a useful payload-only line if Git times out, exits unsuccessfully, or the cache cannot be read or written.

The 75 ms Git deadline and two-second cache leave substantial headroom for process start, JSON parsing, and terminal output.

Do not introduce polling, sleeping, background work, network access, or imports outside the standard library on the agy route.

## Settings

The chezmoi settings transform should add only this statusline configuration when agy is enabled.

```json
"statusLine": {
  "type": "command",
  "command": "statusline antigravity render",
  "enabled": true
}
```

It should continue removing `title`.

The unqualified command deliberately resolves the editable `uv tool` installation on `PATH` rather than baking in a machine-specific virtualenv path.

## Failure handling

Missing fields, malformed values, unsupported terminal widths, non-Git directories, Git failures, and cache failures must degrade by omitting only the affected segment.

The command should exit successfully after emitting a safe line where possible.

It must write diagnostic output only in explicit debug mode, never to the normal statusline stream.

## Tests and verification

Add unit tests for payload defaults, context-remaining conversion, quota and reset selection, state colours, width pruning, ANSI-aware alignment, and Git-cache fallback parsing.

Add subprocess tests that exercise the console command from a fresh Python interpreter, rather than only the already-imported Typer test runner.

Measure cold starts with a representative payload and verify they remain well below the one-second deadline.

Run the Python formatter, linter, and test suite after implementation.

Preview the generated agy settings through chezmoi before applying them.

Validate the deployed command on Ubuntu with both an ordinary Git repository and a non-Git directory.
