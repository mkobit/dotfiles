# Status: on hold

`sandboxr` is currently placed on hold while investing in Docker Sandboxes (`sbx`) as the container and microVM isolation layer.
The CLI entrypoint fails closed with an error on any command invocation (`run`, `shell`, `doctor`) to prevent accidental execution.
See [src/sbx/AGENTS.md](../../sbx/AGENTS.md) for the active Docker Sandboxes implementation and architecture.

## Purpose

`sandboxr` wraps AI agent CLIs (claude, agy, opencode) in an outer sandbox so no-human-in-the-loop runs can use each tool's `--dangerously-skip-permissions`-equivalent without risking credential exfiltration, signed-commit forgery, or destruction of the home directory.

## Mode split

- **HITL.**
Run the tool directly (`claude`, `agy`, `opencode`).
Each tool's own approval prompts are the UX boundary.
Nothing in this package applies.
- **Autonomous.**
`sandboxr run -- TOOL ARGS --dangerously-skip-permissions`.
Outer bwrap (Linux/WSL) is the security boundary; callers supply the tool's bypass flag so inner approval prompts don't fire.
The tool's settings file inside the sandbox is *not* trusted — the OS-level isolation is.
- **Sandboxed with interactive prompts.**
`sandboxr run -- TOOL ARGS`.
Both boundaries active: OS sandbox underneath, tool's own prompts (driven by the existing `.chezmoidata/ai/command_policy/*.toml` allow/ask/deny catalog) still fire on top — e.g. local git ops flow through, `git push`/`gh pr create`/`gh pr merge` still ask.
Uses interactive tool invocation (not `claude -p` print mode) — a prompt has nowhere to render otherwise (tty is enabled by default; use `--no-tty` to disable).

## Profiles

`sandboxr run --profile NAME` selects a named bundle of the granular flags below, defined in `_PROFILES` in `cli/run.py`.
This is *not* the deleted `sandbox.toml` config file: no external file, no env var, no resolution order — just an in-code `dict[str, _Profile]`, a frozen dataclass with one field per overridable setting.
Add an entry to `_PROFILES` to add a profile; nothing else needs to change.
`--profile` takes a single name — a profile only overrides the fields it explicitly sets, so it still composes with the granular flags for anything it doesn't touch (`--profile push --network shared` gets push *and* web access without a second profile).
The resolved invocation is logged to `$XDG_STATE_HOME/sandboxr/invocations.log` (rolling log files) and can be printed directly using `--show-command`.
Built-in profiles:
- `local-commit` forces `--no-ssh-agent --no-gpg-agent`: no push/sign capability, full stop.
- `push` forces `--ssh-agent`.
- `web-access` forces `--network shared`.
- `pr` implies `push` and additionally read-only-binds the real `~/.config/gh`.
This is *not* a scoped credential — there's no short-lived or per-usage token issuance, so the agent gets whatever access your actual `gh auth login` session has, not just this repo.
Read-only only stops the sandbox from tampering with the credential file; it does not limit what the token itself can do once `gh` reads it.
Chose this over a second hand-scoped PAT file because a hand-scoped token is still just another standing secret to create and remember to rotate, for a security property achievable another way if it ever matters (see the deferred broker idea, not built).

## Isolated concurrent sessions

Already works today, no sandboxr-specific support needed: create a git worktree (`git worktree add ../feature-x`, or the `using-git-worktrees` skill), `cd` into it, then `sandboxr run`/`shell` from there.
`_git_common_dir()` (`cli/_common.py`) detects you're in a linked worktree and binds both the worktree's own directory (isolated, per-session) and the main checkout's `.git` (shared object store, so commits/refs are visible across sessions) — verified live, not assumed.
Home-tools binds (`RO_HOME_PATHS`/`RW_HOME_PATHS`) are independent of cwd, so they're identical across every concurrent session regardless.

## Files in the package

- `sandboxr/backend/protocol.py` — `SandboxBackend` `Protocol`.
- `sandboxr/backend/bwrap.py` — `BwrapBackend`, the only implementation (Linux/WSL only).
Bind table: `/` ro, `$HOME` tmpfs (default-deny), explicit re-binds for the toolchain, agent state dirs, and the project worktree.
- `sandboxr/sandbox/spec.py` — `SandboxSpec` dataclass, the argument surface between CLI flags and the bwrap builder.
- `sandboxr/sandbox/tool.py` — per-tool adapters (`adapt_command`) that inject ai-policy settings files.
- `sandboxr/cli/` — typer commands `run`, `shell`, `doctor`; `_common.py` holds shared spec-building and guard helpers.
- `sandboxr/main.py` — typer `app` wiring the three commands.

## Deliberate omissions

- **No external profile/config file** — every knob is an explicit CLI flag (`--project-write`, `--network`, `--ssh-agent`, `--gpg-agent`, `--ro`, `--rw`), or a named bundle of them via `--profile` (see Profiles — an in-code registry, not a file).
A prior design read profiles from `.chezmoidata/ai/sandbox.toml` and supported a pluggable `srt` backend; both were removed as unneeded indirection over a single, always-on `bwrap` path.
- **No domain-allowlisted egress** — `--network` is binary (`none` or full host network); bwrap has no proxy/filtering primitive of its own.
`srt` (`@anthropic-ai/sandbox-runtime`) was tried for exactly this gap and reverted: its seccomp filter architecturally cannot forward SSH/GPG agent sockets on Linux (path-based unix-socket filtering isn't possible under seccomp-bpf), and porting bwrap's bind-table concepts into its config surface produced most of the integration bugs this project has hit.
The gain is bounded anyway — the agent's own session credential can't be denylisted, so an allowlist stops arbitrary-domain exfil but not exfil through the one API domain a run necessarily needs.
`sbx` (Docker Sandboxes) has stronger egress policy but requires a Docker cloud login and is closed-source — revisit only once it reaches GA with a local-auth mode.
If scoped egress becomes a hard requirement before then, prefer a filtering proxy inside bwrap's own network namespace over re-adopting a vendor sandbox runtime.
Full reasoning: `docs/decisions/2026-08-12-sandboxr-sandbox-backend.md`.
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
- New profiles are entries in `_PROFILES` (`cli/run.py`) — add a field to `_Profile` first if the knob doesn't exist yet.
