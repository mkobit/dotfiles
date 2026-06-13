## Purpose

`agent-run` wraps AI agent CLIs (claude, agy, opencode) in an outer sandbox so no-human-in-the-loop runs can use each tool's `--dangerously-skip-permissions`-equivalent without risking credential exfiltration, signed-commit forgery, or destruction of the home directory.

## Mode split

- **HITL.**
Run the tool directly (`claude`, `agy`, `opencode`).
Each tool's own approval prompts are the UX boundary.
Nothing in this package applies.
- **Autonomous.**
`agent-run run --profile autonomous -- TOOL ARGS`.
Outer bwrap (Linux/WSL) is the security boundary; each adapter flips the tool's bypass flag so the inner approval prompts don't fire.
The tool's settings file inside the sandbox is *not* trusted — the OS-level isolation is.

## Files in the package

- `agent_sandbox/config.py` — pydantic model for `~/.config/ai-policy/sandbox.toml` plus profile resolution.
Resolution order: `--profile` CLI flag > `$AGENT_RUN_PROFILE` > `default_profile` from config.
Never reads from the project tree (so a hostile repo cannot upgrade its own capabilities).
- `agent_sandbox/backend.py` — `SandboxBackend` `Protocol` plus `BwrapBackend` (implemented) and `SeatbeltBackend` (stub for future macOS support).
- `agent_sandbox/bwrap.py` — bwrap argv builder.
Bind table: `/` ro, `$HOME` tmpfs (default-deny), explicit re-binds for the toolchain, agent state dirs, and the project worktree.
- `agent_sandbox/main.py` — typer `app` exposing `run` and `doctor`.
Per-tool adapters (`claude`, `agy`, `opencode`) live in `_adapt_command`.

## Deliberate omissions

- **No global PreToolUse guard hook** — earlier design ripped out because the agent's own config files are agent-writable; only the OS-level boundary is real.
- **No `--sandbox` flag passed to `agy`** — antigravity-cli#36: combining it with `--dangerously-skip-permissions` auto-approves bypassing it.
- **No `OPENCODE_HARDENED_MODE=1`** — it would engage opencode's own bwrap inside our bwrap and create nested namespaces.
- **No per-repo configuration** — profile resolution does not look at git remote, marker files, or `.agent-run` files in the project.
- **No write credentials inside the sandbox** — `~/.ssh`, `~/.gnupg`, `~/.config/gh`, and `/run/user/<uid>` are masked.
A read-only `gh` PAT at `~/.local/state/ai-policy/tokens/readonly.token` (chmod 600 required) is injected as `GH_TOKEN` if present.
- **No macOS implementation yet** — `SeatbeltBackend.build_args` raises `NotImplementedError`; sketch is in `.claude/plans/` of how a Seatbelt profile would look.

## Verification

- `uv run pytest src/python/agent_sandbox` — unit coverage for config, backend dispatch, and bwrap argv.
- `agent-run doctor --profile autonomous` — probes inside the sandbox confirm credentials are hidden, root is read-only, project is writable, and commit signing is disabled.
- `agent-run doctor --profile readonly` — same probes plus project read-only assertion.

## When extending

- Add per-tool adapters in `_adapt_command` keyed on `Path(command[0]).name`.
- Add new RW or RO home paths in `bwrap.py` (`RW_HOME_PATHS` / `RO_HOME_PATHS`) when a tool needs persistent state inside the sandbox.
Bind defensively — if the path doesn't exist on the host, the bwrap step is skipped, so adding speculative candidate paths is cheap.
- Add new profile fields by editing `config.py` (pydantic model) and the corresponding chezmoi data in `src/chezmoi/.chezmoidata/ai/sandbox.toml`.
The model uses `extra="forbid"` on `Profile`, so unknown keys fail closed.
- New backends implement the `SandboxBackend` Protocol and register in `select_backend`.
