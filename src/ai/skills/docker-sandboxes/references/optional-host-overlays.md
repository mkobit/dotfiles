# Optional host overlays

Repository environments must run without chezmoi.

When a host has a reviewed managed skills kit, keep its overlay outside the repository and pass it after the project environment file so SBX merges it as a later override.

Do not copy host credentials, SSH material, GPG material, or agent settings into a repository environment.

Do not claim global skill discovery works for Codex or AGY until it has been proven by a live sandbox check for that agent.

Host overlays are optional extensions for shared skills, local models, GPU capability, or policy defaults.

GPU passthrough is experimental Linux NVIDIA VFIO host support and is never enabled by a project environment by default.
