# Optional host overlays

Repository environments must run without chezmoi.

Keep the managed personal files outside repositories under `~/.local/share/sbx/personal/` and pass exactly one personal overlay after the project environment file.
Do not compose both personal overlays because their shared kit content would be duplicated.

`personal.codex.sbxenv.yaml` is the primary Codex-native plugin option.
It composes the shared `./kit` instructions/tools and the separate `./codex-kit` plugin kit.
It does not include the loose `./skills-kit` snapshot because the Codex kit activates the native plugin instead.
Use the Codex overlay only with a Codex project environment; do not assume AGY or other agents support the Codex plugin API.
`personal.sbxenv.yaml` is the portable compatibility fallback for shared guidelines and loose skills.
It composes the shared `./kit` and `./skills-kit` snapshots and sets `sandboxOptions.shareSkills: false`.

The generator is controlled by `sbx.personal.enabled` during `chezmoi apply`.
It keeps the portable overlay and adds the Codex overlay only when the boolean `plugins.codex` BOM setting is enabled.
The native setup must add the generated owned `dotfiles` marketplace and `mkobit-dotfiles` plugin through the Codex CLI, then verify installation and enabled state with the exact composed command:
`sbx env exec PROJECT PERSONAL -- codex plugin list --json`.
Do not claim all plugin types or agent invocation paths are verified from this Codex check.

Shared guest tools are selected explicitly through `sbx.personal.tools`, currently using the `ripgrep` and `fd` catalog entries (`rg` is the ripgrep binary).
Use the existing pinned Linux binary catalog URLs and checksums, guard for the local Linux architecture, and cache host downloads under `.local/share/sbx/tool-cache/linux_<arch>/<catalog-name>`.
Install them in the guest at `.local/share/sbx/bin/<binary>` and append that guest directory after the project PATH so project tools win.
Changing the overlay or kit requires `sbx env rm` and recreation; `sbx env run` does not reprovision kits.

Update canonical sources and apply chezmoi before creating a sandbox.
Explicitly setting `enabled = false` removes generated personal files; omitting it leaves them unmanaged.
Do not copy credentials, SSH/GPG material, or agent settings into repository environments.

Read Docker's [environment-file reference](https://docs.docker.com/ai/sandboxes/configuration/environment-files/) and [kit customization reference](https://docs.docker.com/ai/sandboxes/customize/kits/) for composition and kit behavior.
GPU passthrough remains experimental Linux NVIDIA VFIO host support and is never enabled by a project environment by default.
