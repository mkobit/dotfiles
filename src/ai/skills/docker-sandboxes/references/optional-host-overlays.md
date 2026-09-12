# Optional host overlays

Repository environments must run without chezmoi.

When a host has a reviewed managed personal layer, keep `~/.local/share/sbx/personal/personal.sbxenv.yaml` outside the repository and pass it after the project environment file so SBX merges it as a later override.

The personal layer carries shared guidelines and skills that follow the user across repositories.
Each project owns its dependency versions, tool versions, build checks, and project-specific setup.
Do not create a personal copy inside each project.

In the personal dotfiles, `sbx.personal.enabled` controls kit generation during `chezmoi apply`.
The kit uses `ai.guidelines.sections` and portable skills selected as `present` in `ai.skills`, including their supporting files.
Update those canonical sources and apply chezmoi before creating a sandbox to receive the new learning.
Explicitly setting `enabled = false` removes the generated personal layer; an omitted setting leaves it unmanaged.

Disable native writable shared skills in the personal overlay with `sandboxOptions.shareSkills: false` when the overlay supplies its own skill snapshots.
This is a personal-overlay choice, not a universal project prohibition.
Private skill snapshots are copied when the sandbox is created and require environment recreation to update.
Do not describe them as live refreshed files.

Do not copy host credentials, SSH material, GPG material, or agent settings into a repository environment.

Do not claim global skill discovery works for Codex or AGY until it has been proven by a live sandbox check for that agent.

Host overlays are optional extensions for shared skills, local models, GPU capability, or policy defaults.

GPU passthrough is experimental Linux NVIDIA VFIO host support and is never enabled by a project environment by default.
