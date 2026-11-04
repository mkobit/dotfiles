# Local model routing verification

Task 6 adds host OpenCode and Pi configuration and an ordinary Chezmoi hook for native SBX model settings.
All use the declared host URL; direct guest clients retain a separate declared route and repository-owned configuration.
Pi files use private target attributes and mode `0600`.
Disabled or missing choices preserve existing state.
Provider, model, plugin, and feature metadata survive the managed updates.

The failing baseline reported 45 failed, 2 passed, and 2 skipped tests before source edits.
Final routing and OpenCode tests passed: 57 passed and 2 existing overlay-only skips.
The overlay source is not mounted in the guest.
Eight adjacent schema tests also passed.
Ruff, format, rendered Bash syntax, and root ShellCheck `0.11.0` passed.

Tests cover private modes, disabled state, repeated apply, preserved foreign fields, native complete records, all reads before writes, drift repair, failed reads, and failed-write retry.
Independent review found no correction needed.
Its invalid-JSON probes stopped apply and preserved each host target's bytes.
All seven reported source hashes and modes match manifest SHA256 `2fce819f38bba677c80b402b55d3dae716cd674550408c623bf5ce34a361352f`.
The seventh entry is the unchanged existing OpenCode test.
The guest and its child checks stopped before return.

Tools: mise `2026.10.23`, uv `0.12.10`, Python `3.14.7`, Chezmoi `2.74.0`, Ruff `0.17.0`, and ty `0.0.87`.
Local context: `.sbx/task-context/model-routing/`.
Detailed local report: `/tmp/sbx-rearch-model-routing-report.md`.

Live apply, endpoint requests, model execution, and CI for this source remain integration gates.
An available Ollama service, selected model, reachability, and adequate tool/context support remain prerequisites.
A nondefault `PI_CODING_AGENT_DIR` needs explicit configuration.
No live setting, credential, tool install, or existing sandbox model was changed during this unit.
Use [the route contract](model-routing.md) for primary sources and format details.
