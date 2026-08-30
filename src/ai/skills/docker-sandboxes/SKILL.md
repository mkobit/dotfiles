---
name: docker-sandboxes
description: Use when setting up, running, or troubleshooting an sbx sandbox for a Git repository, especially unattended AGY work in an isolated clone.
---

# Docker Sandboxes

Use the managed `sbx-agy` launcher for repository work.
It creates an `sbx --clone` sandbox, so the agent never writes the host checkout.

## Project workflow

1. Read the repository’s `AGENTS.md`, agent configuration, and `mise` tasks.
2. Check for an optional tracked `.sbx/sbx-agy/` mixin kit.
3. State the project, the requested task, the default `work` authority, the selected checks, and the mixin before starting a sandbox.
4. Obtain confirmation before running `sbx-agy`, because it creates a host microVM and mounts a repository read-only for cloning.
5. Run AGY with an explicit non-interactive prompt when the user requested unattended work.
6. Obtain separate confirmation before `sbx-agy fetch --name NAME PROJECT`, which updates host Git remote refs but never merges them.

Example:

```bash
sbx-agy /path/to/project -- --print "run mise checks, fix the reported failure, and commit the change"
```

## Context composition

`sbx-agy` copies the host-managed AGY skill packages into the sandbox’s global discovery location.
It never mounts host agent settings, GitHub credentials, SSH material, or GPG material.
The managed AGY base kit uses Docker's mediated Google OAuth credential for AGY authentication, not a raw token in the sandbox.

The cloned repository keeps its own `.agents/skills` unchanged.
AGY gives project `.agents/skills` higher precedence than the injected global baseline.

The optional `.sbx/sbx-agy/` directory must validate as an `sbx` mixin kit without credentials.
Use it for project-local, versioned setup only.
Do not use it to add credentials, a writable host mount, or a second base sandbox.

## Authority boundaries

`work` is supported now.
It permits sandbox-local edits, project checks, and unsigned sandbox commits.

`publish` and `land` are design names, not implemented commands.
Do not infer GitHub API access, `git push`, pull-request creation, CI polling, or merging from a `work` request.
Each requires an explicit future capability and a real-host credential and egress proof.

## Troubleshooting

Use `sbx diagnose` and `sbx daemon status` before creating a sandbox.
Use `sbx kit validate` to validate an optional repository mixin without starting a sandbox.
Use `sbx ls` and `sbx policy check` only for read-only inspection.
Choose a new sandbox name for every `sbx-agy` run, because the launcher refuses to reattach to preserve clone-only isolation.

The first live launch must verify custom AGY-kit support and injected global-skill discovery for the installed `sbx` version.

`sbx skills import` does not provision AGY skills.
It supports a separate shared store for other built-in agents.

The current `sbx` CLI does not expose host SSH-agent or GPG-agent forwarding.
Keep sandbox commits unsigned and sign a reviewed host-side result if required.
