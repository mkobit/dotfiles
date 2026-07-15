# Agent context for dotfiles repository

This is a **personal dotfiles repository** managed by mkobit.
It is a highly customized environment optimized for specific personal workflows.
AI agents must prioritize consistency with established architectural patterns, naming conventions, and local configuration styles.
Avoid imposing standard industry "best practices" if they conflict with the existing idiomatic choices made in this repository.

## Git context

This repository uses git worktrees.
You may be operating in a worktree on a feature branch, not the main checkout.
**Always run `git status` and `git worktree list` at the start of a session** to confirm which branch and worktree you are in before making any changes.
Never assume you are on `main` or in the primary checkout directory.

## Repository structure

- `src/chezmoi/` - Chezmoi templates and deployment configuration (the source of truth; `.chezmoiroot`).
- `src/chezmoi/.chezmoidata/` - Modular configuration data (TOML).
- `src/chezmoi/.chezmoidata/ai/skills.toml` - AI skill deployment catalog (pinned upstream skills installed via chezmoi externals).
- `src/ai/skills/` - Authored AI skills (canonical sources, deployed as copies).
- `src/python/` - Local Python tools (uv workspace).

## Critical path rules

1. **ALWAYS use `{{ .chezmoi.destDir }}` for ALL paths**
   - ✅ `export PATH="{{ .chezmoi.destDir }}/.local/bin:${PATH}"`
   - ❌ `export PATH="$HOME/.local/bin:${PATH}"`

2. **NEVER use `$HOME` or `{{ .chezmoi.homeDir }}`** in templates.
   - You must never use `$HOME`.
   - You must never use `{{ .chezmoi.homeDir }}` of your own accord.
   - You must always inject and template using `{{ .chezmoi.destDir }}`, `{{ .chezmoi.sourceDir }}`, `{{ .chezmoi.workingTree }}` (for the full source git directory), and other chezmoi variables.
   - The only exception is through explicit wording from user prompting.
   - If a user asks you to use them, you must provably come to the user with the reasons why before ever making an edit.
   - We install to a target directory, which may not be the user's home during testing/CI.

## Managed environment constraints

- **`modify_` scripts** are the ONLY safe way to customize externally managed files (like `.gitconfig`, `.zshrc` in corporate environments).
- **Never replace** system binaries or externally-installed tools.
- **Header pattern** for `modify_` scripts:
  ```bash
  # /path/to/script.tmpl:BEGIN:section:12345678 - WARNING: managed by chezmoi, do not edit
  # Applied: {{ now | date "2006-01-02T15:04:05Z07:00" }}
  [configuration]
  # /path/to/script.tmpl:END:section:12345678
  ```
- **Default new `modify_` scripts to a pure `chezmoi:modify-template`** (`{{- /* chezmoi:modify-template */ -}}` as the first line, e.g. `dot_codex/modify_config.toml`, `dot_claude/modify_settings.json`) rather than embedding another language (Python, shell) inside a rendered template string. Requires the source filename to have **no `.tmpl` suffix** and **no executable bit** — both confirmed empirically to break chezmoi's dispatch (it silently falls through to the legacy executable-script code path instead, and `.chezmoi.stdin` never gets populated). Parse the incoming file with `fromJson`/`fromToml`/`fromYaml` on `.chezmoi.stdin` (guard with `{{- if .chezmoi.stdin -}}` for a not-yet-existing target), transform with `mergeOverwrite`/`setValueAtPath`/`omit`, serialize back with `toPrettyJson`/`toToml`/`toYaml`. `toPrettyJson`'s return value always carries a trailing `\n` that `-}}` trim markers can't remove (trim only strips surrounding template *text*, not a pipeline's runtime value) — pipe through `trimSuffix "\n"` if the target shouldn't end in a blank line.
  **Known exception, don't relitigate:** `modify_dot_claude.json.tmpl` stays Python. Go's `fromJson`/`toPrettyJson` always alphabetize map keys (`encoding/json` marshal behavior, no workaround via these functions) — fine for a script that owns its whole output, but that script's entire point is touching one key in a ~2000-line file Claude Code itself constantly rewrites with its own key order and literal UTF-8; a Go-template rewrite would reformat the whole file every apply. Reconsider only if chezmoi ever exposes an order-preserving JSON codec.

