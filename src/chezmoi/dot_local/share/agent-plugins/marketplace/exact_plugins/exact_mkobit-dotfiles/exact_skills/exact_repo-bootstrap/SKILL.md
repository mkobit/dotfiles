---
name: repo-bootstrap
description: Use when onboarding a repository to agent work with mise tasks, a repository-owned SBX kit, and Beads tracking.
---

# Repo bootstrap

Inspect the caller's repository and prepare setup through its explicit bootstrap interface.
Keep onboarding incomplete until the tracked kit works in a fresh environment.

1. Read the repository instructions, source files, build files, runtime declarations, existing tasks, and CI configuration.
   Identify the actual languages and required runtime versions.
   Preserve custom content in `AGENTS.md`, `mise.toml`, `.sbx`, and `.beads`.
   Keep changes in the assigned repository.
   Do not create a separate kit repository by default.

2. Record each real `check`, `test`, and `verify` command with its source evidence.
   Use only commands supplied explicitly or proven by the repository's build configuration.
   Language detection alone does not establish these commands.
   Collect all missing commands and prerequisites in one gap report.
   Request the missing evidence and leave onboarding incomplete.
   Do not add successful placeholder tasks.

3. Check the actual task listing and help for the explicit `repo:bootstrap` interface before invocation.
   Use the discovered syntax for all setup and changes.
   If the interface is absent, report it as a missing prerequisite and stop setup.
   Do not treat a planned helper or global task as an available command.
   Run its dry run first and inspect the proposed changes.
   Confirm that the dry run leaves files and runtime state unchanged.
   Apply only the required additions through that interface within the assigned scope.

4. Require a complete tracked kit owned by this repository.
   Include runtimes, executable tools, native packages, network rules, ports, services, and real checks needed by the project.
   Keep Chezmoi-managed changes in source, preview the diff, and verify convergence through ordinary apply.
   Do not substitute ad hoc installations or manual settings for a reproducible kit.

5. Preserve the existing tracker and its route.
   Only the designated host owner can initialize an absent tracker through the explicit bootstrap task after prerequisites pass.
   Verify the required installed dependencies and record Beads proxied-server mode as experimental.
   The task must use `bd init --proxied-server --non-interactive --skip-agents --skip-hooks` when initialization is needed.
   Do not force a migration or require guest Beads access for a host-owned route.

6. Reproduce setup from the tracked kit in a fresh disposable environment and run the established checks.
   Verify that a repeat setup preserves custom content and has no further changes.
   Report exact commands, exits, changes, verification evidence, and remaining gaps.
   Mark onboarding complete only after fresh reproduction and all required checks succeed.
