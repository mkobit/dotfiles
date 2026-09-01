---
name: docker-sandboxes
description: Use when setting up, running, or troubleshooting Docker Sandboxes (`sbx`) for a Git repository, including isolated Codex or AGY work.
---

# Docker Sandboxes

Use this skill when the user asks to set up, run, or repair an SBX environment for a repository.

1. Run `sbx version` and require `0.39.0` or later before using environment files.
2. Read the repository’s `AGENTS.md`, agent configuration, `.agents/skills`, CI workflows, build manifests, Docker files, and mise configuration.
3. State the selected agent, clone-mode workspace, required checks, requested authority, and any optional kit before changing files or creating a sandbox.
4. Obtain confirmation before any host-side sandbox lifecycle, credential, network-policy, publishing, Git push, PR, CI, or merge action.
5. For repository setup, read [repository setup](references/repository-setup.md) and [environment files](references/environment-files.md).
6. For agent selection, read [agents](references/agents.md), and read [upstream pins](references/upstream-pins.md) before creating an AGY environment.
7. Read [optional host overlays](references/optional-host-overlays.md) only when the user asks to compose host-managed skills or capabilities.

Do not use direct workspace mounts for autonomous work.
Do not place secrets, bindings, registries, local-command MCP servers, or writable additional workspaces in tracked project environments.