## Chezmoi externals & scripts

All binary downloads go through chezmoi externals — never custom curl/wget scripts.
Use the `.chezmoiexternals/` **directory** form (flat `.chezmoiexternals.toml.tmpl` files are not recognized by chezmoi).
Versions, checksums, and download metadata live in `.chezmoidata/bin/`.
Shared shell libraries live in `.chezmoitemplates/` and are sourced via `{{ .chezmoi.sourceDir }}` at script render time.

## Binary tool catalog (BOM pattern)

Each binary tool has a catalog entry in `.chezmoidata/bin/` describing how to download it (URL pattern, platform map, checksums) for each supported source (GitHub releases, vendor hosting, package managers).
The **BOM** (Bill of Materials) in `.chezmoi.toml.tmpl` declares which tools are active on a given machine and by which method — catalog entries are inert until opted into via the BOM.
A dispatch template in `.chezmoiexternals/` reads the BOM and generates the appropriate chezmoi external entries.

When adding a tool: add a catalog entry, add a BOM entry, verify the correct source type is used (GitHub releases, direct vendor download, or package manager — don't conflate them).
When a tool extracts a full directory tree rather than a single binary, it needs its own `.chezmoiexternals/` entry rather than going through the shared dispatch template.

## Command approval policy

`.chezmoidata/ai/command_policy/*.toml` — one file per command family (e.g. `git.toml`, `beads.toml`), each declaring `[ai.command_policy.families.<name>]` with `prefixes` (literal command heads, no globs/regex).
Rendered into each tool's native permission-rule syntax by `dot_claude/modify_settings.json.tmpl` (`Bash(<prefix>:*)`) and `dot_gemini/antigravity-cli/modify_settings.json.tmpl` (`command(<prefix>)`).
New family = new file under `command_policy/`.
An overlay extends or shrinks an existing family via sibling `add`/`remove` prefix lists in the same `[ai.command_policy.families.<name>]` table — chezmoi list values replace wholesale on collision, so never restate `prefixes` directly — or disables one entirely via `enabled = false` (defaults to `true`, so base files never need to declare it).

## Data and templates

`.chezmoidata/` is the capability catalog — environment-neutral tool metadata, catalog entries, and structural additive data (config fragment registrations, plugin arrays, keybinds).
`.chezmoi.toml.tmpl` is the control plane — `installation_method` declarations, opt-in/opt-out decisions, and any logic requiring Go template conditionals.
Template values take precedence over `.chezmoidata/` for the same key path.
Scripts that read `installation_method` must use `dig "installation_method" "none" $tool` so a missing key is a no-op, not an accidental install or uninstall.
Access hyphenated keys with `index` rather than dot notation.

## Overlay compatibility

This repo is designed to be composed with an overlay — a separate chezmoi source tree that layers environment-specific configuration on top.
The overlay wins all file collisions, including `.chezmoi.toml.tmpl` — the overlay's init template completely replaces this one.

When adding features, keep them overlay-friendly:

- `installation_method` decisions belong in `.chezmoi.toml.tmpl`; overlays re-declare them in their own init template.
- Capability data (catalog entries, structural config) belongs in `.chezmoidata/` — overlays extend by adding keys, not editing base files.
- Use generic key names — describe the concept, not the environment.
- Use `dig` with a safe default for any key an overlay might omit so absence is a no-op.
- Loop over maps (`range $k, $v := .feature.items`) for injectable content.
- Keep all source files and data environment-neutral; machine-specific values belong in the overlay.

## Troubleshooting package installations

If an install fails due to a package being too new, check for a minimum release age setting in the relevant config (mise, uv, etc.) and use an older version that satisfies it.

## Zellij layout system

Each environment owns its layout files directly — no cross-repo injection.
Scalar config defaults live in `.chezmoidata/zellij.toml`; overlay environments override via `[data.zellij.*]`.
Docs: https://zellij.dev/documentation/creating-a-layout
