## Purpose

`sandboxr` wraps AI agent CLIs (claude, agy, opencode) in an outer sandbox so no-human-in-the-loop runs can use each tool's `--dangerously-skip-permissions`-equivalent without risking credential exfiltration, signed-commit forgery, or destruction of the home directory.

## Mode split

- **HITL.**
Run the tool directly (`claude`, `agy`, `opencode`).
Each tool's own approval prompts are the UX boundary.
Nothing in this package applies.
- **Autonomous.**
`sandboxr run -- TOOL ARGS`.
Outer bwrap (Linux/WSL) is the security boundary; each adapter flips the tool's bypass flag so the inner approval prompts don't fire.
The tool's settings file inside the sandbox is *not* trusted — the OS-level isolation is.

## Files in the package

- `sandboxr/backend/protocol.py` — `SandboxBackend` `Protocol`.
- `sandboxr/backend/bwrap.py` — `BwrapBackend`, the only implementation (Linux/WSL only).
Bind table: `/` ro, `$HOME` tmpfs (default-deny), explicit re-binds for the toolchain, agent state dirs, and the project worktree.
- `sandboxr/sandbox/spec.py` — `SandboxSpec` dataclass, the argument surface between CLI flags and the bwrap builder.
- `sandboxr/sandbox/tool.py` — per-tool adapters (`adapt_command`) that flip each agent CLI's own permission-bypass flag.
- `sandboxr/cli/` — typer commands `run`, `shell`, `doctor`; `_common.py` holds shared spec-building and guard helpers.
- `sandboxr/main.py` — typer `app` wiring the three commands.

## Deliberate omissions

- **No profile/config file** — every knob is an explicit CLI flag (`--project-write`, `--network`, `--ssh-agent`, `--gpg-agent`, `--ro`, `--rw`).
A prior design read profiles from `.chezmoidata/ai/sandbox.toml` and supported a pluggable `srt` backend; both were removed as unneeded indirection over a single, always-on `bwrap` path.
- **No global PreToolUse guard hook** — earlier design ripped out because the agent's own config files are agent-writable; only the OS-level boundary is real.
- **No `--sandbox` flag passed to `agy`** — antigravity-cli#36: combining it with `--dangerously-skip-permissions` auto-approves bypassing it.
- **No `OPENCODE_HARDENED_MODE=1`** — it would engage opencode's own bwrap inside our bwrap and create nested namespaces.
- **No write credentials inside the sandbox** — `~/.ssh`, `~/.gnupg` private key material, `~/.config/gh`, and `/run/user/<uid>` are masked; only the SSH/GPG agent *sockets* are forwarded, for signing only.
A read-only `gh` PAT at `~/.local/state/ai-policy/tokens/readonly.token` (chmod 600 required) is injected as `GH_TOKEN` if present.
- **No macOS support** — bwrap is Linux-only; `run`/`shell`/`doctor` all require `bwrap` on PATH and fail closed otherwise.

## Verification

- `uv run pytest src/python/sandboxr` — unit coverage for CLI guards and bwrap argv.
- `sandboxr doctor` — probes inside the sandbox confirm credentials are hidden, root is read-only, project is writable, and commit signing is disabled.
- `sandboxr doctor --no-project-write` — same probes plus a project-read-only assertion.

## When extending

- Add per-tool adapters in `adapt_command` (`sandbox/tool.py`) keyed on `Path(command[0]).name`.
- Add new RW or RO home paths in `bwrap.py` (`RW_HOME_PATHS` / `RO_HOME_PATHS`) when a tool needs persistent state inside the sandbox.
Bind defensively — if the path doesn't exist on the host, the bwrap step is skipped, so adding speculative candidate paths is cheap.
- New sandbox knobs are CLI flags threaded through `_sandbox_spec` (`cli/_common.py`) into `SandboxSpec`, not config file keys.
