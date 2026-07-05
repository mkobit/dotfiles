# Handoff: sandboxr runtime decision (srt-primary, codex fallback)

Date: 2026-07-05.
Status: analysis complete, direction chosen, zero implementation done.
Audience: fresh agent session executing follow-ups.

## Governing criteria (user-stated, binding)

1. **Explicit opens, fails closed in the most general sense.**
   Every capability (read, write, egress) is deny-by-default; each exposure is a named, deliberate open.
2. **No hand-rolled enforcement.**
   sandboxr is a policy compiler; enforcement belongs to a maintained vendor tool.
3. **This chezmoi repo is higher privilege.**
   It is the control plane that generates sandbox policy; agents working on *other* projects must never see it writable, and policy inputs (`~/.config/ai-policy`, srt settings) must not be writable from inside any sandbox.
4. Whole-agent-loop sandboxing: sandboxr wraps a shell execution inside which an entire agentic loop (claude/gemini/etc.) runs.
   The loop needs egress to its LLM API, so binary network on/off is insufficient — this is why domain allowlisting decides the runtime choice.
5. macOS is not a requirement; delete the seatbelt stub.

## Decision

**Primary: adopt `@anthropic-ai/sandbox-runtime` (srt) as the enforcement runtime.**
sandboxr compiles `SandboxSpec`/`sandbox.toml` profiles into srt settings JSON and the srt invocation.

**Fallback (already spec'd and committed): two-layer bwrap-mask + `codex sandbox`** — see `docs/DESIGN-sandboxr-two-layer.md`.
Use it if srt's maturity/proxy issues (below) prove disqualifying.

### Why the recommendation flipped from the codex two-layer spec

The earlier srt dismissal rested on two beliefs, both now falsified empirically (2026-07-05, srt via npm, Linux/WSL2, node 22.14):

- Believed: srt `denyRead` is path-based denial (weaker than mount absence, bypass history).
  **Measured: `denyRead: ["~"]` yields ENOENT ("No such file or directory") — mount-level absence via bwrap, the same primitive as the hand-rolled mask.**
  Deny-then-allow works: `allowRead: ["~/.claude"]` re-exposed that subtree while the rest of home stayed absent.
- Believed: "meh" (user's initial take, since retracted).

And the fails-closed criterion exposed the codex path's structural gap: codex network is all-or-nothing; an agent loop needs it on, and "on" is unrestricted egress with no allowlist mechanism.
srt is the only process-level option with fail-closed egress (domain allowlist via proxy).

## Verified facts (do not re-derive)

### srt (tested via local npm install in scratchpad)

- Defaults with no settings: writes fail closed (even cwd read-only); egress fails closed (proxy 403); reads fail open (home readable) — so **`denyRead: ["~"]` + explicit `allowRead` list is mandatory in our profiles**.
- Settings schema (confirmed in dist): `filesystem.{denyRead,allowRead,allowWrite,denyWrite}`, `network.{allowedDomains,deniedDomains}`, `proxyPort`.
- Linux architecture (from `-d` debug output): bwrap + vendored native `apply-seccomp` binary (blocks Unix sockets) + host-side mux proxy (HTTP+SOCKS) on localhost, bridged into the network namespace via `socat UNIX-LISTEN:/tmp/claude-http-*.sock → TCP:localhost:<muxport>`; `HTTP_PROXY`-style env points processes at localhost:3128 inside.
- srt also `/dev/null`-masks config-injection vectors inside writable roots (`.gitconfig`, `.bashrc`, `.zshrc`, `.mcp.json`, `.ripgreprc`, …) — protection the codex path only has for `.git`/`.codex`.
- **Open bug**: with `denyRead: ["~"]`, curl inside got "Failed to connect to localhost port 3128" for both allowed and denied domains.
  socat IS installed on this machine, so that's not it.
  Suspect: home-deny masks srt state the bridge needs, or the bridge socket path is masked.
  This is follow-up #1; the domain allowlist worked in the default (no-settings) run, so the mechanism itself functions.

### codex sandbox (tested via release binary, v0.142.5)

- Standalone, no auth; Apache-2.0; static musl binary (~286 MB) with `.sigstore` attestations.
- Write-scoping (`workspace-write` + `writable_roots`) and network on/off verified working.
- **No read-hiding of any kind** (`~/.gnupg`, `~/.claude.json` readable under default profile); no deny-read config exists in the binary.
- No domain allowlisting.
- Nesting under an outer bwrap tmpfs-home mask works (needs writable `/tmp` for its mount-registry lock).
- Config schema mid-migration upstream (`[permissions]` tables erroring); `--full-auto` already deprecated once — churn-prone surface.

### Rejected outright

- **firejail**: Linux-only setuid-root binary, recurring local-root CVEs (CVE-2022-31214 et al.), no programmatic policy API.
- **Hand-rolled hardening** of `bwrap.py`: viable but keeps us in the enforcement business; declined on principle.
- **Container / dedicated WSL distro tier**: strongest fail-closed, zero sandbox code, but env duplication; keep as escalation path, not current direction.

## Policy layer (settled, applies regardless of runtime)

- Signing: off inside the sandbox; human signs at merge/push from host ("sign at the gate"); unsigned-inside remains the provenance marker.
- Push/PR: no path out (no gh token, no git-push egress); export = human acting from the host on the bind-mounted worktree.
- Hooks/plugins/skills: per-tool-family read-only allowlist entries as data in `sandbox.toml` profiles (overlay-extensible).
- Higher-privilege chezmoi: default profiles must not expose this repo rw; a distinct privileged profile (or simply working unsandboxed) covers work on the dotfiles themselves.

## Follow-ups (file as beads or execute in order)

1. **Debug the srt proxy-under-deny-home failure.**
   Reproduce: settings `denyRead:["~"]`, run `srt -d -c 'curl https://api.github.com/zen'`; bisect by adding `allowRead` entries (srt state dirs, `/tmp/claude-*.sock` paths) until the bridge works; identify the minimal allow set.
2. **Security audit of srt at a pinned version** (per repo practice for onboarding upstream code): npm supply chain, the vendored native `apply-seccomp` binary, proxy MITM/cert handling.
3. **Provisioning design**: pinned srt without global npm — e.g. `npm pack`ed tarball as chezmoi external, node via existing mise toolchain; must satisfy "policy inputs not writable from inside sandbox".
4. **Acceptance test**: run a real `claude` loop inside srt with `allowedDomains` limited to its API + statsig/sentry endpoints; extend `doctor.py` probes (absence through layers, write scoping, allowed vs denied domains, proxy health).
5. **Map `SandboxSpec`/`sandbox.toml` → srt settings generator**; keep the pure-function compilation + unit test pattern from `test_bwrap.py`.
6. **Housekeeping**: delete `seatbelt.py` stub; mark `DESIGN-sandboxr-two-layer.md` as fallback; decide `bwrap.py`'s fate (likely deleted once srt acceptance passes).

## Continuation prompt for the next session

See PR/branch `feat/sandboxr-two-layer-design` for both documents and the design-decision trail.
