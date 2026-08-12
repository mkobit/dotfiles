# 2026-08-12: sandboxr sandbox backend — bwrap only

## Decision

`sandboxr` (`src/python/sandboxr`) uses `bwrap` as its only sandboxing backend for wrapping autonomous AI agent CLI runs (claude, agy, opencode).
Do not re-add `srt` (`@anthropic-ai/sandbox-runtime`).
Do not adopt `sbx` (Docker Sandboxes) for this use case yet.

## Context

sandboxr sandboxes autonomous, no-human-in-the-loop agent runs: the agent bypasses its own permission prompts, so the OS-level sandbox is the real security boundary.
`srt` was previously made the primary backend (2026-07-05) specifically for domain-allowlisted network egress, since bwrap only supports full-network-or-none.
PR #784 (2026-08-12) reverted that, stripping sandboxr back to bwrap-only, as part of a separately-scoped simplification.
This record captures why that reversal is the right call on its own merits, not just an artifact of the prompt that drove #784.

## Reasoning

- bwrap is the only option that cleanly forwards the SSH/GPG agent socket for commit signing on Linux.
`srt`'s seccomp-bpf filter architecturally cannot do path-based unix-socket filtering, so it can't selectively allow just the agent socket — confirmed against the installed srt 0.0.63's own shipped code.
`sbx` has no host-agent-socket forwarding at all; its model is sign-elsewhere, via a git remote.
- Domain-allowlisted egress has bounded value.
An autonomous run's own session credential can't be denylisted — it needs `api.anthropic.com` to function — so even a perfect allowlist stops exfiltration to arbitrary domains but not exfiltration through the one domain the agent is already authenticated to.
- Re-adding `srt` reopens a proven bug surface.
Nearly every historical srt bug in this project came from porting bwrap-shaped concepts (bind-mount allow-lists, agent-socket handling) into srt's differently-shaped config, including one where the wrapped command's arguments were silently dropped and it ran as a no-op while reporting success.
- `sbx` is not ready for this use case.
It requires a Docker cloud login (`sbx login`), is closed-source, and ships only `dev-`/`nightly` pre-releases.
Its microVM isolation and daemon-governed egress policy (`sbx policy allow network <hosts>`) are the strongest design of the three — revisit once it reaches GA with a local-auth mode.

## Revisit when

- `sbx` reaches GA, offers a no-cloud-login mode, and/or adds host-agent-socket forwarding.
- Scoped egress becomes a hard requirement for an autonomous run — build a filtering proxy inside bwrap's own network namespace first, before reconsidering a vendor runtime.

## Verification

Live-checked on the deciding host, not assumed: bwrap 0.9.0, claude 2.1.215, srt 0.0.63 installed (0.0.70 latest upstream), sbx v0.38.0 with a healthy daemon.
`sandboxr doctor` passes end to end under the bwrap-only backend.
