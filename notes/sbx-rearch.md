# RFC & Implementation Spec: Autonomous Handoff Swarm & Skill Refactor (`mkobit/dotfiles`)

Implementation uses the [accepted plan](sbx-rearch-plan.md), [shared progress](sbx-rearch-progress.md), and [task 7 corrections](sbx-rearch-tasks/task7-refinement.md).
Those records supersede the shell examples and guest tracker steps below where installed CLI behavior or later decisions differ.
Use host claim and close, exact-head independent review before merge, and the shared long-lived feature branch for this migration.

> **Execution Prompt for Implementing Agent**
>
> You are tasked with implementing a major architectural shift in this Chezmoi repository (`mkobit/dotfiles`).
>
> **Mandatory Operating Rules:**
> 1. **Inspect & Respect Base/Overlay Architecture First**: Before editing any files, inspect `.chezmoi.toml.tmpl` / `.chezmoidata.*`, `.chezmoitemplates/`, and existing `src/ai/` files to understand how the **base/overlay mechanism** works in this repository. Every feature, skill, harness permission rule, `sbx` setting, model route, and `mise` task you add **MUST** follow the existing base/overlay pattern so an overlay (e.g., a restricted work machine vs. personal home machine) can cleanly mutate, enable, disable, or inject/subtract behavior.
> 2. **Create a Persistent Checklist / Bead Graph First**: Before writing implementation code, translate **Section 9 (Atomic Implementation Checklist)** into a tracked checklist (or `bd` issues if `bd` is initialized in this repo) and verify your plan against existing repository conventions.
> 3. **Commit Every Minor Addition Atomically**: Do **not** batch this migration into one giant commit. Commit each logical step independently (`git commit -S`), verifying that `chezmoi status` / `chezmoi execute-template` / `mise run` succeeds after every single commit so we maintain a bisect-friendly, working Git history.
> 4. **Use `mise` Exclusively for Tasks & Tooling**: Never introduce `Justfile` or `make`. Use `mise` (`mise.toml` and global `~/.config/mise/config.toml`) for all task orchestration, tool provisioning, and verification gates.

## 1. Executive Summary & Paradigm Shift

We are migrating our personal AI engineering workflow from **high-friction host-interactive sessions** (where agents run on the host or via ad-hoc `clone: false` sandbox calls, triggering constant approval prompts and cross-reaching into sibling repositories) to a **low-overhead Autonomous Handoff Swarm**.

