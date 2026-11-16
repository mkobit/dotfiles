# GitHub CLI extensions

Chezmoi manages `github/gh-stack` and `github/gh-actions-lock` on Linux and macOS for amd64 and arm64.
Release versions, platform assets, and SHA-256 checksums live in [the binary catalogs](../../../.chezmoidata/bin/).
The existing binary updater uses each catalog's `minimum_release_age = "21d"` when selecting version updates.

## Installation controls

The [init template](../../../.chezmoi.toml.tmpl) enables supported platforms through separate extension choices:

```toml
[data.gh.extensions.gh-stack]
installation_method = "github_releases"

[data.gh.extensions.gh-actions-lock]
installation_method = "github_releases"
```

Overlays can omit either choice or set its `installation_method` to `none`.
Missing and disabled choices perform no download, registration, update, or removal for that extension and preserve existing installations.
Keep these choices outside `data.local.bin` so the generic binary dispatcher does not emit duplicate downloads.

## Local registration and version updates

Chezmoi externals verify and deploy each executable to `<destination>/.local/share/gh-managed/gh-NAME/gh-NAME`.
Every apply makes enabled executables match their declared versions, including upgrades and downgrades.
After checking the executable, the registration script changes into its `gh-NAME` directory and runs the destination's `.local/bin/gh extension install .` without authentication or network access.
GitHub CLI registers that directory locally, so later chezmoi updates replace the executable used by `gh stack` or `gh actions-lock`.
Matching registration links stay unchanged, and every apply repairs missing or changed registrations.

Before replacing an enabled registration, the script removes only `<destination>/.local/share/gh/extensions/gh-NAME`.
A registration symlink is unlinked without deleting its target; a real registration directory is removed recursively at that exact path.
Local installation clears that extension's stale update state.

Supported extension storage is `<destination>/.local/share/gh`, with registration commands setting `XDG_DATA_HOME` to `<destination>/.local/share` and `XDG_STATE_HOME` to `<destination>/.local/state`.
Enabled management rejects a nonempty inherited `XDG_DATA_HOME` that differs from the supported data directory.
Disabled management bypasses this check.

To change a version, update its catalog version and all supported platform checksums, review `chezmoi diff`, then run `chezmoi apply`.
The 21-day setting controls updater release selection; applying an explicitly declared version reconciles immediately.
