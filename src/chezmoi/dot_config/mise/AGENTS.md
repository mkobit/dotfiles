# Mise tool version manager

## Installation

- **Mechanism**: Installed via `.chezmoiexternals/` directly from GitHub releases.
- **Location**: `{{ .chezmoi.destDir }}/.local/bin/mise`.

## Configuration

- **Global tools catalog** (versions, postinstall hooks): `src/chezmoi/.chezmoidata/bin/mise.toml` under `[mise.global_tools.<tool>]`.
- **Global tools BOM** (per-machine opt-in via `installation_method`): `src/chezmoi/.chezmoi.toml.tmpl` under `[data.local.mise.global_tools.<tool>]`.
  Catalog entries are inert until a BOM entry opts in (`installation_method = "mise"`).
  Mirrors the `.local.bin.*` convention.
- **Settings**: `src/chezmoi/.chezmoidata/bin/mise.toml` under `[mise.settings]`.
- **Shell**: Automatically hooked into `.zshrc` / `.bashrc`.

## Lockfile

`~/.config/mise/mise.lock` is regenerated locally by `mise lock` and is **not tracked in this repo** — `.chezmoiignore` blocks it (`**/.config/mise/mise.lock`) so per-machine drift doesn't pollute the chezmoi diff.
`run_onchange_after_06_trust-install-global-mise-tools.sh.tmpl` installs unlocked (`MISE_LOCKED=0`, fresh machine has nothing to validate against yet), then immediately runs `mise -C {{ .chezmoi.destDir }} lock --global` to populate it.
Required: mise merges the global config into any `mise install -C <dir>` call, so script `07`'s locked repo-tools install would otherwise re-validate the global tools too and fail.

### Never disable lock enforcement for the repo config

Root `mise.toml` sets `locked = true` (restored by #575 after a prior regression); script `07` installs with no override, by design — this is what keeps `uv` pinned to the committed `mise.lock`.
If a locked install ever fails, regenerate the stale lockfile (`mise lock`, or the global one above) — never add `MISE_LOCKED=0` to the script.
Watch for this in agent PRs (e.g. Jules) that hit a locked-install failure and "fix" it by disabling the check instead.

### Updating tools and relocking

Follow these steps exactly when updating any mise-managed tool version.
Do not substitute alternative commands — especially in Jules, where `mise lock` destroys the shell session permanently and irrevocably.

1. Update the version in `src/chezmoi/.chezmoidata/bin/mise.toml` under `[mise.global_tools.<tool>]` (catalog).
   New tools also require a BOM entry in `src/chezmoi/.chezmoi.toml.tmpl` under `[data.local.mise.global_tools.<tool>]` with `installation_method = "mise"`, followed by `chezmoi init` to propagate.
2. Apply the config to the home directory:
   ```
   chezmoi apply ~/.config/mise/config.toml
   ```
3. Regenerate the lockfile:
   ```
   MISE_LOCKED=0 mise -C ~ lock --global
   ```
   The `-C ~` flag is required — running from the dotfiles repo root causes global-only tools (e.g. `uv`) to be excluded because the repo-root `mise.toml` claims them.