### Core Pillars of the New Paradigm
- **Strict Separation of Roles**:
  - **Interactive Architect / Triage Loop (Host or Sandbox)**: The human collaborates with a high-reasoning agent (`claude`, `agy`, or `codex`) to define domain axioms, UX constraints, `SPEC.md`, and `AGENTS.md`, decomposing work into dependency-linked [Beads (`bd`)](https://beads.gascity.com/) issues.
  - **Unattended Worker Loop (Inside `sbx` MicroVMs)**: Worker agents run **entirely inside** [Docker Sandboxes (`sbx`)](https://docs.docker.com/ai/sandboxes/) with auto-approval flags (`--dangerously-skip-permissions` / `--full-auto`). Because only the target repository is mounted into the microVM, the agent physically cannot wander into sibling repositories (`../other-repo`) on the host.
- **Chezmoi Base/Overlay Composability**: All harnesses (`agy`, `claude`, `codex`, `opencode`, `pi`), skills, permission allowlists, `sbx` configurations, and `mise` tasks are parameterized through Chezmoi data so work overlays can disable personal `sbx` settings, swap model providers, or tighten `gh`/`git` allowlists without forking base templates.
- **Direct In-Sandbox Git, Commit Signing & `gh` PR Handoff**: Agents commit directly inside the sandbox (via forwarded SSH signing or a dedicated GPG signing subkey), push their branch, open a PR via `gh` (authenticated via host-side `sbx secret` proxy injection), watch CI checks (`gh pr checks --watch --fail-fast`), and merge on green.
- **Universal Repo Adoption (`mise` Bootstrap)**: Any personal repository (such as `storagemaxxing` or `canopy`) can adopt this workflow with a single `mise run repo:bootstrap` command that scaffolds `AGENTS.md`, `mise.toml` (`verify`, `check`, `test`), and `bd` initialization.

## 2. Architectural Decisions & Tradeoffs Record (ADR)

 implementing agents and future maintainers should preserve the rationale behind these choices:

| Decision Area | Chosen Approach (Short Term) | Alternative / Fallback Considered | Rationale & Tradeoffs |
| :--- | :--- | :--- | :--- |
| **1. Sandbox Runtime** | **[Docker Sandboxes (`sbx`)](https://docs.docker.com/ai/sandboxes/)** as primary microVM runner; keep task interface modular in `mise`. | [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell) (`openshell-driver-vm`), [`nono`](https://github.com/nolabs-ai/nono) (Landlock/Seatbelt), [Anthropic `srt`](https://github.com/anthropics/sandbox-runtime) ([Sandbox Comparison](https://rywalker.com/research/local-agent-sandboxes)). | We already have working knowledge and skills (`sbx-orchestrator`) around `sbx`. It provides a true microVM boundary, private Docker daemon, `SSH_AUTH_SOCK` forwarding, `sbx secret` proxy injection, and `llmman` model routing. Wrapping invocations in `mise` tasks lets us swap in OpenShell or `nono` via overlay later. |
| **2. Workspace Mount Mode (`clone: false` vs `--clone`)** | **Support both via flag**, defaulting to **in-sandbox execution**:<br>• Direct mount (`clone: false`) for single-worker / Architect sessions where immediate host file visibility is desired.<br>• Clone mode (`--clone`) when dispatching parallel swarm workers on the same repo ([Docker Git Workflows](https://docs.docker.com/ai/sandboxes/workflows/git/)). | Host-side agent shelling out to `sbx` for individual commands. | Running the agent on the host while shelling out to `sbx` caused constant host approval prompts because file reads (`Read`/`Glob`) and `bd`/`gh` calls still ran unsandboxed on the host. Running the harness *inside* `sbx` confines filesystem visibility strictly to the mounted repo while still returning file diffs (in direct mode) or pushed branches/PRs (in both modes). |
| **3. Commit Signing Inside Sandboxes** | **Dual-Support (Configurable via Chezmoi Overlay)**:<br>• **Option A (Default/Zero-Setup)**: **SSH Agent Forwarding** (`gpg.format = ssh`) using `sbx`'s automatic `SSH_AUTH_SOCK` passthrough ([Docker Commit Signing](https://docs.docker.com/ai/sandboxes/workflows/git/)).<br>• **Option B (GPG Subkey)**: Dedicated 1-year signing-only GPG subkey (`[S]`) exported or forwarded via `S.gpg-agent.extra`. | Using the host's primary GPG master key interactively for every commit. | `sbx` forwards `SSH_AUTH_SOCK` out of the box, allowing agents to run `git commit -S` directly inside the sandbox without private keys ever entering the VM or triggering host `pinentry` popups. For repos/overlays requiring strict PGP signatures, a dedicated signing subkey isolates risk so it can be revoked independently. |
| **4. `gh` CLI & Credential Scoping** | **In-Sandbox `gh` via Host Sentinel Proxy** (`sbx secret set github --command 'gh auth token'`) + **Scoped Allowlist on Host** ([Docker CLI Auth](https://docs.docker.com/ai/sandboxes/workflows/authentication/)). | Running `gh` only on the host after sandbox exit, or passing `GH_TOKEN` env vars in plaintext. | Nearly every worker sandbox needs `gh` to open PRs, watch checks, merge on green, or file follow-up GitHub issues. `sbx secret set github` lets `gh` run inside the sandbox while keeping the actual token on the host. |
| **5. Beads (`bd`) Concurrency & Sync** | **Beads Proxied-Server Mode (`bd init --proxied-server`)** (or Dolt `refs/dolt/data` push/pull when in `--clone` mode) ([DoltHub Proxied-Server Blog](https://www.dolthub.com/blog/2026-07-22-introducing-beads-proxied-server-mode/)). | Legacy `bd` embedded single-writer lock without coordination. | Embedded mode locks `.beads/embeddeddolt/` to a single process, which breaks when the host and a sandbox (or multiple agents) query/create beads concurrently. Proxied-server mode manages a lightweight on-demand local Dolt server automatically. |
| **6. Upstream Forge & CI Portability** | **GitHub (`gh`) Short-Term**, abstracted behind `mise run pr:*` tasks so **[Forgejo (`fj`)](https://forgejo.org/)** and **[Tangled (`knot` + `spindle`)](https://tangled.org/docs/spindles/)** can be enabled per-repo or per-overlay. | Hardcoding `gh` commands inside agent prompts and skills. | Calling `mise run verify` for testing and `mise run pr:ship` for PR handoff means agents never hardcode forge-specific logic, making future migration to self-hosted Forgejo or Tangled seamless. |
| **7. Local / LAN Model Routing** | **Subscription Auth for Tier 1/2 (`claude`, `codex`, `agy`)** + **Host/LAN [Ollama](https://docs.ollama.com/integrations) via `sbx --provider ollama`** for Tier 3/4 background tasks ([Docker Models Docs](https://docs.docker.com/ai/sandboxes/configuration/models/)). | Paying per-token API rates for all background tasks. | Preserves flat-rate subscriptions for high-reasoning architecture/coding while routing repetitive unit test, lint, and triage loops to local/LAN GPUs at zero marginal cost. |

## 3. Chezmoi Base / Overlay Architecture Requirements

All changes in `mkobit/dotfiles` **must** adhere to the existing base/overlay pattern so that an overlay repository or machine profile can override, disable, or extend any piece of the AI suite.

### 3.1 Structured Data Schema (`.chezmoidata` / `.chezmoi.toml.tmpl`)
Extend the existing AI configuration map in Chezmoi data with composable keys that overlays can merge or override:

```toml
# Conceptual structure — adapt to existing key naming in mkobit/dotfiles
[data.ai]
  enabled = true

  [data.ai.sandbox]
    provider = "sbx"                    # "sbx" | "none" (overlay can disable sbx in restricted work envs)
    default_clone_mode = false          # false = direct mount, true = --clone microVM copy
    skills_mode = "readonly"            # "readonly" | "readwrite" | "off"
    network_policy = "balanced"         # "balanced" | "custom"
    proxy_gh_secret = true              # Whether to wire `sbx secret set github --command 'gh auth token'`

  [data.ai.signing]
    mode = "ssh-forwarded"              # "ssh-forwarded" | "gpg-subkey" | "host-default"
    gpg_subkey_id = ""                  # Populated if mode == "gpg-subkey"

  [data.ai.ollama]
    enabled = true
    host_url = "http://localhost:11434"
    sandbox_url = "http://host.docker.internal:11434"
    default_coder_model = "qwen3-coder:30b"

  [data.ai.permissions]
    # Base safe allowlists merged with `.data.ai.overlay.permissions`
    allow_sbx = true
    allow_bd = true
    allow_mise = true
    deny_parent_traversal = true        # Blocks Read(../**) and Edit(../**) on host
    # Safe subset of git and gh commands auto-approved on host (see Section 4)
    git_safe_subcommands = ["status", "diff", "log", "branch", "checkout", "Switch", "add", "commit", "fetch", "pull", "push", "worktree", "rev-parse"]
    gh_safe_subcommands = ["pr create", "pr view", "pr list", "pr checks", "pr status", "pr diff", "pr merge", "issue create", "issue list", "issue view", "run view", "run list", "repo view"]

  [data.ai.skills]
    # Overlays can append to `disabled` or `extra_dirs`
    enabled_list = ["sbx-orchestrator", "architect-scoping", "worker-handoff", "repo-bootstrap", "retro-self-improve"]
    disabled_list = []
```

### 3.2 Overlay Mutation Rules
1. **Skill Enable/Disable**: When rendering skills into `~/.claude/skills/`, `~/.agents/skills/`, and `~/.config/opencode/skills/`, iterate over `data.ai.skills.enabled_list` minus `data.ai.skills.disabled_list` (plus any overlay-injected skills). Use `.chezmoiignore.tmpl` to exclude disabled skills cleanly.
2. **Permission & Command Injection**: Use Chezmoi template helpers (`.chezmoitemplates/ai_permissions.tmpl`) that merge base `git_safe_subcommands` / `gh_safe_subcommands` with `dig "ai" "overlay" "permissions" ...` so a work overlay can strip `gh pr merge` or `sbx` while adding internal corporate CLI tools.
3. **Syncing Skills into `sbx`**: Add a `run_onchange_after_sync-sbx-skills.sh.tmpl` script gated by `{{ if eq .ai.sandbox.provider "sbx" }}`. Because `sbx skills import` skips symlinks *inside* skill directories ([Docker Share Agent Skills](https://docs.docker.com/ai/sandboxes/workflows/agent-skills/)), ensure materialized files (not nested symlinks) exist in the source skill folders before running `sbx skills import --force` and `sbx settings set skills.defaultMode {{ .ai.sandbox.skills_mode }}`.

## 4. Global Harness Permission Allowlists (`agy`, `claude`, `codex`)

When running interactive Architect sessions or orchestrator commands on the host, we want **zero annoying approval prompts** for safe day-to-day commands (`sbx`, `mise`, `bd`, safe `git`, safe `gh`) while **strictly blocking** cross-repository wandering (`../`) and destructive operations (`gh repo delete`, `git push --force` to `main`, `rm -rf ~`).

### 4.1 Google Antigravity (`agy`) — `~/.gemini/antigravity-cli/settings.json.tmpl`
Configure `permissions.allow` and `permissions.deny` using Antigravity's `action(target)` syntax ([Antigravity CLI Headless & Permissions Docs](https://antigravity.google/docs/cli/headless/)):

```json
{
  "permissions": {
    "allow": [
      "write_file(./)",
      "command(mise)",
      "command(bd)",
      {{- if .ai.permissions.allow_sbx }}
      "command(sbx)",
      {{- end }}
      "command(regex:^git (status|diff|log|branch|checkout|switch|add|commit|fetch|pull|worktree|rev-parse|show)(\\s|$))",
      "command(regex:^git push(\\s+-u)?\\s+origin\\s+(feat|fix|chore|docs|refactor|test)/)",
      "command(regex:^gh pr (create|view|list|checks|status|diff|ready|comment)(\\s|$))",
      "command(regex:^gh pr merge(\\s+.*)?\\s+--(squash|merge|rebase))",
      "command(regex:^gh issue (create|view|list|comment)(\\s|$))",
      "command(regex:^gh run (view|list|watch)(\\s|$))"
    ],
    "deny": [
      "read_file(../)",
      "write_file(../)",
      "command(regex:^gh (repo delete|auth token|secret|ssh-key|gpg-key))",
      "command(regex:^git push.*(--force|-f).*main)"
    ]
  }
}
```

### 4.2 Claude Code (`claude`) — `~/.claude/settings.json.tmpl`
Render the equivalent allow/deny boundaries for Claude Code:

```json
{
  "permissions": {
    "allow": [
      "Bash(mise *)",
      "Bash(bd *)",
      {{- if .ai.permissions.allow_sbx }}
      "Bash(sbx *)",
      {{- end }}
      "Bash(git status*)",
      "Bash(git diff*)",
      "Bash(git log*)",
      "Bash(git checkout*)",
      "Bash(git switch*)",
      "Bash(git branch*)",
      "Bash(git add*)",
      "Bash(git commit*)",
      "Bash(git fetch*)",
      "Bash(git pull*)",
      "Bash(git push -u origin *)",
      "Bash(git push origin feat/*)",
      "Bash(git push origin fix/*)",
      "Bash(git push origin chore/*)",
      "Bash(gh pr create*)",
      "Bash(gh pr view*)",
      "Bash(gh pr list*)",
      "Bash(gh pr checks*)",
      "Bash(gh pr status*)",
      "Bash(gh pr diff*)",
      "Bash(gh pr merge * --squash*)",
      "Bash(gh issue create*)",
      "Bash(gh issue view*)",
      "Bash(gh issue list*)",
      "Bash(gh run view*)",
      "Bash(gh run list*)"
    ],
    "deny": [
      "Read(../**)",
      "Edit(../**)",
      "Bash(gh repo delete*)",
      "Bash(gh auth*)",
      "Bash(git push * --force * main*)"
    ]
  }
}
```

### 4.3 OpenAI Codex (`codex`) — `~/.codex/config.toml.tmpl`
Configure Codex to use `workspace-write` sandbox confinement by default on host (which natively blocks writes outside `pwd` via Landlock/Seatbelt) and define an `unattended` profile for in-sandbox execution.

## 5. Commit Signing & Secret Proxying Architecture

### 5.1 How In-Sandbox Commit Signing Works (Two Paths)

You noted you previously signed commits on the host because you didn't realize sandboxes could sign commits directly, or wanted a cleaner way to mint a dedicated subkey. Both paths should be supported via `.ai.signing.mode`:

#### Path 1: Forwarded SSH Signing (`mode = "ssh-forwarded"`, Recommended Default)
- **Why it's great**: [Docker Sandboxes (`sbx`)](https://docs.docker.com/ai/sandboxes/workflows/git/) forwards your host's `SSH_AUTH_SOCK` into the microVM automatically. Your private key never leaves the host, and you don't have to deal with `gpg-agent` pinentry/tty issues across WSL/container boundaries.
- **One-Time Host Setup**:
  1. Generate a dedicated signing key (or use your existing SSH key loaded in `ssh-agent`):
     ```bash
     ssh-keygen -t ed25519 -C "mkobit-agent-signing" -f ~/.ssh/id_ed25519_signing
     ssh-add ~/.ssh/id_ed25519_signing
     ```
  2. Upload `~/.ssh/id_ed25519_signing.pub` to **GitHub Settings → SSH and GPG keys → New SSH key → Key type: Signing Key**.
- **In-Sandbox Git Configuration** (automated via Chezmoi / `sbx` init):
  ```bash
  git config --global gpg.format ssh
  git config --global commit.gpgsign true
  git config --global user.signingkey "key::$(ssh-add -L | head -n 1)"
  ```

#### Path 2: Minted GPG Signing-Only Subkey (`mode = "gpg-subkey"`)
- **Why it's great**: Keeps traditional PGP signatures while isolating your master `[C]` key. If an agent environment is ever compromised, you revoke only the `[S]` subkey without invalidating your primary PGP identity.
- **One-Time Host Setup**:
  ```bash
  # 1. Mint a 1-year ed25519 signing-only subkey under your primary GPG key
  gpg --quick-add-key <PRIMARY_KEY_FPR> ed25519 sign 1y
  # 2. Export public key and update GitHub GPG keys
  gpg --armor --export <PRIMARY_KEY_FPR> | gh gpg-key add -
  # 3. Export ONLY the secret subkey (note trailing '!') for unattended agent use
  gpg --export-secret-subkeys <NEW_SUBKEY_ID>! > ~/.gnupg/agent-subkey.sec
  ```

### 5.2 Host-Proxied `gh` Authentication in `sbx`
In `run_onchange_after_configure-sbx.sh.tmpl` (when `.ai.sandbox.proxy_gh_secret` is `true`), configure `sbx` to dynamically resolve your `gh` token on the host:
```bash
sbx secret set github --command 'gh auth token'
```
The `sbx` host proxy intercepts outbound requests to `api.github.com` / `github.com` from inside the microVM and injects the auth header on the host side ([Docker Authenticate CLI Tools](https://docs.docker.com/ai/sandboxes/workflows/authentication/)). The sandbox never sees the raw token, yet `gh pr create`, `gh pr checks --watch`, `gh pr merge`, and `gh issue create` work transparently inside the sandbox.

## 6. Dual-Loop Workflow: Interactive Architect vs. Unattended Worker

### 6.1 Loop 1: The Interactive Architect Session (`mise run agent:architect`)
You can run the Architect session either **on the host** (thanks to the scoped allowlists in Section 4) or **inside an `sbx` sandbox** (`mise run agent:architect --sandbox`).

**What the Architect Agent Does:**
1. Reads `AGENTS.md`, `SPEC.md`, and current `bd list` state.
2. Collaborates with you interactively to:
   - Define or refine **Product Axioms & Invariants** (e.g., non-blocking UI rules in `canopy`, storage safety invariants in `storagemaxxing`).
   - Capture UX feedback, edge cases, and acceptance criteria.
   - Record architectural decisions in `docs/decisions/` (or `AGENTS.md`).
3. Translates the agreed scope into dependency-ordered **Beads (`bd`)** units of work:
   ```bash
   bd create "Define core trait and error types" -t feature -p 1 -d "Detailed acceptance criteria..."
   bd create "Implement CLI subcommand and wire unit tests" -t feature -p 1 --deps blocks:<id-1> -d "..."
   ```
4. **Never writes large feature implementations itself** unless explicitly asked—it keeps its context window clean for product steering, triage, and backlog coordination.

### 6.2 Loop 2: The Unattended Worker Handoff Loop (`mise run agent:work` & `agent:swarm`)
Once beads exist in `bd ready`, you dispatch workers without babysitting:

**What Each Unattended Worker Does Inside `sbx`:**
1. Starts inside an isolated `sbx` microVM (`clone: false` for single-worker direct file sync, or `--clone` for parallel multi-agent workers).
2. Claims the target bead (`bd update <id> --claim`) and checks out branch `feat/<id>` (or `fix/<id>`).
3. Implements the unit of work strictly within the current repository.
   - **Scope Guardrail**: If the worker discovers a tangential bug, needed refactor, or open question outside the bead's scope, it **must not** edit unrelated files. Instead, it files a follow-up bead (`bd create "Follow-up: ..." -t chore -p 2`) or GitHub issue (`gh issue create ...`).
   - **Ambiguity Guardrail**: If blocked on a product/UX question that requires human input, it marks the bead blocked (`bd update <id> --status blocked`), posts the question on a draft PR or issue, and exits cleanly.
4. Runs `mise run verify` (format, lint, typecheck, unit/integration tests) in a loop until 100% green locally.
5. Creates a signed commit (`git commit -S`), pushes the branch, opens a PR via `mise run pr:ship`, watches CI checks (`gh pr checks --watch --fail-fast`), squash-merges on green (`gh pr merge --squash --delete-branch`), and closes the bead (`bd close <id>`).

## 7. Refactoring In-Chezmoi Skills (`src/ai/skills/`)

Our existing in-Chezmoi skills (including `sbx-orchestrator`) must be refactored so they stop instructing a host-running agent to manually wrap individual commands in `sbx`, and instead support the new dual-loop paradigm:

| Skill Name (`src/ai/skills/<name>/SKILL.md`) | Role & Trigger | Key Instructions to Bake In |
| :--- | :--- | :--- |
| **`sbx-orchestrator` (Refactored)** | Invoked when launching or managing sandboxes from the host (`agy`, `claude`, `codex`). | • Stop wrapping ad-hoc shell commands inside an interactive host session.<br>• Dispatch full units of work via `mise run agent:work --bead <id> --agent <claude\|codex\|agy\|opencode>` or `sbx run`/`sbx exec`.<br>• Explain when to use direct mount (`clone: false`, single active session per repo) vs. `--clone` (parallel background workers).<br>• Document `sbx secret set github` and `--provider ollama` model flags. |
| **`architect-scoping` (New)** | Used during interactive product/UX planning and backlog grooming (`mise run agent:architect`). | • Interview the user concisely on product axioms, UX expectations, and constraints.<br>• Update `AGENTS.md` / `SPEC.md` / `docs/decisions/` with durable axioms.<br>• Decompose work into atomic, independently verifiable `bd` issues (`bd create`) with explicit dependency links (`bd dep add`) and model-tier labels (`tier:fast`, `tier:standard`, `tier:deep`). |
| **`worker-handoff` (New)** | Loaded by unattended worker agents executing a bead inside `sbx`. | • Enforce the strict 6-step handoff protocol: Claim (`bd update --claim`) → Branch (`feat/<id>`) → Implement + File Follow-up Beads (`bd create`) → Verify (`mise run verify`) → Signed Commit (`git commit -S`) → Ship & Watch (`mise run pr:ship`).<br>• Never traverse outside the repository root (`../*`).<br>• On CI failure during `pr:ship`, inspect `gh run view --log-failed`, fix locally, re-run `mise run verify`, push, and re-watch (up to 2 self-repair attempts). |
| **`repo-bootstrap` (New)** | Used to onboard any new or existing repo (`storagemaxxing`, `canopy`, etc.) to this workflow. | • Inspect repo language/runtime and generate/update `mise.toml` with standardized `check`, `test`, and `verify` tasks.<br>• Initialize Beads in concurrent-safe mode (`bd init --proxied-server`) if `.beads/` is not present.<br>• Generate a tailored `AGENTS.md` with repo build/test commands, architecture overview, and handoff rules. |
| **`retro-self-improve` (New)** | Triggered after CI retries, PR review comments, or milestone completion. | • Distill non-obvious failure root causes into repo memory (`bd remember "..."` and `AGENTS.md` gotchas section).<br>• If a friction point applies across all repositories (e.g., a `mise` task improvement or permission tweak), draft a PR or bead targeting `mkobit/dotfiles`. |

## 8. Global & Per-Repo `mise` Task Specifications

### 8.1 Global `~/.config/mise/config.toml.tmpl` Tasks
Add the following global tasks to Chezmoi's `mise` configuration (parameterized by `.ai.*` overlay variables):

```toml
# Global AI Swarm & Handoff Tasks in ~/.config/mise/config.toml.tmpl

[tasks."agent:architect"]
description = "Start an interactive Architect/Scoping session (on host or inside sbx) to define axioms and file Beads"
usage = '''
flag "-a --agent <agent>" default="claude" help="Harness (claude, agy, codex)"
flag "-s --sandbox" help="Run the interactive architect session inside an sbx sandbox"
'''
run = '''
#!/usr/bin/env bash
set -euo pipefail
ARCH_PROMPT="Load the 'architect-scoping' skill. Read AGENTS.md and run 'bd list' to understand current project state. Help me scope features, refine product/UX axioms, and create dependency-linked beads in 'bd'."

if [[ "${usage_sandbox:-false}" == "true" ]]; then
  sbx run "${usage_agent}" . -- "${ARCH_PROMPT}"
else
  case "${usage_agent}" in
    claude) claude "${ARCH_PROMPT}" ;;
    agy)    agy "${ARCH_PROMPT}" ;;
    codex)  codex "${ARCH_PROMPT}" ;;
  esac
fi
'''

[tasks."agent:work"]
description = "Pick up an unblocked bead (or specified bead ID) and execute the unattended handoff workflow inside sbx"
usage = '''
flag "-b --bead <bead_id>" help="Specific bead ID (defaults to first item in 'bd ready')"
flag "-a --agent <agent>" default="claude" help="Harness (claude, codex, agy, opencode)"
flag "-m --model <model>" help="Optional Ollama / custom model via sbx --provider ollama"
flag "-c --clone" help="Run in an isolated --clone microVM (enables parallel sessions per repo)"
'''
run = '''
#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${usage_bead:-}" ]]; then
  BEAD_ID="${usage_bead}"
  BEAD_TITLE="$(bd show "$BEAD_ID" --json | jq -r '.[0].title // .title')"
else
  READY_FIRST="$(bd ready --json | jq '.[0] // empty')"
  if [[ -z "$READY_FIRST" ]]; then
    echo "No ready beads found via 'bd ready'."
    exit 0
  fi
  BEAD_ID="$(echo "$READY_FIRST" | jq -r '.id')"
  BEAD_TITLE="$(echo "$READY_FIRST" | jq -r '.title')"
fi

echo "==> Handing off Bead ${BEAD_ID}: ${BEAD_TITLE} to ${usage_agent}"
bd update "$BEAD_ID" --claim >/dev/null

WORKER_PROMPT="Follow the 'worker-handoff' skill for Bead ${BEAD_ID} ('${BEAD_TITLE}').
1. Run 'bd show ${BEAD_ID}' to read full requirements.
2. Create and switch to branch 'feat/${BEAD_ID}'.
3. Implement the changes. Do NOT touch files outside this repository. File any out-of-scope discoveries or questions via 'bd create' or 'gh issue create'.
4. Run 'mise run verify' and fix any issues until all checks and tests pass.
5. Commit changes with a signed commit ('git commit -S -m \"feat(${BEAD_ID}): ${BEAD_TITLE}\"').
6. Run 'mise run pr:ship ${BEAD_ID}' to push, open the PR, watch CI checks, merge on green, and close the bead."

SBX_FLAGS=()
[[ "${usage_clone:-false}" == "true" ]] && SBX_FLAGS+=(--clone)
[[ -n "${usage_model:-}" ]] && SBX_FLAGS+=(--provider ollama --model "${usage_model}")

case "${usage_agent}" in
  claude)
    sbx run "${SBX_FLAGS[@]}" claude . -- --dangerously-skip-permissions -p "${WORKER_PROMPT}"
    ;;
  codex)
    sbx run "${SBX_FLAGS[@]}" codex . -- exec --full-auto "${WORKER_PROMPT}"
    ;;
  opencode)
    sbx run "${SBX_FLAGS[@]}" opencode . -- run "${WORKER_PROMPT}"
    ;;
  agy)
    agy -p "${WORKER_PROMPT}" --dangerously-skip-permissions
    ;;
esac
'''

[tasks."pr:ship"]
description = "Push branch, open PR with gh, watch checks until green, squash-merge, and close bead"
usage = 'arg "<bead_id>" help="Bead ID to close upon green merge"'
run = '''
#!/usr/bin/env bash
set -euo pipefail
BEAD_ID="${usage_bead_id}"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

git push -u origin "$BRANCH"

PR_URL="$(gh pr view "$BRANCH" --json url -q .url 2>/dev/null || true)"
if [[ -z "$PR_URL" ]]; then
  PR_URL="$(gh pr create --fill --head "$BRANCH" --base main)"
fi

echo "==> Watching checks for ${PR_URL}..."
if gh pr checks "$PR_URL" --watch --fail-fast; then
  gh pr merge "$PR_URL" --squash --delete-branch
  bd close "$BEAD_ID" "Merged on green via ${PR_URL}"
  git checkout main && git pull --ff-only
else
  echo "CI checks failed for ${PR_URL}. Inspect failure logs below:" >&2
  gh run view --log-failed | tail -n 100 >&2 || true
  exit 1
fi
'''

[tasks."repo:bootstrap"]
description = "Bootstrap any personal repository (e.g. storagemaxxing, canopy) with AGENTS.md, mise verify tasks, and concurrent-safe Beads"
run = '''
#!/usr/bin/env bash
set -euo pipefail
if [[ ! -d .beads ]]; then
  bd init --proxied-server
fi
echo "Repository bootstrapped for autonomous handoff. Ensure 'mise.toml' defines [tasks.check], [tasks.test], and [tasks.verify]."
'''
```

## 9. Atomic Implementation Checklist (For the Implementing Agent)

> **Instructions for the Agent**: Copy this checklist into your working plan (or create `bd` tasks for each item). Execute and **commit each step individually** (`git commit -S -m "..."`) after verifying template rendering (`chezmoi execute-template` / `chezmoi diff`).

- [ ] **Step 1: Audit Existing Base/Overlay Structure**
  - Inspect `.chezmoi.toml.tmpl`, `.chezmoidata*`, `.chezmoitemplates/`, and `src/ai/` to map out how overlays currently mutate or override base settings.
  - *Verification*: Document exact variable paths before touching any templates.

- [ ] **Step 2: Add Base/Overlay AI Schema & Toggles**
  - Add `.ai.sandbox`, `.ai.signing`, `.ai.ollama`, `.ai.permissions`, and `.ai.skills` defaults to the base Chezmoi data file, ensuring overlay dictionaries merge cleanly without clobbering lists.
  - *Commit*: `feat(ai): add base/overlay schema for sandbox, signing, ollama, and permissions`

- [ ] **Step 3: Implement Scoped Global Allowlists for `agy`, `claude`, and `codex`**
  - Update the Chezmoi templates for `~/.gemini/antigravity-cli/settings.json`, `~/.claude/settings.json`, and `~/.codex/config.toml` to auto-allow `mise`, `bd`, `sbx`, safe `git` subcommands, and safe `gh` PR/issue/check subcommands while explicitly denying `../*` parent directory traversal.
  - *Commit*: `feat(ai): configure overlay-aware permission allowlists for agy, claude, and codex`

- [ ] **Step 4: Configure In-Sandbox Commit Signing & `sbx` Secret Proxying**
  - Add/update the Chezmoi `run_onchange_` setup script to configure `sbx policy init balanced`, `sbx settings set skills.defaultMode readonly`, `sbx secret set github --command 'gh auth token'`, and Git signing config (`ssh-forwarded` vs `gpg-subkey` based on `.ai.signing.mode`).
  - *Commit*: `feat(sbx): configure github secret proxy, balanced policy, and sandbox commit signing`

- [ ] **Step 5: Refactor `sbx-orchestrator` and Author New Core Skills**
  - Refactor `src/ai/skills/sbx-orchestrator/SKILL.md` to use in-sandbox execution (`mise run agent:work` / `sbx run`) rather than host-side command wrapping.
  - Create `architect-scoping/SKILL.md`, `worker-handoff/SKILL.md`, `repo-bootstrap/SKILL.md`, and `retro-self-improve/SKILL.md`, wired to respect `.ai.skills.enabled_list` and `.ai.skills.disabled_list`.
  - *Commit* (commit each skill addition/refactor separately):
    - `refactor(skills): update sbx-orchestrator for in-sandbox handoff execution`
    - `feat(skills): add architect-scoping and worker-handoff skills`
    - `feat(skills): add repo-bootstrap and retro-self-improve skills`

- [ ] **Step 6: Add Automated `sbx skills import` Sync Hook**
  - Create `run_onchange_after_sync-sbx-skills.sh.tmpl` that resolves any nested plugin symlinks into real files in the host skill directories and runs `sbx skills import --force` (when `.ai.sandbox.provider == "sbx"`).
  - *Commit*: `feat(sbx): sync chezmoi and plugin skills into sbx shared skill store`

- [ ] **Step 7: Wire Local/LAN Ollama Routing for `sbx`, `opencode`, and `pi`**
  - Enable `sbx settings set feature.model true` (when `.ai.ollama.enabled == true`) and template `~/.config/opencode/opencode.json.tmpl` and `~/.pi/config.json.tmpl` to point to `.ai.ollama.host_url` / `.ai.ollama.sandbox_url`.
  - *Commit*: `feat(ai): configure ollama model routing for sbx, opencode, and pi`

- [ ] **Step 8: Add Global `mise` Handoff Tasks (`agent:architect`, `agent:work`, `pr:ship`, `repo:bootstrap`)**
  - Add the global `mise` tasks to `~/.config/mise/config.toml.tmpl` so any repository can run `mise run agent:architect`, `mise run agent:work`, `mise run pr:ship`, and `mise run repo:bootstrap`.
  - *Commit*: `feat(mise): add global agent architect, worker handoff, and pr ship tasks`

- [ ] **Step 9: End-to-End Dry Run & Onboarding Guide**
  - Run `chezmoi diff` and `chezmoi apply --dry-run` to verify zero template errors across base and overlay states.
  - Test `mise run repo:bootstrap` and a single bead handoff (`mise run agent:work`) on a test repo or `storagemaxxing` / `canopy`.
  - *Commit*: `docs(ai): document autonomous handoff workflow and repo onboarding`
