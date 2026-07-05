# Sandboxr two-layer sandbox design

Date: 2026-07-05.
Status: approved design, pre-implementation.

sandboxr becomes a policy compiler emitting a two-layer invocation: an outer minimal bwrap mask owned by this repo, wrapping an inner `codex sandbox` (from [openai/codex](https://github.com/openai/codex), Apache-2.0) that owns enforcement.

---

## Decision record

### Why a vendor runtime for enforcement

Hand-rolling namespace/seccomp/network enforcement is ongoing security work (kernel quirks, CVE tracking, syscall-bypass research) that vendor teams already do full-time.
The previous `bwrap.py` had no seccomp layer at all; codex ships bwrap + seccomp + Landlock with `.git`-metadata protection, maintained upstream.

### Why the outer mask still exists

Verified empirically: `codex sandbox` only blocks writes and network — it does **not** hide reads.
Under its default profile, `~/.gnupg` and `~/.claude.json` were fully readable.
Credential *absence* (tmpfs-over-home in a mount namespace) is strictly stronger than path-based read denial, which has published bypasses (`/proc/self/root` path rewriting against Anthropic's denylist).
No vendor tool provides absence, so a thin repo-owned layer keeps it.

### Alternatives rejected

- **firejail**: setuid-root binary with a recurring local-root CVE history (CVE-2022-31214, CVE-2021-26910, OverlayFS escape); profile library targets interactive desktop apps, no programmatic policy API; Linux-only anyway.
- **anthropic-experimental/sandbox-runtime (srt)**: npm-only distribution (no static binary, conflicts with this repo's Python/uv + chezmoi-externals conventions); path-based `denyRead` is the weaker primitive regardless.
- **Fully hand-rolled hardening**: keeping `bwrap.py` and backporting the seccomp deny-list was viable but keeps this repo in the enforcement business; explicitly declined.
- **macOS Seatbelt backend**: not a current requirement; stub deleted, backend protocol remains the seam if it returns.

### Nesting feasibility (verified 2026-07-04)

Outer bwrap (tmpfs home) → inner `codex sandbox` works on this WSL2 kernel.
Inside the nested sandbox: `~/.gnupg` is absent (not permission-denied), `writable_roots` scoping holds, network is denied unless enabled, `/etc` is read-only, and the ephemeral tmpfs home stays writable (matching current semantics — scratch evaporates on exit).
Inner codex requires a writable `/tmp` for its mount-registry lock; the outer layer provides `--tmpfs /tmp` and re-binds needed subpaths after it.

---

## Architecture

```
sandboxr CLI
  → SandboxSpec (unchanged single source of truth)
    → compile to (outer bwrap args, inner codex -c overrides)
      → bwrap [mask mounts] -- codex sandbox [-c policy] -- <command>
```

`SandboxSpec` compilation stays pure argument construction, unit-testable without running either binary.

## Responsibility split

| Concern | Owner |
|---|---|
| Hide `~/.ssh`, `~/.gnupg`, gh tokens, ai-policy token store | Outer mask (tmpfs home + `home_mask`) |
| Re-expose toolchain, agent state, WSL `resolv.conf`, isolated cache | Outer mask (`RO_HOME_PATHS` / `RW_HOME_PATHS` tables, unchanged) |
| ssh/gpg agent socket forwarding | Outer mask (bind after `/run/user` tmpfs, unchanged) |
| TIOCSTI mitigation (`--new-session` when no TTY) | Outer mask |
| Writable `/tmp` for inner codex, project bind | Outer mask |
| Project `writable_roots`, read-only rest-of-world | Inner codex (`sandbox_mode="workspace-write"`) |
| Network on/off | Inner codex (`sandbox_workspace_write.network_access`) |
| Seccomp deny-list, Landlock, `.git`-metadata protection | Inner codex |

The outer layer drops `--unshare-net` and all namespace/network policy; it becomes mounts-only.

## Provisioning

The codex binary is provisioned via chezmoi externals through the existing BOM/catalog pattern in `.chezmoidata/bin/`.
Pinned version with checksum; codex publishes `.sigstore` attestations per release artifact.
The binary is a ~286 MB static musl executable — the accepted cost of exiting the enforcement business.
Upgrades are deliberate events gated by `sandboxr doctor` (see verification).

## Policy layer (unchanged, now explicit)

- **Signing**: off inside the sandbox (`sandbox.gitconfig` unchanged); the human's signature at merge/push from the host is the attestation ("sign at the gate").
- **Push/PR**: no path out of the sandbox — no gh token, no signing key; export happens by the human pushing from the host against the bind-mounted worktree.
- **Hooks/plugins/skills**: per-tool-family read-only whitelist entries as data in `sandbox.toml` profiles; overlay-extensible, no code change per addition.

## Verification

`doctor.py`'s empirical probe pattern is the regression net for the main risk taken on (codex behavior churn between pinned versions).
Probes to keep and extend:

- credential absence through both layers (`~/.ssh`, `~/.gnupg`, gh config, token store — "No such file", not "Permission denied"),
- write denied outside `writable_roots`, allowed inside,
- network denied/allowed per profile,
- inner codex starts cleanly (no mount-registry lock panic),
- codex version canary (fail loudly on unpinned drift).

Unit tests cover the `(outer, inner)` compilation as pure functions, replacing `test_bwrap.py`'s coverage one-for-one.

## Known constraints

- Inner codex panics without writable `/tmp`; the outer layer must tmpfs `/tmp` before re-binding project paths that live under it.
- `CODEX_HOME` points at a sandboxr-owned state directory, never the user's real `~/.codex`.
- codex's config schema is mid-migration upstream (new `[permissions]` tables); pin to the stable `-c sandbox_mode` / `sandbox_workspace_write` surface and revisit on upgrade.
- `codex sandbox` prints a PATH-alias warning when `CODEX_HOME` is under a temp dir; place the state dir under `~/.local/share/sandboxr/`.

## Deletions

- `sandboxr/backend/seatbelt.py` stub.
- Network/namespace flags in the outer arg builder (`--unshare-net`, `--unshare-pid`, `--unshare-ipc`, `--unshare-uts`, `--unshare-cgroup-try` move to inner codex's responsibility).

## Deferred (tracked here, not in issues)

- Scoped agent SSH signing key for positive agent identity on commits, if unsigned-inside stops being a sufficient provenance marker.
- Request-to-push marker UX formalizing the human export gate.
- Extracting the smaller `codex-linux-sandbox` helper from the release bundle instead of the full CLI, if the 286 MB pin becomes a problem (bundle is `.tar.zst`; needs zstd available).
- Watch codex's `[permissions]` schema for native read-restriction support.
